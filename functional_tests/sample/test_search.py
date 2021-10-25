# Prevent logging of Elasticsearch queries
import logging
logging.disable(logging.CRITICAL)

import pytest

from django.urls import reverse
from unittest.mock import patch
from elasticmock import elasticmock

from apps.accounts.tests.test_models import create_new_user
from functional_tests.base import FunctionalTest
from apps.sample.tests.test_views import route_home as sample_route_home
from apps.samplemulti.tests.test_views import route_home as samplemulti_route_home
from apps.search.tests.test_index import create_temp_indices


LIST_EMPTY_RESULTS_TEXT = 'No results found.'


@elasticmock
class SearchTest(FunctionalTest):

    fixtures = [
        'sample_global_key_values',
        'sample',
        'samplemulti',
        'wocat',
        'sample_questionnaires_search',
    ]

    def setUp(self):
        super(SearchTest, self).setUp()
        create_temp_indices([
            ('sample', '2015'),
            ('samplemulti', '2015'),
        ])

    @patch('apps.questionnaire.views.get_configuration_index_filter')
    def test_search_home(self, mock_get_configuration_index_filter):

        mock_get_configuration_index_filter.return_value = [
            'sample', 'samplemulti']

        # Alice goes to the landing page and sees the search field
        self.browser.get(self.live_server_url + reverse('home'))

        # She enters a search value and submits the search form
        self.findBy('xpath', '//input[@type="search"]').send_keys('key')
        self.apply_filter()

        # She sees that she has been taken to the WOCAT configuration
        # where the search results are listed
        self.assertIn('/wocat/list', self.browser.current_url)
        results = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(results), 3)

        # She sees that this is the same result as when searching in
        # WOCAT (at the top of the page)
        self.findBy('xpath', '//input[@type="search"]').clear()
        self.findBy('xpath', '//input[@type="search"]').send_keys('key')
        self.apply_filter()

        self.assertIn('/wocat/list', self.browser.current_url)
        results = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(results), 3)

    def test_search_sample(self):

        # Alice goes to the home page of the sample configuration and
        # sees the search field at the top of the page.
        self.browser.get(self.live_server_url + reverse(sample_route_home))

        # She enters a search value and submits the search form
        self.findBy('xpath', '//input[@type="search"]').send_keys('key')
        self.set_input_value('search-type', 'sample')
        self.apply_filter()

        # She sees that she has been taken to the SAMPLE configuration
        # where the search results are listed
        self.assertIn('/sample/list', self.browser.current_url)
        results = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(results), 2)

        # Vice versa, the samplemulti configuration only shows results
        # from the samplemulti configuration
        self.browser.get(
            self.live_server_url + reverse(samplemulti_route_home))
        self.findBy('xpath', '//input[@type="search"]').send_keys('key')
        self.set_input_value('search-type', 'samplemulti')
        self.apply_filter()
        results = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(results), 1)


@elasticmock
class SearchTestAdmin(FunctionalTest):

    fixtures = [
        'sample_global_key_values',
        'sample',
        'sample_questionnaires',
    ]

    def setUp(self):
        super(SearchTestAdmin, self).setUp()
        create_temp_indices([
            ('sample', '2015')
        ])
        user = create_new_user()
        user.is_superuser = True
        user.save()
        self.user = user

    def test_search_admin(self):

        # Alice logs in
        self.doLogin(user=self.user)

        # She sees the button to access the search administration in the
        # top navigation bar and clicks it.
        self.clickUserMenu(self.user)
        navbar = self.findBy('class_name', 'top-bar')
        navbar.find_element_by_link_text('Search Index Administration').click()

        # First, delete the sample index.
        self.findBy('xpath', '//a[contains(@href, "/delete/sample/")]').click()

        # She sees that the active configurations are listed, all of
        # them having no index
        self.findBy(
            'xpath',
            '//tbody/tr[1]/td[text()="sample 2015"]')
        self.assertEqual(
            self.findBy(
                'xpath',
                '//tbody/tr[1]/td/span/strong[@class="text-warning"]').text,
            'No Index!')

        # She creates the index for the sample configuration
        self.findBy('xpath', '//a[contains(@href, "/index/sample/")]').click()

        # She sees the index was created successfully
        self.findBy('xpath', '//div[contains(@class, "success")]')
        self.assertEqual(
            self.findBy(
                'xpath',
                '//tbody/tr[1]/td/span/strong[@class="text-warning"]').text,
            '0 / 2')

        # She updates the newly created index
        self.findBy('xpath', '//a[contains(@href, "/update/sample/")]').click()

        # She sees that the index was updated successfully
        self.findBy('xpath', '//div[contains(@class, "success")]')
        self.findByNot(
            'xpath', '//tbody/tr[1]/td/span/strong[@class="text-warning"]')
        self.assertEqual(
            self.findBy(
                'xpath',
                '//tbody/tr[1]/td/span/strong[@class="text-ok"]').text,
            '2 / 2')

        # Do not delete all indices, as this will also delete the currently
        # active ones.
