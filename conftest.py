"""
Use this file to setup envdir and django-configurations, as this works nicely with PyCharms
integrated (clickable) test feature.
"""

import os
import envdir
import configurations
import pytest

envdir.read(os.path.join(os.path.dirname(__file__), 'envs'))
os.environ.__setitem__('DJANGO_CONFIGURATION', 'TestDefaultSite')
configurations.setup()


@pytest.fixture
def es(request):
    """
    In order to allow multiple Elasticsearch indices when running tests in
    parallel, overwrite ES_INDEX_PREFIX settings for each test function
    according to its slave id.

    Usage for tests that require Elasticsearch:
    @pytest.mark.usefixtures('es')
    """
    from django.conf import settings
    from apps.search.index import get_elasticsearch
    from apps.search.search import get_indices_alias

    # Clear lru_cache of Elasticsearch indices.
    get_indices_alias.cache_clear()

    # Test setup
    xdist_suffix = getattr(
        request.config, 'slaveinput', {}
    ).get('slaveid', 'es_test_index')
    es_prefix = f'{settings.ES_INDEX_PREFIX}{xdist_suffix}'
    setattr(settings, 'ES_INDEX_PREFIX', es_prefix)

    # Actual test
    yield

    # Test teardown
    #get_elasticsearch().indices.delete(index=f'{es_prefix}*')


@pytest.fixture(scope='session', autouse=True)
def clear_configuration_cache():
    from apps.configuration.cache import get_cached_configuration
    get_cached_configuration.cache_clear()
