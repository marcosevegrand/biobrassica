from django.core.paginator import Paginator


def paginate_queryset(request, queryset, *, per_page):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get('page') or 1)

    query_params = request.GET.copy()
    query_params.pop('page', None)

    return {
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'pagination_query': query_params.urlencode(),
    }