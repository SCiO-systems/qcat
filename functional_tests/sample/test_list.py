import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from unittest.mock import patch
from elasticmock import elasticmock

from functional_tests.base import FunctionalTest

from apps.accounts.models import User
from apps.questionnaire.models import Questionnaire
from apps.sample.tests.test_views import (
    route_home,
    route_questionnaire_list,
    route_questionnaire_filter,
    route_questionnaire_new_step)
from apps.search.tests.test_index import create_temp_indices

from functional_tests.pages.sample import SampleDetailPage, SampleEditPage, \
    SampleStepPage, SampleListPage


@elasticmock
class ListTest(FunctionalTest):

    fixtures = [
        'global_key_values',
        'flags',
        'sample',
        'unccd',
        'sample_questionnaires_5',
        'sample_projects',
        'sample_institutions',
    ]

    def setUp(self):
        super(ListTest, self).setUp()
        self.url_questionnaire_filter_sample = self.live_server_url + reverse(
            route_questionnaire_filter) + '?type=sample'
        create_temp_indices([('sample', '2015'), ('unccd', '2015')])

    def test_list_is_available(self):

        # She goes to the list page and sees all 4 questionnaires available.
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)

        # The entries are also ordered and each entry contains Keys 1 and 5 of
        # the questionnaires.
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
            'contains(text(), "Foo 3")]')
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//p['
            'text()="Faz 3"]')
        link = self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[2]//a['
            'contains(text(), "Foo 4")]')
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[2]//p['
            'text()="Faz 4"]')
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[3]//a['
            'contains(text(), "Foo 2")]')
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[3]//p['
            'text()="Faz 2"]')
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[4]//a['
            'contains(text(), "Foo 1")]')
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[4]//p['
            'text()="Faz 1"]')

        # Each entry has a placeholder because there is no image
        for e in list_entries:
            self.findBy(
                'xpath', '//img[contains(@src, "picture.svg")]', base=e)

        # She clicks a link and sees she is taken to the detail page of the
        # questionnaire
        link.click()
        self.toggle_all_sections()
        self.checkOnPage('Key 3')
        # The button to create a summary is on the page.
        self.findBy('xpath', '//a[@href="{summary_url}"]'.format(
            summary_url=reverse('questionnaire_summary', args=[4])
        ))

    def test_pagination(self):

        # Alice goes to the list view
        self.browser.get(self.url_questionnaire_filter_sample)

        # She sees 4 entries
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)

        # She does not see the pagination because there are not enough entries
        self.findByNot('xpath', '//div[contains(@class, "pagination")]')

        # She adds a limit to the URL and sees it is used to narrow the results
        self.browser.get(self.url_questionnaire_filter_sample + '&limit=1')
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
            'contains(text(), "Foo 3")]')

        # Now the pagination is visible
        self.findBy('xpath', '//div[contains(@class, "pagination")]')
        pagination = self.findManyBy(
            'xpath', '//ul[contains(@class, "pagination")]/li')
        self.assertEqual(len(pagination), 6)

        # She goes to the next page
        self.findBy('xpath', '//li[@class="arrow"]/a').click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located(
                (By.CLASS_NAME, "loading-indicator")))

        pagination = self.findManyBy(
            'xpath', '//ul[contains(@class, "pagination")]/li')
        self.assertEqual(len(pagination), 6)

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
            'contains(text(), "Foo 4")]')

        # She adds a filter
        self.add_advanced_filter('qg_11__key_14', 'value_14_3')

        # She sees that the list was filtered and that she is back on the
        # first page
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
            'contains(text(), "Foo 3")]')

        pagination = self.findManyBy(
            'xpath', '//ul[contains(@class, "pagination")]/li')
        self.assertEqual(len(pagination), 4)

        # She goes to the next page and sees the filter persists
        self.findBy('xpath', '//li[@class="arrow"]/a').click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located(
                (By.CLASS_NAME, "loading-indicator")))

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
            'contains(text(), "Foo 4")]')

        pagination = self.findManyBy(
            'xpath', '//ul[contains(@class, "pagination")]/li')
        self.assertEqual(len(pagination), 4)

        url = self.browser.current_url
        item_1 = self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])').text
        filter_1 = self.findBy('xpath', '//div[@id="active-filters"]/div').text
        pagination_1 = self.findBy(
            'xpath', '//ul[contains(@class, "pagination")]').text

        # She opens the current URL directly and sees that she is taken to the
        # exact same page
        self.browser.get(url)

        item_2 = self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])').text
        filter_2 = self.findBy('xpath', '//div[@id="active-filters"]/div').text
        pagination_2 = self.findBy(
            'xpath', '//ul[contains(@class, "pagination")]').text
        self.assertEqual(item_1, item_2)
        self.assertEqual(filter_1, filter_2)
        self.assertEqual(pagination_1, pagination_2)

        # She removes the specific filter and is back on the first page with
        # all results
        self.remove_filter(0)

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
            'contains(text(), "Foo 3")]')

        pagination = self.findManyBy(
            'xpath', '//ul[contains(@class, "pagination")]/li')
        self.assertEqual(len(pagination), 6)

        # She adds another filter
        self.add_advanced_filter('qg_11__key_14', 'value_14_1')

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
            'contains(text(), "Foo 4")]')

        pagination = self.findManyBy(
            'xpath', '//ul[contains(@class, "pagination")]/li')
        self.assertEqual(len(pagination), 4)

        # She goes to the second page
        self.findBy('xpath', '//li[@class="arrow"]/a').click()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located(
                (By.CLASS_NAME, "loading-indicator")))

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
            'contains(text(), "Foo 1")]')

    @patch('apps.questionnaire.views.get_configuration_index_filter')
    def test_list_with_foreign_configuration(self, mock_config_index_filter):
        mock_config_index_filter.return_value = ['*']

        # Alice goes to the list and sees that there are 5 questionnaires
        # available (one in UNCCD config)
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 5)

        expected_list_order = [
            {
                'name': 'Foo 3',
                'description': 'Faz 3',
            },
            {
                'name': 'UNCCD practice 1',
                'description': 'This is the description of the first UNCCD practice.',
            },
            {
                'name': 'Foo 4',
                'description': 'Faz 4',
            },
            {
                'name': 'Foo 2',
                'description': 'Faz 2',
            },
            {
                'name': 'Foo 1',
                'description': 'Faz 1',
            },
        ]
        self.check_list_results(expected_list_order)

    def test_list_database_es(self):

        # She goes to the WOCAT list and sees the list (retrieved from
        # elasticsearch) also contains metadata information and is
        # practically identical with the one on the landing page
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))

        entry_xpath = '//article[contains(@class, "tech-item")][2]'
        creation = self.findBy(
            'xpath', '{}//time'.format(entry_xpath))
        self.assertEqual(creation.text, '02/13/2014 5:08 p.m.')
        compiler = self.findBy(
            'xpath', '{}//li[contains(text(), "Compiler")]'.format(
                entry_xpath))
        self.assertIn('Foo Bar', compiler.text)

        # She also sees that the second entry has one compiler and one editor
        # but only the compiler is shown
        entry_xpath = '//article[contains(@class, "tech-item")][1]'
        compiler = self.findBy(
            'xpath', '{}//li[contains(text(), "Compiler")]'.format(
                entry_xpath))
        self.assertIn('Foo Bar', compiler.text)

        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
            'contains(text(), "Foo 3")]').click()

        info = self.findBy('xpath', '//ul[@class="tech-infos"]')
        self.assertIn('Foo Bar', info.text)
        self.assertIn('Faz Taz', info.text)

    def test_filter_checkbox(self):

        # Alice goes to the list view
        self.browser.get(self.url_questionnaire_filter_sample)

        # She sees there are 4 Questionnaires in the list
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)

        # The number of Questionnaires is also indicated in the title
        count = self.findBy(
            'xpath', '//h2/span[@id="questionnaire-count"]')
        self.assertEqual(count.text, '4')

        # There is only one active filter set
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 1)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')

        # She filters by some value
        self.add_advanced_filter('qg_11__key_14', 'value_14_2')

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
            'contains(text(), "Foo 2")]')

        # The number of Questionnaires in the title is updated
        count = self.findBy(
            'xpath', '//h2/span[@id="questionnaire-count"]')
        self.assertEqual(count.text, '1')

        # The filter was added to the list of active filters
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, 'Key 14: Value 14_2')

        # She unchecks the checkbox and updates the filter
        self.toggle_selected_advanced_filters(display=True)
        self.findBy('xpath',
                    '//input[@name="filter-value-select" and '
                    '@value="value_14_2" and @checked="checked"]',
                    wait=True).click()

        self.apply_filter()

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 1)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')

        # She selects the first checkbox and updates the filter
        self.add_advanced_filter('qg_11__key_14', 'value_14_1')

        expected_list = [
            {
                'title': 'Foo 4'
            },
            {
                'title': 'Foo 1'
            }
        ]
        self.check_list_results(expected_list)

        # The number of Questionnaires in the title is updated
        count = self.findBy(
            'xpath', '//h2/span[@id="questionnaire-count"]')
        self.assertEqual(count.text, '2')

        # The filter was added to the list of active filters
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, 'Key 14: Value 14_1')

        # She also selects value 3 and updates the filter
        self.toggle_selected_advanced_filters(display=True)
        self.findBy('xpath',
                    '//input[@name="filter-value-select" and '
                    '@value="value_14_3"]', wait=True).click()
        self.apply_filter()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located(
                (By.CLASS_NAME, "loading-indicator")))

        # The filters are joined by OR, therefore there are now more results
        expected_list = [
            {
                'title': 'Foo 3'
            },
            {
                'title': 'Foo 4'
            },
            {
                'title': 'Foo 1'
            }
        ]
        self.check_list_results(expected_list)

        # The active filter updated in the list of active filters
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, 'Key 14: Value 14_1 / Value 14_3')

        self.remove_filter(0)

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)

        # There is no active filter set
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 1)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')

        # She adds a first filter again
        self.add_advanced_filter('qg_11__key_14', 'value_14_3')

        # There is one active filter set
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, 'Key 14: Value 14_3')

        # She removes the first filter and adds another filter instead
        self.toggle_selected_advanced_filters(display=True)
        self.findBy('xpath',
                    '//input[@name="filter-value-select" and '
                    '@value="value_14_2"]', wait=True).click()
        self.findBy('xpath',
                    '//input[@name="filter-value-select" and '
                    '@value="value_14_3"]').click()
        self.apply_filter()

        # Again, there is one active filter set
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, 'Key 14: Value 14_2')

        # She reloads the same page and sees the correct checkbox was selected
        self.browser.get(self.browser.current_url)

        self.toggle_selected_advanced_filters(display=True)
        self.findBy('xpath',
                    '//input[@name="filter-value-select" and '
                    '@value="value_14_2" and @checked="checked"]', wait=True).click()

    # def test_filter_flags(self):
    #
    #     # Alice goes to the list view
    #     self.browser.get(self.live_server_url + reverse(
    #         route_questionnaire_list))
    #
    #     # She sees there are 4 Questionnaires in the list
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 4)
    #
    #     # There is no active filter set
    #     active_filter_panel = self.findBy(
    #         'xpath', '//div[@id="active-filters"]/div')
    #     self.assertFalse(active_filter_panel.is_displayed())
    #     active_filters = self.findManyBy(
    #         'xpath', '//div[@id="active-filters"]//li')
    #     self.assertEqual(len(active_filters), 0)
    #
    #     # She sees a link for advanced filtering which opens the filter
    #     # panel
    #     filter_panel = self.findBy('id', 'search-advanced-options')
    #     self.assertFalse(filter_panel.is_displayed())
    #     self.findBy('link_text', 'Advanced filter').click()
    #     self.assertTrue(filter_panel.is_displayed())
    #
    #     # She expands the flag section
    #     self.findBy('id', 'filter-flags-heading').click()
    #
    #     # She sees a checkbox to filter by flag
    #     WebDriverWait(self.browser, 10).until(
    #         EC.visibility_of_element_located(
    #             (By.ID, "flag_unccd_bp")))
    #
    #     url = self.browser.current_url
    #     # She submits the filter and sees the flag values were not submitted
    #     self.apply_filter()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #     self.assertEqual(self.browser.current_url, '{}?'.format(url))
    #
    #     # She clicks the UNCCD flag checkbox
    #     flag_cb = self.findBy('id', 'flag_unccd_bp')
    #     flag_cb.click()
    #
    #     # She submits the filter
    #     self.apply_filter()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #
    #     # She sees that the filter was submitted and the results are filtered.
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 1)
    #     self.findBy(
    #         'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
    #                  'contains(text(), "Foo 4")]')
    #
    #     # The filter is in the list of active filters
    #     active_filter_panel = self.findBy(
    #         'xpath', '//div[@id="active-filters"]/div')
    #     self.assertTrue(active_filter_panel.is_displayed())
    #     active_filters = self.findManyBy(
    #         'xpath', '//div[@id="active-filters"]//li')
    #     self.assertEqual(len(active_filters), 1)
    #     filter_1 = self.findBy('xpath', '//div[@id="active-filters"]//li[1]')
    #     self.assertEqual(filter_1.text, 'UNCCD Best Practice')
    #
    #     # The checkbox is checked
    #     self.assertTrue(flag_cb.is_selected())
    #
    #     # She clears the filter
    #     self.findBy('xpath', '(//a[@class="remove-filter"])[1]').click()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #
    #     # She sees the active filter is gone, checkbox is not checked and the
    #     # results are all there again
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 4)
    #     self.assertFalse(flag_cb.is_selected())
    #     active_filters = self.findManyBy(
    #         'xpath', '//div[@id="active-filters"]//li')
    #     self.assertEqual(len(active_filters), 0)
    #
    #     # She applies the filter once again
    #     flag_cb.click()
    #     self.apply_filter()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 1)
    #
    #     # She reloads the page
    #     url = self.browser.current_url
    #     self.browser.get(url)
    #
    #     # She sees that the results are correctly filtered
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 1)
    #     self.findBy(
    #         'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
    #                  'contains(text(), "Foo 4")]')
    #
    #     # The filter is in the list of active filters
    #     active_filter_panel = self.findBy(
    #         'xpath', '//div[@id="active-filters"]/div')
    #     self.assertTrue(active_filter_panel.is_displayed())
    #     active_filters = self.findManyBy(
    #         'xpath', '//div[@id="active-filters"]//li')
    #     self.assertEqual(len(active_filters), 1)
    #     filter_1 = self.findBy('xpath', '//div[@id="active-filters"]//li[1]')
    #     self.assertEqual(filter_1.text, 'UNCCD Best Practice')
    #
    #     # The checkbox is checked
    #     flag_cb = self.findBy('id', 'flag_unccd_bp')
    #     self.assertTrue(flag_cb.is_selected())
    #
    #     # She clicks "filter" again and sees the filter is not added twice.
    #     url = self.browser.current_url
    #     self.findBy('link_text', 'Advanced filter').click()
    #     self.apply_filter()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #     self.assertEqual(self.browser.current_url, url)

    # def test_filter_dates(self):
    #
    #     # Alice goes to the list view
    #     self.browser.get(self.live_server_url + reverse(
    #         route_questionnaire_list))
    #
    #     # She sees there are 4 Questionnaires in the list
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 4)
    #
    #     # There is no active filter set
    #     active_filter_panel = self.findBy(
    #         'xpath', '//div[@id="active-filters"]/div')
    #     self.assertFalse(active_filter_panel.is_displayed())
    #     active_filters = self.findManyBy(
    #         'xpath', '//div[@id="active-filters"]//li')
    #     self.assertEqual(len(active_filters), 0)
    #
    #     # She sees a link for advanced filtering which opens the filter
    #     # panel
    #     filter_panel = self.findBy('id', 'search-advanced-options')
    #     self.assertFalse(filter_panel.is_displayed())
    #     self.findBy('link_text', 'Advanced filter').click()
    #     self.assertTrue(filter_panel.is_displayed())
    #
    #     # She opens the date filter section
    #     self.findBy('id', 'filter-dates-heading').click()
    #
    #     WebDriverWait(self.browser, 10).until(
    #         EC.visibility_of_element_located(
    #             (By.CLASS_NAME, "filter-created")))
    #
    #     # She sees a slider to filter by creation date
    #     leftLabel = self.findBy(
    #         'xpath', '//span[contains(@class, "filter-created") and '
    #         'contains(@class, "leftLabel")]')
    #     self.assertEqual(leftLabel.text, '2000')
    #     rightLabel = self.findBy(
    #         'xpath', '//span[contains(@class, "filter-created") and '
    #         'contains(@class, "rightLabel")]')
    #     self.assertEqual(rightLabel.text, '2016')
    #
    #     url = self.browser.current_url
    #
    #     # She submits the filter and sees the slider values were not submitted
    #     self.apply_filter()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #     self.assertEqual(self.browser.current_url, '{}?'.format(url))
    #
    #     # She "changes" the slider
    #     created_slider_min = self.findBy(
    #         'xpath', '//input[contains(@class, "filter-created") and '
    #         'contains(@class, "min")]')
    #     self.changeHiddenInput(created_slider_min, '2014')
    #     self.apply_filter()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #
    #     # She sees that the filter was submitted in the url and the results
    #     # are filtered
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 1)
    #     self.findBy(
    #         'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
    #         'contains(text(), "Foo 4")]')
    #
    #     # The filter was added to the list of active filters
    #     active_filter_panel = self.findBy(
    #         'xpath', '//div[@id="active-filters"]/div')
    #     self.assertTrue(active_filter_panel.is_displayed())
    #     active_filters = self.findManyBy(
    #         'xpath', '//div[@id="active-filters"]//li')
    #     self.assertEqual(len(active_filters), 1)
    #     filter_1 = self.findBy('xpath', '//div[@id="active-filters"]//li[1]')
    #     self.assertEqual(filter_1.text, 'Created: 2014 - 2016')
    #
    #     # She also sets a filter for the updated year
    #     updated_slider_max = self.findBy(
    #         'xpath', '//input[contains(@class, "filter-updated") and '
    #         'contains(@class, "max")]')
    #     self.changeHiddenInput(updated_slider_max, '2012')
    #     self.apply_filter()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #
    #     # As the filters are joined by OR, there are now more results
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 3)
    #     self.findBy(
    #         'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
    #                  'contains(text(), "Foo 4")]')
    #     self.findBy(
    #         'xpath', '(//article[contains(@class, "tech-item")])[2]//a['
    #                  'contains(text(), "Foo 2")]')
    #     self.findBy(
    #         'xpath', '(//article[contains(@class, "tech-item")])[3]//a['
    #                  'contains(text(), "Foo 1")]')
    #
    #     filter_1 = self.findBy('xpath', '//div[@id="active-filters"]//li[1]')
    #     self.assertEqual(filter_1.text, 'Created: 2014 - 2016')
    #     filter_2 = self.findBy('xpath', '//div[@id="active-filters"]//li[2]')
    #     self.assertEqual(filter_2.text, 'Updated: 2000 - 2012')
    #
    #     # She removes the first filter (creation date), 2 entries show up
    #     self.findBy('xpath', '(//a[@class="remove-filter"])[1]').click()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 2)
    #     self.findBy(
    #         'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
    #         'contains(text(), "Foo 2")]')
    #     self.findBy(
    #         'xpath', '(//article[contains(@class, "tech-item")])[2]//a['
    #         'contains(text(), "Foo 1")]')
    #
    #     # She hits the button to remove all filters
    #     self.findBy('id', 'filter-reset').click()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #
    #     # She sees there are 4 Questionnaires in the list
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 4)
    #
    #     # There is no active filter set
    #     active_filter_panel = self.findBy(
    #         'xpath', '//div[@id="active-filters"]/div')
    #     self.assertFalse(active_filter_panel.is_displayed())
    #     active_filters = self.findManyBy(
    #         'xpath', '//div[@id="active-filters"]//li')
    #     self.assertEqual(len(active_filters), 0)
    #
    #     # She sets a filter again and reloads the page
    #     created_slider_min = self.findBy(
    #         'xpath', '//input[contains(@class, "filter-created") and '
    #         'contains(@class, "min")]')
    #     self.changeHiddenInput(created_slider_min, '2012')
    #     created_slider_max = self.findBy(
    #         'xpath', '//input[contains(@class, "filter-created") and '
    #         'contains(@class, "max")]')
    #     self.changeHiddenInput(created_slider_max, '2013')
    #
    #     created_left_handle = self.findBy(
    #         'xpath', '//div[contains(@class, "leftGrip") and contains(@class, '
    #         '"filter-created")]')
    #     self.assertEqual(
    #         created_left_handle.get_attribute('style'), 'left: 0px;')
    #
    #     self.apply_filter()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #     url = self.browser.current_url
    #     self.browser.get(url)
    #
    #     self.findBy('link_text', 'Advanced filter').click()
    #     self.findBy('id', 'filter-dates-heading').click()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.visibility_of_element_located(
    #             (By.CLASS_NAME, "filter-created")))
    #
    #     # She sees the filter is set
    #     list_entries = self.findManyBy(
    #         'xpath', '//article[contains(@class, "tech-item")]')
    #     self.assertEqual(len(list_entries), 2)
    #     self.findBy(
    #         'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
    #         'contains(text(), "Foo 3")]')
    #     self.findBy(
    #         'xpath', '(//article[contains(@class, "tech-item")])[2]//a['
    #         'contains(text(), "Foo 2")]')
    #
    #     # The filter was added to the list of active filters
    #     active_filter_panel = self.findBy(
    #         'xpath', '//div[@id="active-filters"]/div')
    #     self.assertTrue(active_filter_panel.is_displayed())
    #     active_filters = self.findManyBy(
    #         'xpath', '//div[@id="active-filters"]//li')
    #     self.assertEqual(len(active_filters), 1)
    #     filter_1 = self.findBy('xpath', '//div[@id="active-filters"]//li[1]')
    #     self.assertEqual(filter_1.text, 'Created: 2012 - 2013')
    #
    #     # She sees the slider is set to match the current filter
    #     created_left_handle = self.findBy(
    #         'xpath', '//div[contains(@class, "leftGrip") and contains(@class, '
    #         '"filter-created")]')
    #     self.assertNotEqual(
    #         created_left_handle.get_attribute('style'), 'left: 0px;')
    #
    #     # She removes the filter and sees that the slider position has
    #     # been reset.
    #     self.findBy('xpath', '(//a[@class="remove-filter"])[1]').click()
    #     WebDriverWait(self.browser, 10).until(
    #         EC.invisibility_of_element_located(
    #             (By.CLASS_NAME, "loading-indicator")))
    #     time.sleep(1)
    #     self.assertEqual(
    #         created_left_handle.get_attribute('style'), 'left: 0px;')
    #
    #     # She clicks "filter" again (slider not being set) and sees that
    #     # nothing is happening.
    #     # She submits the filter and sees the slider values were not submitted
    #     self.apply_filter()
    #     self.assertEqual(
    #         self.browser.current_url, '{}?'.format(
    #             self.live_server_url + reverse(route_questionnaire_list)))
    #     time.sleep(0.5)

    def test_filter_project(self):

        # Alice goes to the list view
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))

        # She sees there are 4 Questionnaires in the list
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)

        # There is no active filter set
        active_filter_panel = self.findBy(
            'xpath', '//div[@id="active-filters"]/div')
        self.assertFalse(active_filter_panel.is_displayed())
        active_filters = self.findManyBy(
            'xpath', '//div[@id="active-filters"]//li')
        self.assertEqual(len(active_filters), 0)

        # She sees a datalist to filter by project
        project_filter = self.findBy(
            'xpath', '//div/label[@for="filter-project"]/../div'
        )

        url = self.browser.current_url

        # She submits the filter and sees no values were submitted
        self.apply_filter()
        self.assertEqual(self.browser.current_url, '{}?type=sample'.format(url))

        # She enters a project
        project_filter = self.findBy(
            'xpath', '//div/label[@for="filter-project"]/../div'
        )
        project_filter.click()

        project_filter.find_element_by_xpath(
            '//ul[@class="chosen-results"]/li[text()="The first Project (TFP)"]'
        ).click()

        self.apply_filter()

        # She sees that the filter was submitted in the url and the results
        # are filtered
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
                     'contains(text(), "Foo 3")]')

        # The filter was added to the list of active filters
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertIn('The first Project (TFP)', active_filters[1].text)

        # She hits the button to remove all filters
        self.remove_filter(index=None)

        # She sees there are 4 Questionnaires in the list
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)

        # There is only one active filter
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 0)

        # She sets a filter again and reloads the page
        project_filter = self.findBy(
            'xpath', '//div/label[@for="filter-project"]/../div'
        )
        project_filter.click()
        project_filter.find_element_by_xpath(
            '//ul[@class="chosen-results"]/li[text()="The first Project (TFP)"]'
        ).click()
        self.apply_filter()

        url = self.browser.current_url
        self.browser.get(url)

        # She sees the filter is set
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
                     'contains(text(), "Foo 3")]')

        # The filter was added to the list of active filters
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertIn('The first Project (TFP)', active_filters[1].text)

        # She sees the text in the input field matches the project
        project_filter = self.findBy(
            'xpath', '//div/label[@for="filter-project"]/../div/a/span'
        )
        self.assertEqual(
            project_filter.text,
            'The first Project (TFP)'
        )

        # She removes the filter and sees that the input field has been
        # reset
        self.remove_filter(index=None)
        project_filter = self.findBy(
            'xpath', '//div/label[@for="filter-project"]/../div/a/span'
        )
        self.assertEqual(project_filter.text, 'Select or type a project name')

        # She clicks "filter" again and sees that nothing is happening.
        # She submits the filter and sees no values were submitted
        self.apply_filter()

        self.assertEqual(
            self.browser.current_url, '{}?type=sample'.format(
                self.live_server_url + reverse(route_questionnaire_list)))

    def test_filter_search(self):

        search_term = '4'

        # Alice goes to the list view
        self.browser.get(self.url_questionnaire_filter_sample)

        # She sees there are 4 Questionnaires in the list
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)

        # There is only the type filter active
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 1)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')

        self.add_advanced_filter('qg_11__key_14', 'value_14_1')

        # She sees the results are filtered
        expected_list = [
            {
                'title': 'Foo 4'
            },
            {
                'title': 'Foo 1'
            }
        ]
        self.check_list_results(expected_list)

        # She also searches for a word
        self.findBy('xpath', '//input[@type="search"]').send_keys(search_term)
        self.apply_filter()

        # She sees that both filters are applied, they are joined by AND
        expected_list = [
            {
                'title': 'Foo 4'
            }
        ]
        self.check_list_results(expected_list)

        # The filter was added to the list of active filters
        active_filters = self.get_active_filters(has_any=True)
        self.assertEqual(len(active_filters), 3)

        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, 'Key 14: Value 14_1')
        self.assertEqual(active_filters[2].text, f'Search Terms: {search_term}')

        # She removes one filter
        self.remove_filter(index=0)

        # The filters are updated
        active_filters = self.get_active_filters(has_any=True)
        self.assertEqual(len(active_filters), 2)

        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, f'Search Terms: {search_term}')

        # The results are filtered
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)

        # She goes to the home page
        self.browser.get(self.live_server_url + reverse(route_home))

        # She enters a search term there
        self.findBy('xpath', '//input[@type="search"]').send_keys(search_term)
        self.set_input_value('search-type', 'sample')
        self.findBy('id', 'submit-search').click()

        # She sees she is taken to the list view with the filter set
        active_filters = self.get_active_filters(has_any=True)
        self.assertEqual(len(active_filters), 2)

        self.assertEqual(active_filters[1].text, 'SLM Data: sample')
        self.assertEqual(active_filters[0].text, f'Search Terms: {search_term}')

        # The results are filtered
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)

        # She goes to the advanced filter and sees the filter is still active
        # there
        self.open_advanced_filter('sample')
        active_filters = self.get_active_filters(has_any=True)
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, f'Search Terms: {search_term}')
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 1)

        # She adds a second filter
        self.add_advanced_filter('qg_11__key_14', 'value_14_1')

        # The results are filtered
        expected_list = [
            {
                'title': 'Foo 4'
            }
        ]
        self.check_list_results(expected_list)

        # The filter was added to the list of active filters
        active_filters = self.get_active_filters(has_any=True)
        self.assertEqual(len(active_filters), 3)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, 'Key 14: Value 14_1')
        self.assertEqual(active_filters[2].text, f'Search Terms: {search_term}')

        # She removes all filters
        self.remove_filter(index=None)

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)

        # There is only one active filter left
        active_filters = self.get_active_filters(has_any=True)
        self.assertEqual(len(active_filters), 1)

        # The search field is empty
        search_field = self.findBy('xpath', '//input[@type="search"]')
        self.assertEqual(search_field.get_attribute('value'), '')

        # She searches again by keyword, this time entering two words
        search_field.send_keys(search_term)
        self.apply_filter()

        # The filter is set correctly
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, f'Search Terms: {search_term}')

        # She refreshes the page and sees the text in the search bar did not
        # change
        self.browser.get(self.browser.current_url)
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, f'Search Terms: {search_term}')
        search_field = self.findBy('xpath', '//input[@type="search"]')
        self.assertEqual(search_field.get_attribute('value'), search_term)

        # She removes the filter and sees it works.
        self.remove_filter(index=None)

        active_filters = self.get_active_filters(has_any=True)
        self.assertEqual(len(active_filters), 1)
        search_field = self.findBy('xpath', '//input[@type="search"]')
        self.assertEqual(search_field.get_attribute('value'), '')

        # She searches again by keyword, this time entering two words
        special_chars = ';ö$ ,_%as[df)'
        search_field.send_keys(special_chars)
        self.apply_filter()

        # The filter is set correctly
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(
            active_filters[1].text, f'Search Terms: {special_chars}')

        # She refreshes the page and sees the text in the search bar did not
        # change
        self.browser.get(self.browser.current_url)
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(
            active_filters[1].text, f'Search Terms: {special_chars}')
        search_field = self.findBy('xpath', '//input[@type="search"]')
        self.assertEqual(search_field.get_attribute('value'), special_chars)

        # She removes the filter and sees it works.
        self.remove_filter(index=None)

        active_filters = self.get_active_filters(has_any=True)
        self.assertEqual(len(active_filters), 1)
        search_field = self.findBy('xpath', '//input[@type="search"]')
        self.assertEqual(search_field.get_attribute('value'), '')

    def test_filter_country(self):

        # Alice goes to the list view
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))

        # She sees there are 4 Questionnaires in the list
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)

        # There is no active filter set
        self.get_active_filters(has_any=False)

        # She sees a chosen container to filter by country and opens it
        country_filter = self.findBy(
            'xpath', '//div/label[@for="filter-country"]/../div')
        country_filter.click()
        url = self.browser.current_url

        # She submits the filter and sees no values were submitted
        self.apply_filter()
        self.assertEqual(self.browser.current_url, '{}?type=sample'.format(url))

        # She opens the country filter again and selects the value for
        # Switzerland
        country_filter = self.findBy(
            'xpath', '//div/label[@for="filter-country"]/../div')
        country_filter.click()
        country_filter.find_element_by_xpath(
            '//ul[@class="chosen-results"]/li[text()="Switzerland"]'
        ).click()

        self.apply_filter()

        # She sees that the filter was submitted in the url and the results
        # are filtered
        expected_list = [
            {
                'title': 'Foo 4'
            },
            {
                'title': 'Foo 2'
            },
            {
                'title': 'Foo 1'
            }
        ]
        self.check_list_results(expected_list)

        # The filter was added to the list of active filters
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, 'Country: Switzerland')

        # She hits the button to remove all filters
        self.remove_filter(index=None)

        # She sees there are 4 Questionnaires in the list
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 4)

        # There is no active filter set
        self.get_active_filters(has_any=False)

        # She sets a filter again and reloads the page
        country_filter = self.findBy(
            'xpath', '//div/label[@for="filter-country"]/../div')
        country_filter.click()
        country_filter.find_element_by_xpath(
            '//ul[@class="chosen-results"]/li[text()="Afghanistan"]'
        ).click()
        self.apply_filter()

        url = self.browser.current_url
        self.browser.get(url)

        # She sees the filter is set
        expected_list = [
            {
                'title': 'Foo 3'
            }
        ]
        self.check_list_results(expected_list)

        # The filter was added to the list of active filters
        active_filters = self.get_active_filters()
        self.assertEqual(len(active_filters), 2)
        self.assertEqual(active_filters[0].text, 'SLM Data: sample')
        self.assertEqual(active_filters[1].text, 'Country: Afghanistan')

        # She sees the text in the input field matches the country
        selected_country = self.findBy(
            'class_name', 'chosen-single'
        ).find_element_by_tag_name('span')
        self.assertEqual(
            selected_country.text,
            'Afghanistan'
        )

        # She removes the filter and sees that the input field has been
        # reset
        self.remove_filter(index=None)
        selected_country = self.findBy(
            'class_name', 'chosen-single'
        ).find_element_by_tag_name('span')
        self.assertEqual(selected_country.text, 'Select or type a country name')

        # She clicks "filter" again and sees that nothing is happening.
        # She submits the filter and sees no values were submitted
        self.apply_filter()

        self.assertEqual(
            self.browser.current_url, '{}?type=sample'.format(
                self.live_server_url + reverse(route_questionnaire_list)))


