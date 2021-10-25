import pytest
from elasticmock import elasticmock

from functional_tests.base import FunctionalTest
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
            ('technologies', '2015'),
            ('unccd', '2015'),
            ('watershed', '2015'),
        ])

    def test_list_is_available(self):
        # User goes to the default WOCAT list and sees that all questionnaires
        # of WOCAT and UNCCD are listed
        page = ListPage(self)
        page.open()

        expected_results = [
            {
                'title': 'WOCAT Tech 2 en español',
                'description': 'Descripción 2 en español',
                'translations': ['es'],
            },
            {
                'title': 'WOCAT Technology 1',
                'description': 'This is the definition of the first WOCAT Technology.',
                'translations': ['fr'],
            },
            {
                'title': 'UNCCD practice 2',
                'description': 'This is the description of the second UNCCD practice.',
            },
            {
                'title': 'UNCCD practice 1',
                'description': 'This is the description of the first UNCCD practice.',
                'translations': ['es'],
            },
        ]
        page.check_list_results(expected_results)

    def test_list_handles_invalid_type(self):
        # The list can be loaded with invalid types.

        # User goes to the WOCAT list and sees "wocat" is selected as type
        # filter by default.
        page = ListPage(self)
        page.open()
        assert page.get_type_value() == 'wocat'
        assert page.count_list_results() == 4

        # User manually enters type "technologies" in the URL and loads the
        # page. The search type has changed.
        self.browser.get(page.get_url() + '?type=technologies')
        assert page.get_type_value() == 'technologies'
        assert page.count_list_results() == 2

        # User manually enters an invalid type in the URL. There is no error
        # message and the default type ("wocat") is loaded.
        self.browser.get(page.get_url() + '?type=foo')
        assert page.get_type_value() == 'foo'
        assert page.count_list_results() == 4

        # User manually enters type "UNCCD" (uppercase) in the URL.
        self.browser.get(page.get_url() + '?type=UNCCD')
        assert page.get_type_value() == 'UNCCD'
        assert page.count_list_results() == 2

    def test_list_is_multilingual(self):
        # User goes to the list
        page = ListPage(self)
        page.open()

        # English
        expected_results = [
            {
                'title': 'WOCAT Tech 2 en español',
                'description': 'Descripción 2 en español',
                'translations': ['es'],
            },
            {
                'title': 'WOCAT Technology 1',
                'description': 'This is the definition of the first WOCAT Technology.',
                'translations': ['fr'],
            },
            {
                'title': 'UNCCD practice 2',
                'description': 'This is the description of the second UNCCD practice.',
            },
            {
                'title': 'UNCCD practice 1',
                'description': 'This is the description of the first UNCCD practice.',
                'translations': ['es'],
            },
        ]
        page.check_list_results(expected_results)

        # User changes the language and sees the list again
        page.change_language('es')

        # Spanish
        expected_results = [
            {
                'title': 'WOCAT Tech 2 en español',
                'description': 'Descripción 2 en español',
            },
            {
                'title': 'WOCAT Technology 1 en français',
                'description': 'Ceci est la déscription 1 en français.',
                'translations': ['en', 'fr'],
            },
            {
                'title': 'UNCCD practice 2',
                'description': 'This is the description of the second UNCCD practice.',
            },
            {
                'title': 'UNCCD 1 en español',
                'description': 'Descripción 1 en español',
                'translations': ['en'],
            },
        ]
        page.check_list_results(expected_results)
