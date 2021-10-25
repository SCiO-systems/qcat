import logging
from unittest.mock import patch

from django.urls import reverse
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from functional_tests.base import FunctionalTest
from apps.summary.views import SummaryPDFCreateView

driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver")
logging.disable(logging.CRITICAL)


class SummaryTest(FunctionalTest):

    fixtures = [
        'global_key_values',
        'sample',
        'sample_questionnaires',
    ]

    def setUp(self):
        super().setUp()
        self.url = '{base}{summary_url}'.format(
            base=self.live_server_url,
            summary_url=reverse('questionnaire_summary', kwargs={'id': 1})
        )
        self.data_title_mock = {
            'title': {
                'partials': {
                    'title': 'Success story',
                    'country': 'Wonderland',
                    'local_name': 'The Rabbit Hole',
                }
            }
        }

    def test_summary_no_configured_summary(self):
        # The summary page is visited, but no configuration is stored for the
        # sample summary
        response = self.browser.get(self.url)
        self.assertIsNone(response)

    # opening files seems tricky. as almost the same is tested with the
    # ?as=html, not much effort was put into this test.
    # @patch.object(QuestionnaireSummaryPDFCreateView, 'get_template_names')
    # @patch('questionnaire.views.get_summary_data')
    # def test_summary_pdf(self, mock_get_summary, mock_template_names):
    #     profile = webdriver.FirefoxProfile()
    #     profile.set_preference('browser.helperApps.neverAsk.openfile',
    #                            'application/pdf')
    #     browser = webdriver.Firefox(
    #         firefox_binary=FirefoxBinary(settings.TESTING_FIREFOX_PATH),
    #         firefox_profile=profile
    #     )
    #     mock_get_summary.return_value = self.data_title_mock
    #     mock_template_names.return_value = 'questionnaire/summary/layout/' \
    #                                        'technologies.html'
    #
    #     response = browser.get(self.url)

    @patch.object(SummaryPDFCreateView, 'get_template_names')
    @patch.object(SummaryPDFCreateView, 'get_summary_data')
    def test_summary_html(self, mock_get_summary, mock_template_names):
        rendered_summary = 'summary'
        mock_get_summary.return_value = rendered_summary
        mock_template_names.return_value = 'summary/layout/base.html'

        self.browser.get('{}?as=html'.format(self.url))
        self.assertIn(rendered_summary, self.browser.page_source)