@elasticmock
class ListTestLinks(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'global_key_values',
        'sample',
        'samplemulti',
        'sample_samplemulti_questionnaires',
    ]

    """
    1
        configurations: sample
        code: sample_1
        key_1 (en): This is the first key
        links: 3

    2
        configurations: sample
        code: sample_2
        key_1 (en): Foo
        links: -

    3
        configurations: samplemulti
        code: samplemulti_1
        key_1 (en): This is key 1a
        links: 1

    4
        configurations: samplemulti
        code: samplemulti_2
        key_1 (en): This is key 1b
        links: -
    """

    def setUp(self):
        super(ListTestLinks, self).setUp()
        create_temp_indices([('sample', '2015'), ('samplemulti', '2015')])

    def test_list_displays_links_user_questionnaires(self):

        user_alice = User.objects.get(pk=101)

        # Alice logs in
        self.doLogin(user=user_alice)

        # She enters a new questionnaire with some basic data
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_new_step,
            kwargs={'identifier': 'new', 'step': 'cat_1'}))
        self.findBy('name', 'qg_1-0-original_key_1').send_keys('Foo')
        self.findBy('name', 'qg_1-0-original_key_3').send_keys('Bar')
        self.submit_form_step()

        # She also links another questionnaire
        self.wait_for(
            'xpath',
            '//a[contains(@href, "/edit/") and contains(@href, "cat_5")]'
        )
        self.click_edit_section('cat_5')
        self.findBy(
            'xpath', '//input[contains(@class, "link-search-field")]'
                     '[1]').send_keys('key')
        self.wait_for('xpath', '//li[@class="ui-menu-item"]')
        self.findBy(
            'xpath',
            '//li[@class="ui-menu-item"]//strong[text()="This is key 1a"'
            ']').click()
        self.submit_form_step()

        # She goes to the page where she can see her own questionnaires
        self.clickUserMenu(user_alice)
        self.findBy(
            'xpath', '//li[contains(@class, "has-dropdown")]/ul/li/a['
             'contains(@href, "accounts/questionnaires")]').click()

        # She sees the newly created questionnaire and that it contains only one
        # link
        self.findBy('xpath', '(//article[contains(@class, "tech-item")])[1]//a'
                             '[contains(text(), "Foo")]')
        link_count = self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//ul['
                     'contains(@class, "tech-attached")]/li/a')
        self.assertEqual(link_count.text, '')  # No number

    def test_list_displays_links_search(self):

        # Alice logs in and creates a new questionnaire with some basic data and
        # a linked questionnaire
        user_alice = User.objects.get(pk=101)
        user_alice.groups = [Group.objects.get(pk=3), Group.objects.get(pk=4)]
        self.doLogin(user=user_alice)

        # She submits and publishes the questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_new_step,
            kwargs={'identifier': 'new', 'step': 'cat_1'}))
        self.findBy('name', 'qg_1-0-original_key_1').send_keys('Foo')
        self.findBy('name', 'qg_1-0-original_key_3').send_keys('Bar')
        self.submit_form_step()
        btn = '//a[contains(@href, "/edit/") and contains(@href, "cat_5")]'
        self.wait_for('xpath', btn)

        self.click_edit_section('cat_5')
        self.findBy(
            'xpath', '//input[contains(@class, "link-search-field")]'
                     '[1]').send_keys('key')
        self.wait_for('xpath', '//li[@class="ui-menu-item"]')
        self.findBy(
            'xpath',
            '//li[@class="ui-menu-item"]//strong[text()="This is key 1a"'
            ']').click()
        self.submit_form_step()

        self.review_action('submit')
        self.review_action('review')
        self.review_action('publish')

        # She goes to the SAMPLE search page and sees the questionnaires. These
        # are: 3 (newly created, with link), 2 and 1 (with link)
        self.browser.get(
            self.live_server_url + reverse(route_questionnaire_list))

        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 3)

        # She sees that the first one contains a link to SAMPLEMULTI. The link
        # count is only one!
        link_count_1 = self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//ul['
                     'contains(@class, "tech-attached")]/li/a')
        self.assertEqual(link_count_1.text, '')

        # Same for the third entry of the list
        link_count_3 = self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[3]//ul['
                     'contains(@class, "tech-attached")]/li/a')
        self.assertEqual(link_count_3.text, '')


