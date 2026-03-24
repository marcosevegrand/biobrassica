from __future__ import annotations

from django.db.models import Case, IntegerField, Prefetch, When
from django.utils.translation import get_language


DEFAULT_LANGUAGE = 'pt'
_TRANSLATION_CACHE_ATTR = '_translation_fallback_cache'


def normalized_language(lang=None, fallback=DEFAULT_LANGUAGE):
    language = (lang or get_language() or fallback or DEFAULT_LANGUAGE).split('-')[0]
    return language or DEFAULT_LANGUAGE


def language_choices(lang=None, fallback=DEFAULT_LANGUAGE):
    primary = normalized_language(lang, fallback=fallback)
    fallback_language = normalized_language(fallback, fallback=DEFAULT_LANGUAGE)
    languages = [primary]
    if fallback_language not in languages:
        languages.append(fallback_language)
    return languages


def translation_prefetch(translation_model, *, related_name='translations', lang=None, fallback=DEFAULT_LANGUAGE, to_attr=None):
    languages = language_choices(lang=lang, fallback=fallback)
    rank = Case(
        *[When(language=language, then=index) for index, language in enumerate(languages)],
        default=len(languages),
        output_field=IntegerField(),
    )
    queryset = translation_model.objects.filter(language__in=languages).order_by(rank, 'pk')
    return Prefetch(related_name, queryset=queryset, to_attr=to_attr)


def _translation_cache(instance):
    cache = getattr(instance, _TRANSLATION_CACHE_ATTR, None)
    if cache is None:
        cache = {}
        setattr(instance, _TRANSLATION_CACHE_ATTR, cache)
    return cache


def _translation_list(instance, *, related_name='translations', prefetched_attr=None):
    if prefetched_attr and hasattr(instance, prefetched_attr):
        return list(getattr(instance, prefetched_attr) or [])

    prefetched = getattr(instance, '_prefetched_objects_cache', {})
    if related_name in prefetched:
        return list(prefetched[related_name])

    related_manager = getattr(instance, related_name)
    if hasattr(related_manager, 'all'):
        return list(related_manager.all())

    return list(related_manager or [])


def select_translation(instance, *, lang=None, fallback=DEFAULT_LANGUAGE, related_name='translations', prefetched_attr=None):
    languages = tuple(language_choices(lang=lang, fallback=fallback))
    cache_key = (related_name, prefetched_attr, languages)
    cache = _translation_cache(instance)
    if cache_key in cache:
        return cache[cache_key]

    translations = _translation_list(instance, related_name=related_name, prefetched_attr=prefetched_attr)
    selected = None

    for language in languages:
        selected = next((translation for translation in translations if getattr(translation, 'language', None) == language), None)
        if selected is not None:
            break

    if selected is None and translations:
        selected = translations[0]

    cache[cache_key] = selected
    return selected


def get_translated_attr(
    instance,
    attribute,
    *,
    default='',
    lang=None,
    fallback=DEFAULT_LANGUAGE,
    related_name='translations',
    prefetched_attr=None,
    fallback_on_empty=False,
):
    translation = select_translation(
        instance,
        lang=lang,
        fallback=fallback,
        related_name=related_name,
        prefetched_attr=prefetched_attr,
    )
    if translation is None:
        return default

    value = getattr(translation, attribute, default)
    if not fallback_on_empty or value:
        return default if value is None else value

    fallback_language = normalized_language(fallback, fallback=DEFAULT_LANGUAGE)
    current_language = normalized_language(lang, fallback=fallback)
    if current_language == fallback_language:
        return default if value is None else value

    fallback_translation = select_translation(
        instance,
        lang=fallback_language,
        fallback=fallback_language,
        related_name=related_name,
        prefetched_attr=prefetched_attr,
    )
    if fallback_translation is None:
        return default

    fallback_value = getattr(fallback_translation, attribute, default)
    return fallback_value or default


class TranslationProxy:
    def __init__(self, instance, *, default='', lang=None, fallback=DEFAULT_LANGUAGE, related_name='translations', prefetched_attr=None):
        self.instance = instance
        self.default = default
        self.lang = lang
        self.fallback = fallback
        self.related_name = related_name
        self.prefetched_attr = prefetched_attr

    def __getattr__(self, attribute):
        return get_translated_attr(
            self.instance,
            attribute,
            default=self.default,
            lang=self.lang,
            fallback=self.fallback,
            related_name=self.related_name,
            prefetched_attr=self.prefetched_attr,
        )

    def __bool__(self):
        return select_translation(
            self.instance,
            lang=self.lang,
            fallback=self.fallback,
            related_name=self.related_name,
            prefetched_attr=self.prefetched_attr,
        ) is not None


def translation_proxy(instance, *, default='', lang=None, fallback=DEFAULT_LANGUAGE, related_name='translations', prefetched_attr=None):
    return TranslationProxy(
        instance,
        default=default,
        lang=lang,
        fallback=fallback,
        related_name=related_name,
        prefetched_attr=prefetched_attr,
    )