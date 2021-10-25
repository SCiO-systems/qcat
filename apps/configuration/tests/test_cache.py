from django.test.utils import override_settings
from unittest.mock import patch

from apps.configuration.cache import get_configuration
from apps.qcat.tests import TestCase


@patch('apps.configuration.cache.cache')
class GetConfigurationQueryFilterTest(TestCase):

    @override_settings(USE_CACHING=True)
    def test_returns_cache_if_found(self, mock_cache):
        mock_cache.get.return_value = 'bar'
        ret = get_configuration('foo', 'edition_2015')
        self.assertEqual(ret, 'bar')

    @override_settings(USE_CACHING=True)
    def test_does_not_set_cache_if_found(self, mock_cache):
        mock_cache.get.return_value = 'bar'
        get_configuration('foo', 'edition_2015')
        self.assertEqual(mock_cache.set.call_count, 0)