@elasticmock
class ListTestStatus(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'global_key_values',
        'sample',
        'sample_questionnaire_status',
    ]

    def setUp(self):
        super(ListTestStatus, self).setUp()
        create_temp_indices([('sample', '2015')])

    # def test_unknown_name(self):
    #     user = create_new_user()
    #     user.groups = [
    #         Group.objects.get(pk=3), Group.objects.get(pk=4)]
    #     user.save()
    #
    #     # Alice logs in
    #     self.doLogin(user=user)
    #
    #     # She creates an empty questionnaire
    #     self.browser.get(self.live_server_url + reverse(
    #         route_questionnaire_new_step,
    #         kwargs={'identifier': 'new', 'step': 'cat_0'}))
    #     self.submit_form_step()
    #
    #     url = self.browser.current_url
    #
    #     # She goes to "my data" and sees it is listed there, no name indicated
    #     self.browser.get(self.live_server_url + reverse(
    #         accounts_route_questionnaires, kwargs={'user_id': user.id}))
    #
    #     self.findByNot('xpath', '//a[contains(text(), "{}")]'.format(
    #         "{'en': 'Unknown name'}"))
    #
    #     # She publishes the questionnaire
    #     self.browser.get(url)
    #     self.wait_for('class_name', 'review-panel-content')
    #
    #     self.review_action('submit')
    #     self.review_action('review')
    #     self.review_action('publish')
    #
    #     # She goes to the list and sees the data is listed there, "unknown name"
    #     # correctly displayed
    #     self.browser.get(self.live_server_url + reverse(
    #         route_questionnaire_list))
    #
    #     self.findByNot('xpath', '//a[contains(text(), "{}")]'.format(
    #         "{'en': 'Unknown name'}"))

    def test_list_status_public(self):

        # She goes to the list view and sees the same questionnaires
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))

        expected_results = [
            {
                'title': 'Foo 5',
                'status': 'public'
            },
            {
                'title': 'Foo 3',
                'status': 'public'
            },
        ]
        self.check_list_results(expected_results)

    def test_list_status_logged_in(self):

        # Alice logs in as user 1.
        user = User.objects.get(pk=101)
        self.doLogin(user=user)

        # Design change: Home also shows only public questionnaires

        # She goes to the list view and sees only the public
        # questionnaires
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))

        expected_results = [
            {
                'title': 'Foo 5',
                'status': 'public'
            },
            {
                'title': 'Foo 3',
                'status': 'public'
            },
        ]
        self.check_list_results(expected_results)

        # She logs in as user 2
        user = User.objects.get(pk=102)
        self.doLogin(user=user)

        # Design change: Home also shows only public questionnaires

        # She goes to the list view and sees only the public
        # questionnaires
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_list))

        self.check_list_results(expected_results)

    def test_list_shows_only_one_public(self):

        code = 'sample_3'
        old_key_1 = 'Foo 3'
        new_key_1 = 'asdf'

        old_questionnaire_count = Questionnaire.objects.count()

        # Alice logs in and goes to the detail page of a "public" Questionnaire
        user = User.objects.get(pk=101)
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': code}
        detail_page.open(login=True, user=user)
        assert code in self.browser.current_url

        assert detail_page.has_text(old_key_1)
        assert not detail_page.has_text(new_key_1)

        # She edits the Questionnaire and sees that the URL contains the
        # code of the Questionnaire
        detail_page.create_new_version()
        edit_page = SampleEditPage(self)
        edit_page.click_edit_category('cat_1')
        assert code in self.browser.current_url

        step_page = SampleStepPage(self)
        step_page.enter_text(
            step_page.LOC_FORM_INPUT_KEY_1, new_key_1, clear=True)
        step_page.submit_step()

        # She sees that the value of Key 1 was updated
        assert not edit_page.has_text(old_key_1)
        assert edit_page.has_text(new_key_1)

        # Also there was an additional version created in the database
        assert Questionnaire.objects.count() == old_questionnaire_count + 1

        # The newly created version has the same code
        assert Questionnaire.objects.filter(code=code).count() == 2

        # She goes to the list view and sees only two entries: Foo 5 and Foo 3
        list_page = SampleListPage(self)
        list_page.open()
        list_results = [
            {
                'title': 'Foo 5'
            },
            {
                'title': old_key_1,
            }
        ]
        list_page.check_list_results(list_results)

        # She goes to the detail page of the questionnaire and sees the
        # draft version.
        list_page.click_list_entry(index=1)
        detail_page.expand_details()
        assert not detail_page.has_text(old_key_1)
        assert detail_page.has_text(new_key_1)

        # She submits the questionnaire
        detail_page.submit_questionnaire()

        # In the DB, there is one active version
        db_q = Questionnaire.objects.filter(code=code, status=4)
        assert db_q.count() == 1
        db_q_id = db_q[0].id

        # Bob (the moderator) logs in
        # The moderator publishes the questionnaire
        user_moderator = User.objects.get(pk=105)
        detail_page.open(login=True, user=user_moderator)
        detail_page.review_questionnaire()
        detail_page.publish_questionnaire()

        # In the DB, there is still only one active version but it has a
        # different ID now.
        db_q = Questionnaire.objects.filter(code=code, status=4)
        assert db_q.count() == 1
        assert db_q_id != db_q[0].id

        # He goes to the list view and sees only two entries: asdf and Foo 6.
        list_page = SampleListPage(self)
        list_page.open()
        list_results = [
            {
                'title': 'Foo 5'
            },
            {
                'title': new_key_1
            },
        ]
        list_page.check_list_results(list_results)
