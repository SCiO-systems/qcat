import contextlib
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.urls import reverse
from django.test import RequestFactory, override_settings
from django.utils.translation import get_language

from apps.qcat.tests import TestCase
from apps.configuration.models import Configuration
from apps.configuration.cache import get_configuration, get_cached_configuration
from apps.configuration.views import BuildAllCachesView, delete_caches, EditionNotesView


class CacheTest(TestCase):

    fixtures = [
        'sample_global_key_values',
        'sample',
    ]
    locmem = {'default': {'BACKEND': 'django.core.cache.backends.locmem.'
                                     'LocMemCache'}}

    def setUp(self):
        self.factory = RequestFactory()
        # Initially clear cache
        get_cached_configuration.cache_clear()

    def setup_view(self, view, request, *args, **kwargs):
        """
        Mimic ``as_view()``, but returns view instance.
        Use this function to get view instances on which you can run unit tests,
        by testing specific methods.
        """
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view

    @override_settings(CACHES=locmem, USE_CACHING=True)
    def test_build_cache(self):
        """
        Integration test: check valid cache after call to view.
        """
        request = self.factory.get(reverse('search:build_caches'))
        request._messages = MagicMock()
        view = self.setup_view(BuildAllCachesView(), request)
        view.get(request)
        self.assertIsNotNone(cache.get('sample_2015_{}'.format(get_language())))

    @override_settings(CACHES=locmem, USE_CACHING=True)
    def test_clear_cache(self):
        config = Configuration.objects.all().first()
        get_configuration(code=config.code, edition=config.edition)
        cache_key = '{}_{}_{}'.format(
            config.code, config.edition, get_language())
        self.assertIsNotNone(cache.get(cache_key))
        request = MagicMock()
        request.user.is_superuser = True

        # Missing messages-framework will raise a type error.
        with contextlib.suppress(TypeError):
            delete_caches(request)
            self.assertIsNone(cache.get(cache_key))


class EditionNotesViewTest(TestCase):

    def setUp(self):
        self.request = RequestFactory().get(reverse('configuration:release_notes'))
        self.view = self.setup_view(
            view=EditionNotesView(),
            request=self.request
        )

    def test_get(self):
        with patch.object(EditionNotesView, 'get_editions') as get_editions_mock:
            self.view.get(request=self.request)
            self.assertTrue(get_editions_mock.called)
