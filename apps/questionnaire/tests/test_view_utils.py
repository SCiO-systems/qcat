from unittest.mock import patch, Mock

from apps.qcat.tests import TestCase
from apps.questionnaire.view_utils import (
    ESPagination,
    get_limit_parameter,
    get_page_parameter,
    get_paginator,
)
from django.core.paginator import Paginator, Page


def get_valid_pagination_parameters():
    return {
        'pages': 1,
        'page': 1,
        'previous': '',
        'next': '',
        'has_previous': False,
        'has_next': False,
        'page_range': [1],
        'in_leading_range': True,
        'in_trailing_range': True,
        'pages_outside_leading_range': range(0, 0),
        'pages_outside_trailing_range': range(0, 0),
        'get_params': '',
        'count': 0,
    }


class ESPaginationTest(TestCase):

    def test_init_sets_data_total(self):
        p = ESPagination(['foo'], 1)
        self.assertEqual(p.data, ['foo'])
        self.assertEqual(p.total, 1)

    def test_len_returns_total(self):
        p = ESPagination(['foo'], 1)
        self.assertEqual(len(p), p.total)

    def test_slice_always_returns_all_items(self):
        p = ESPagination(['foo', 'bar', 'faz', 'taz'], 4)
        self.assertEqual(p[1:3], ['foo', 'bar', 'faz', 'taz'])


class GetPaginatorTest(TestCase):

    @patch('apps.questionnaire.view_utils.Paginator')
    def test_calls_Paginator(self, mock_Paginator):
        get_paginator([], 1, 10)
        mock_Paginator.assert_called_once_with([], 10)

    @patch('apps.questionnaire.view_utils.Paginator')
    def test_paginates(self, mock_Paginator):
        get_paginator([], 1, 10)
        mock_Paginator.return_value.page.assert_called_once_with(1)

    def test_paginates_with_1_if_page_not_integer(self):
        paginated, paginator = get_paginator([], 'foo', 10)
        self.assertEqual(paginated.number, 1)

    def test_paginates_with_max_if_page_too_big(self):
        paginated, paginator = get_paginator(['a', 'b', 'c', 'd'], 10, 1)
        self.assertEqual(paginated.number, 4)

    def test_returns_paginated_and_paginator(self):
        paginated, paginator = get_paginator([], 1, 10)
        self.assertIsInstance(paginated, Page)
        self.assertIsInstance(paginator, Paginator)


class GetLimitParameterTest(TestCase):

    def setUp(self):
        self.request = Mock()
        self.default_limit = 10

    def test_gets_limit_from_request(self):
        self.request.GET = {'limit': 5}
        limit = get_limit_parameter(self.request)
        self.assertEqual(limit, 5)

    def test_returns_default_if_no_limit_in_request(self):
        self.request.GET = {}
        limit = get_limit_parameter(self.request)
        self.assertEqual(limit, self.default_limit)

    def test_returns_default_if_limit_not_integer(self):
        self.request.GET = {'limit': 'foo'}
        limit = get_limit_parameter(self.request)
        self.assertEqual(limit, self.default_limit)

    def test_returns_default_if_limit_negative(self):
        self.request.GET = {'limit': -5}
        limit = get_limit_parameter(self.request)
        self.assertEqual(limit, self.default_limit)

    def test_returns_default_if_limit_0(self):
        self.request.GET = {'limit': 0}
        limit = get_limit_parameter(self.request)
        self.assertEqual(limit, self.default_limit)

    def test_returns_default_if_limit_bigger_than_maximum(self):
        self.request.GET = {'limit': 1000}
        limit = get_limit_parameter(self.request)
        self.assertEqual(limit, self.default_limit)


class GetPageParameterTest(TestCase):

    def setUp(self):
        self.request = Mock()
        self.default_page = 1

    def test_gets_page_from_request(self):
        self.request.GET = {'page': 5}
        page = get_page_parameter(self.request)
        self.assertEqual(page, 5)

    def test_returns_default_if_no_page_in_request(self):
        self.request.GET = {}
        page = get_page_parameter(self.request)
        self.assertEqual(page, self.default_page)

    def test_returns_default_if_page_not_integer(self):
        self.request.GET = {'page': 'foo'}
        page = get_page_parameter(self.request)
        self.assertEqual(page, self.default_page)

    def test_returns_default_if_page_negative(self):
        self.request.GET = {'page': -5}
        page = get_page_parameter(self.request)
        self.assertEqual(page, self.default_page)

    def test_returns_default_if_page_0(self):
        self.request.GET = {'page': 0}
        page = get_page_parameter(self.request)
        self.assertEqual(page, self.default_page)
