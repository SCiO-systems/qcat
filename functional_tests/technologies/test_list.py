import pytest
from django.test import override_settings
from elasticmock import elasticmock

from functional_tests.base import FunctionalTest
from functional_tests.pages.api import ApiV2ListPage
from functional_tests.pages.wocat import ListPage
from apps.search.tests.test_index import create_temp_indices


@elasticmock
class ListTest(FunctionalTest):

    fixtures = [
        'global_key_values',
        'approaches',
        'cca',
        'technologies',
        'unccd',
        'watershed',
        'wocat',
        'technologies_questionnaires',
        'unccd_questionnaires',
    ]

    def setUp(self):
        super().setUp()
        create_temp_indices([
            ('approaches', '2015'),
            ('cca', '2015'),
            ('technologies', '2015'),
            ('unccd', '2015'),
            ('watershed', '2015'),
            ('wocat', '2015'),
        ])

    def test_list_is_available(self):

        # User goes to the WOCAT list and sees both Technologies and UNCCD
        # practices are listed.
        page = ListPage(self)
        page.open()

        expected_results = [
            {
                'title': 'WOCAT Tech 2 en español',
                'description': 'Descripción 2 en español',
            },
            {
                'title': 'WOCAT Technology 1',
                'description': 'This is the definition of the first WOCAT Technology.',
            },
            {
                'title': 'UNCCD practice 2',
                'description': 'This is the description of the second UNCCD practice.',
            },
            {
                'title': 'UNCCD practice 1',
                'description': 'This is the description of the first UNCCD practice.',
            },
        ]
        page.check_list_results(expected_results)

        # User filters by type "technologies".
        page.filter_by_type('technologies')
        page.apply_filter()

        expected_results = [
            {
                'title': 'WOCAT Tech 2 en español',
                'description': 'Descripción 2 en español',
            },
            {
                'title': 'WOCAT Technology 1',
                'description': 'This is the definition of the first WOCAT Technology.',
            },
        ]
        page.check_list_results(expected_results)

    def test_filter(self):

        # User goes to the list view and filters by technologies, two entries
        # remain.
        page = ListPage(self)
        page.open()
        page.filter_by_type('technologies')
        page.apply_filter()
        assert page.count_list_results() == 2

        # User also filters by country (Switzerland), one entry remains.
        page.filter_by_country('Switzerland')
        page.apply_filter()
        assert page.count_list_results() == 1

        # Two filters are active.
        active_filters = page.get_active_filters()
        assert active_filters == [
            'SLM Data: SLM Technologies',
            'Country: Switzerland',
        ]

    def test_filter_also_in_api(self):

        # User goes to the list view and sees 4 results
        list_page = ListPage(self)
        list_page.open()
        assert list_page.count_list_results() == 4

        # User filters by type (technologies) and country (Switzerland), 1
        # result remains
        list_page.filter_by_type('technologies')
        list_page.filter_by_country('Switzerland')
        list_page.apply_filter()

        expected_results = [
            {
                'title': 'WOCAT Technology 1',
                'description': 'This is the definition of the first WOCAT Technology.',
            },
        ]
        list_page.check_list_results(expected_results)

        # User adds the same filter to the API URL
        query_dict = list_page.get_query_dict()
        api_page = ApiV2ListPage(self)
        api_page.open(query_dict=query_dict)

        # There is only one result (the same as in the list) in the result
        api_page.check_list_results(expected_results)

        # User does a search (by "wocat") in the list, there are 2 results
        list_page.open()
        list_page.search('wocat')
        list_page.apply_filter()

        expected_results = [
            {
                'title': 'WOCAT Technology 1',
                'description': 'This is the definition of the first WOCAT Technology.',
            },
            {
                'title': 'WOCAT Tech 2 en español',
                'description': 'Descripción 2 en español',
            },
        ]
        list_page.check_list_results(expected_results)

        # The same search (with the same results) is possible in the API
        query_dict = list_page.get_query_dict()
        api_page = ApiV2ListPage(self)
        api_page.open(query_dict=query_dict)
        api_page.check_list_results(expected_results)


@elasticmock
class ListTestEditions(FunctionalTest):

    fixtures = [
        'global_key_values',
        'approaches',
        'cca',
        'technologies',
        'technologies_2018',
        'unccd',
        'watershed',
        'wocat',
        'technologies_questionnaires',
        'technologies_2018_questionnaires',
        'unccd_questionnaires',
    ]

    def setUp(self):
        super().setUp()
        create_temp_indices([
            ('technologies', '2015'),
            ('technologies', '2018'),
        ])

    def test_filter_edition_in_api(self):
        expected_results_2018 = [
            {
                'title': 'WOCAT Technology 2018',
            },
        ]
        expected_results_2015 = [
            {
                'title': 'WOCAT Tech 2 en español',
            },
            {
                'title': 'WOCAT Technology 1',
            },
        ]

        api_page = ApiV2ListPage(self)

        # Filtering edition 2018
        query_dict = {'type': 'technologies', 'edition': '2018'}
        api_page.open(query_dict=query_dict)
        api_page.check_list_results(expected_results_2018)

        # Filtering edition 2015
        query_dict = {'type': 'technologies', 'edition': '2015'}
        api_page.open(query_dict=query_dict)
        api_page.check_list_results(expected_results_2015)

        # No edition filter (showing all)
        query_dict = {'type': 'technologies'}
        api_page.open(query_dict=query_dict)
        api_page.check_list_results(
            expected_results_2015 + expected_results_2018)

    @override_settings(FILTER_EDITIONS={'technologies': '2015'})
    def test_filter_specific_edition_2015(self):
        list_page = ListPage(self)
        list_page.open()

        self.open_advanced_filter('technologies')
        self.add_advanced_filter(
            'tech_qg_9__tech_landuse', 'tech_lu_grazingland')

        assert list_page.count_list_results() == 1
        expected_results = [
            {
                'title': 'WOCAT Technology 1',
            },
        ]
        list_page.check_list_results(expected_results)
