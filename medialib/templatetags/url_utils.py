from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def replace_param(context, **kwargs):
    """
    Заменяет или добавляет параметры в текущий URL.
    """
    request = context.get("request")
    if not request:
        return ""

    query_params = request.GET.copy()

    for key, value in kwargs.items():
        if value is not None:
            query_params[key] = value
        else:
            query_params.pop(key, None)

    return query_params.urlencode()
