from apps.configuration.models import Configuration
from functools import lru_cache

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import get_language

from apps.qcat.decorators import log_memory_usage


def get_configuration(code: str, edition: str):
    """
    Return a QuestionnaireConfiguration. If cache is being used (setting
    ``USE_CACHING=True``), it is returned from the cache if found. If
    not found, it is added to the cache and returned. If the use of
    cache is deactivated, always a new configuration is returned.

    Args:
        ``configuration_code`` (str): The code of the configuration

    Returns:
        ``QuestionnaireConfiguration``. The Questionnaire configuration,
        either returned from cache or newly created.
    """

    if settings.USE_CACHING:
        cache_key = get_cache_key(code, edition)
        configuration = get_cached_configuration(
            cache_key=cache_key, code=code, edition=edition)
        return configuration

    return get_configuration_by_code_edition(code=code, edition=edition)


@lru_cache(maxsize=32)
@log_memory_usage
def get_cached_configuration(cache_key: str, code: str, edition: str):
    """
    Simple retrieval. If object is not in the lru_cache, use the default cache
    from django as fallback.

    @todo: refactor configurations. this is a workaround due to bad performance
    which caches the configs in two places (memcached and python-threads -->
    twice the memory usage!). configurations should probably be cached by
    section or such.
    """
    configuration = cache.get(cache_key)

    if not configuration:
        configuration = get_configuration_by_code_edition(code, edition)
        cache.set(key=cache_key, value=configuration)

    return configuration


def get_configuration_by_code_edition(code: str, edition: str):
    """
    Get the configuration object.
    """
    from apps.configuration.configuration import QuestionnaireConfiguration
    configuration_object = Configuration.objects.get(code=code, edition=edition)
    return QuestionnaireConfiguration(
        code, configuration_object=configuration_object)


def delete_configuration_cache(configuration_object):
    """
    Delete a configuration object from the cache (incl. lru_cache) if it exists. Also remove all
    QuestionnaireSections from the cache.
    cache.clear() is not used, as the cache is shared on some hosts.

    Args:
        ``configuration_object`` (``QuestionnaireConfiguration``): The
        configuration object whose configuration is to be deleted.
    """
    if settings.USE_CACHING:
        cache_key = get_cache_key(
            configuration_object.code, configuration_object.edition)
        cache.delete(cache_key)
        get_cached_configuration.cache_clear()


def get_cache_key(configuration_code: str, edition: str) -> str:
    """
    Return the key under which a given configuration is stored in the
    cache. Currently, the key is composed as:
    ``[configuration_code]_[locale]``, for example ``technologies_en``.

    Args:
        ``configuration_code`` (str): The code of the configuration

    Returns:
        ``str``. The key for the cache.
    """
    return '{}_{}_{}'.format(configuration_code, edition, get_language())
