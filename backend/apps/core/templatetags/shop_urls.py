from django import template
from django.urls import reverse
from django.utils import translation

from apps.core.site_content import get_shop_base_url
from apps.core.translations import normalized_language


register = template.Library()


@register.simple_tag(takes_context=True)
def shop_url(context, view_name='catalog:shop_home', language=None, **kwargs):
    request = context.get('request')
    lang = normalized_language(language or context.get('LANGUAGE_CODE') or getattr(request, 'LANGUAGE_CODE', None))

    with translation.override(lang):
        path = reverse(view_name, kwargs=kwargs, urlconf='config.urls_shop')

    return f'{get_shop_base_url(request=request)}{path}'