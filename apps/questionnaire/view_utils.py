from collections import Sequence
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class ESPagination(Sequence):
    """
    A very simple helper object to allow Django to treat Elasticsearch
    results as paginated data. The Django Paginator expects a list or
    tuple which is basically the hit list returned by ES. The count of
    the total results is also returned by ES and is used to simulate a
    count of the objects. Slicing the object always returns the entire
    list of objects.

    .. seealso::
        https://docs.djangoproject.com/en/1.7/topics/pagination
    """
    def __init__(self, object_list, total):
        self.data = object_list
        self.total = total

    def __len__(self):
        return self.total

    def __getitem__(self, sliced):
        return self.data


def get_paginator(objects, page, limit, offset=None, total=None):
    """
    Create and return a Paginator filled with the objects and paginated
    at the given page.

    The paginator works in the following way. It takes the number of the objects and the current page and serves
    accordingly the pagination. EG 100 items and page 8 serves items 70-80
    However if we have objects queried with on offset meaning that if we are at page 8 with offset 70 it should
    show results 0-10. So we did add offset parameter and if offset is set, we do inject so many objects as the count
    in order to trick the paginator. That will result in us requesting page 8, the paginator to return objects 70-80,
    but the first 70 objects to be dummy objects and the actual results displayed to be 0-10.
    If total is set then we append as many objects as needed in order to get total object value value

    Args:
        ``objects`` (list): A list of objects to be paginated.

        ``page`` (int): The current page of the pagination. If it is not
        a valid integer, the first page is used. If the page provided is
        bigger than the nuber of pages available, the last page is
        returned.

        ``limit`` (int): The number of items per page.

    Returns:
        ``django.core.paginator.Page``. The paginated data.

        ``django.core.paginator.Paginator``. The Paginator object.
    """

    dummy_objects_prefix = [{} for item in range(offset)] if offset and offset > 5 else []
    dummy_objects_suffix = [
        {} for item in range(total - (len(dummy_objects_prefix) + len(objects)))
    ] if total else []
    objects = dummy_objects_prefix + objects + dummy_objects_suffix
    paginator = Paginator(objects, limit)
    try:
        paginated = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        paginated = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        paginated = paginator.page(paginator.num_pages)
    return paginated, paginator


def get_pagination_parameters(request, paginator, paginated):
    """
    Prepare and return the template parameters needed for pagination.

    Thanks to https://gist.github.com/sbaechler/5636351

    Args:
        ``request`` (django.http.HttpRequest): The request object.

        ``paginator`` (django.core.paginator.Paginator): An instance of
        the Paginator with the paginated data.

        ``paginated`` (django.core.paginator.Page): The paginated data.

    Returns:
        ``dict``. A dictionary with all values needed by the template to
        create the pagination.
    """
    LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 10
    LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 8
    NUM_PAGES_OUTSIDE_RANGE = 2
    ADJACENT_PAGES = 4

    pages = paginator.num_pages
    page = paginated.number
    in_leading_range = in_trailing_range = False
    pages_outside_leading_range = pages_outside_trailing_range = range(0)
    if pages <= LEADING_PAGE_RANGE_DISPLAYED + NUM_PAGES_OUTSIDE_RANGE + 1:
        in_leading_range = in_trailing_range = True
        page_range = [n for n in range(1, pages + 1)]
    elif page <= LEADING_PAGE_RANGE:
        in_leading_range = True
        page_range = [n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1)]
        pages_outside_leading_range = [
            n + pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
    elif page > pages - TRAILING_PAGE_RANGE:
        in_trailing_range = True
        page_range = [n for n in range(
            pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, pages + 1)
            if n > 0 and n <= pages]
        pages_outside_trailing_range = [
            n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
    else:
        page_range = [n for n in range(
            page - ADJACENT_PAGES, page + ADJACENT_PAGES + 1)
            if n > 0 and n <= pages]
        pages_outside_leading_range = [
            n + pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        pages_outside_trailing_range = [
            n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]

    # Now try to retain GET params, except for 'page'
    params = request.GET.copy()
    if 'page' in params:
        del(params['page'])
    get_params = params.urlencode()
    prev = paginated.previous_page_number() if paginated.has_previous() else ""

    return {
        'pages': pages,
        'page': page,
        'previous': prev,
        'next': paginated.next_page_number() if paginated.has_next() else "",
        'has_previous': paginated.has_previous(),
        'has_next': paginated.has_next(),
        'page_range': page_range,
        'in_leading_range': in_leading_range,
        'in_trailing_range': in_trailing_range,
        'pages_outside_leading_range': pages_outside_leading_range,
        'pages_outside_trailing_range': pages_outside_trailing_range,
        'get_params': get_params,
        'count': paginator.count,
    }


def get_limit_parameter(request):
    """
    Return the ``limit`` parameter of the request's GET parameters. This
    number is used to limit queries to the database or Elasticsearch. It
    needs to be a positive integer below the maximum valid limit. If the
    limit is not indicated or invalid, the default limit is returned.

    Args:
        ``request`` (django.http.HttpRequest): The request object with
        parameter ``limit`` set.

    Returns:
        ``int``. The limit.
    """
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 500
    try:
        limit = int(request.GET.get('limit', DEFAULT_LIMIT))
    except ValueError:
        limit = DEFAULT_LIMIT
    if limit <= 0 or limit > MAX_LIMIT:
        return DEFAULT_LIMIT
    return limit


def get_page_parameter(request):
    """
    Return the ``page`` parameter of the request's GET parameters. This
    number is used in combination with the ``limit`` parameter to
    perform pagination on queries to the database or Elasticsearch. It
    needs to be a positive integer. If the page is not indicated or
    invalid, the default page is returned.

    Args:
        ``request`` (django.http.HttpRequest): The request object with
        parameter ``page`` set.

    Returns:
        ``int``. The page.
    """
    DEFAULT_PAGE = 1
    try:
        page = int(request.GET.get('page', DEFAULT_PAGE))
    except ValueError:
        page = DEFAULT_PAGE
    if page <= 0:
        return DEFAULT_PAGE
    return page
