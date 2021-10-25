import inspect
import logging
import os
import psutil

from django.conf import settings


logger = logging.getLogger('profile_log')


def log_memory_usage(func):
    """
    Simple decorator which logs memory usage of decorated function.

    Notes:
        - The first logged info should be the resource type. In this case, it's always the parent,
          so this is wrong for decorated functions or such.

        - The second logged info is the 'params', and as of now only the keyword arguments are
          logged. If other modules than cache.py are logged, this should probably change.

    """
    delimiter = ';'

    def wrapper(*args, **kwargs):
        if settings.IS_ACTIVE_FEATURE_MEMORY_PROFILER:
            django_process = psutil.Process(pid=os.getpid())
            memory_before = django_process.memory_info().vms

        result = func(*args, **kwargs)

        if settings.IS_ACTIVE_FEATURE_MEMORY_PROFILER:
            increment = django_process.memory_info().vms - memory_before

            if increment:
                called_from = inspect.stack()[1]
                callee_module = inspect.getmodule(called_from[0])

                # Don't log any params for sensitive vars, the record type should be sufficient.
                params = callee_module.__name__
                if not hasattr(func, 'sensitive_variables'):
                    params = ",".join(kwargs.values())

                logger.info(
                    msg=f'{delimiter}{callee_module.__name__}'
                        f'{delimiter}{params}'
                        f'{delimiter}{memory_before}'
                        f'{delimiter}{increment}'
                )

        return result

    return wrapper


