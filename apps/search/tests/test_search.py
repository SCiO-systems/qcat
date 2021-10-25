from unittest.mock import patch

from apps.qcat.tests import TestCase
from apps.search.search import advanced_search


TEST_INDEX_PREFIX = 'qcat_test_prefix_'


class AdvancedSearchTest(TestCase):

    @patch('apps.search.search.es')
    @patch('apps.search.search.get_alias')
    def test_calls_get_alias_with_code(self, mock_get_alias, mock_es):
        advanced_search(filter_params=[], configuration_codes=['code'])
        mock_get_alias.assert_called_once_with('code_*')

    @patch('apps.search.search.es')
    @patch('apps.search.search.get_alias')
    def test_calls_get_alias_if_no_code(self, mock_get_alias, mock_es):
        advanced_search(filter_params=[], configuration_codes=[])
        mock_get_alias.assert_called_once_with()

    @patch('apps.search.search.get_alias')
    @patch('apps.search.search.es')
    def test_calls_search_no_query_string(self, mock_es, mock_get_alias):
        advanced_search(filter_params=[], query_string='')
        mock_es.search.assert_called_once_with(
            index=mock_get_alias.return_value,
            body={
                'query': {'bool': {'must': []}},
                'sort': [{'list_data.country.keyword': {'order': 'asc'}}, '_score']},
            size=10, from_=0)

    @patch('apps.search.search.get_alias')
    @patch('apps.search.search.es')
    def test_calls_search_with_query_string(self, mock_es, mock_get_alias):
        advanced_search(filter_params=[], query_string='foo')
        mock_es.search.assert_called_once_with(
            index=mock_get_alias.return_value,
            body={
                'query': {'bool': {'must': [{'multi_match': {'query': 'foo', 'fields': ['list_data.name.*^4', 'list_data.definition.*', 'list_data.country'], 'type': 'cross_fields', 'operator': 'and'}}]}},
                'sort': ['_score']},
            size=10, from_=0)

    @patch('apps.search.search.es')
    def test_returns_search(self, mock_es):
        ret = advanced_search(filter_params=[])
        self.assertEqual(ret, mock_es.search())
