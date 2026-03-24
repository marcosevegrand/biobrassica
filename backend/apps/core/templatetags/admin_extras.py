from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def context_get(context, key, default=''):
    return context.flatten().get(key, default)


@register.filter
def safe_attr(value, name):
    if value is None:
        return ''

    result = None
    try:
        result = getattr(value, name)
    except AttributeError:
        try:
            result = value[name]
        except (KeyError, TypeError, IndexError):
            return ''

    if callable(result):
        try:
            return result()
        except TypeError:
            return result

    return result