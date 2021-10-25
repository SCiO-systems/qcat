from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import activate

from apps.configuration.cache import get_configuration
from apps.configuration.models import Configuration


class Command(BaseCommand):
    """
    This command creates all configuration caches for the current process.
    """
    def handle(self, **options):
        languages = dict(settings.LANGUAGES).keys()
        for configuration in Configuration.objects.all():
            for language in languages:
                activate(language)
                get_configuration(configuration.code, configuration.edition)
