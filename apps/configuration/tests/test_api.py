import logging

from django.test import RequestFactory

from apps.qcat.tests import TestCase
from apps.configuration.api.views import ConfigurationView, ConfigurationEditionView


class ConfigurationViewTest(TestCase):
    """
    Tests Code for v2
    """
    fixtures = [
        'global_key_values',
        'sample',
    ]

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.factory = RequestFactory()
        self.url = '/en/api/v2/configuration'
        self.request = self.factory.get(self.url)
        self.request.version = 'v2'
        # self.invalid_request = self.factory.get('/en/api/v2/foo')
        self.view = self.setup_view(
            ConfigurationView(), self.request
        )

    def test_get_object(self):
        response = self.view.get(self.request)
        self.assertEqual(response.status_code, 200)


class ConfigurationEditionViewTest(TestCase):
    """
    Tests Editions for v2
    """

    fixtures = [
        'global_key_values',
        'sample',
    ]

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.factory = RequestFactory()
        self.url = '/en/api/v2/configuration/sample'
        self.request = self.factory.get(self.url)
        self.request.version = 'v2'
        self.code = 'sample'
        self.view = self.setup_view(
            ConfigurationEditionView(), self.request, code=self.code
        )

    def test_get_object(self):
        response = self.view.get(self.request, code=self.code)
        self.assertEqual(response.status_code, 200)

