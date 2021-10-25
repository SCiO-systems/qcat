import os
import psutil
import logging

from django.conf import settings
from django.core.cache import cache


class StaffFeatureToggleMiddleware:
    """
    Staff members are either logged in, or are making requests from the CDE subnet.
    """
    def process_request(self, request):
        cache.set(key='is_cde_user', value=self.is_cde_user(request=request))

    def is_cde_user(self, request) -> bool:
        """
        Check if user is a logged in staff memeber or if the request stems from the CDE subnet.
        """
        is_from_cde_subnet = request.META.get('REMOTE_ADDR', '').startswith(settings.CDE_SUBNET_ADDR)
        is_logged_in_staff = hasattr(request, 'user') and request.user.is_staff
        return is_from_cde_subnet or is_logged_in_staff


class ProfilerMiddleware:
    """
    Write following info to a logfile, separated by a delimiter (for csv import):
    - source of record (middleware, caching)
    - params (identifying the action)
    - memory in use
    - memory increment

    When adding info to the log at a different layer (e.g. db), this structure must remain in place!

    """
    logger = logging.getLogger('profile_log')
    memory_at_request = 'memory_at_request'
    delimiter = ';'
    record_type = 'middleware'

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    def process_request(self, request):
        if settings.IS_ACTIVE_FEATURE_MEMORY_PROFILER:
            setattr(request, self.memory_at_request, self.current_memory_usage)

    def process_response(self, request, response):
        if settings.IS_ACTIVE_FEATURE_MEMORY_PROFILER and hasattr(request, self.memory_at_request):
            current_memory = self.current_memory_usage
            increment = current_memory - getattr(request, self.memory_at_request)
            # Exclude logging of static assets (favicon, etc.)
            if increment:
                self.logger.info(
                    msg=f'{self.delimiter}{self.record_type}'
                        f'{self.delimiter}{request.path}'
                        f'{self.delimiter}{current_memory}'
                        f'{self.delimiter}{increment}'
                )
        return response

    @property
    def current_memory_usage(self):
        django_process = psutil.Process(pid=os.getpid())
        memory = django_process.memory_info()
        return memory.vms
