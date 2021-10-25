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
        'unccd',
        'technologies',
        'wocat',
        'approaches_questionnaires',
        'unccd_questionnaires',
    ]

    def setUp(self):
        super(ListTest, self).setUp()
        create_temp_indices([
            ('approaches', '2015'),
            ('technologies', '2015'),
            ('unccd', '2015'),
        ])

    def test_list_is_available(self):

        # User goes to the WOCAT list and sees that both Approaches and
        # UNCCD practices are listed.
        page = ListPage(self)
        page.open()

        expected_results = [
            {
                'title': 'WOCAT Approach 2 en español',
                'description': 'Descripción 2 en español'
            },
            {
                'title': 'WOCAT Approach 1',
                'description': 'This is the definition of the first WOCAT '
                               'Approach.'
            },
            {
                'title': 'UNCCD practice 2',
                'description': 'This is the description of the second UNCCD '
                               'practice.'
            },
            {
                'title': 'UNCCD practice 1',
                'description': 'This is the description of the first UNCCD '
                               'practice.'
            },
        ]
        page.check_list_results(expected_results)

        # User filters by type "approaches".
        page.filter_by_type('approaches')
        page.apply_filter()

        expected_results = [
            {
                'title': 'WOCAT Approach 2 en español',
                'description': 'Descripción 2 en español'
            },
            {
                'title': 'WOCAT Approach 1',
                'description': 'This is the definition of the first WOCAT '
                               'Approach.'
            },
        ]
        page.check_list_results(expected_results)
