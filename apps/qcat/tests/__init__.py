import pytest
from django.test import TestCase as DjangoTestCase
from django.test.utils import override_settings

TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache/test',
        'TIMEOUT': 0,
    }
}


@override_settings(CACHES=TEST_CACHES)
@override_settings(DEBUG=True)
@override_settings(USE_TZ=False)
@pytest.mark.unit
class TestCase(DjangoTestCase):

    def setup_view(self, view, request, *args, **kwargs):
        """
        Mimic as_view() returned callable, but returns view instance.

        See: http://tech.novapost.fr/django-unit-test-your-views-en.html
        """
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view
