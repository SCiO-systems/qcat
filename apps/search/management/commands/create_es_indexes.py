from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import activate

from apps.configuration.cache import get_configuration
from apps.configuration.models import Configuration
from ...index import get_mappings, create_or_update_index


class Command(BaseCommand):
    """
    This command creates elasticsearch indexes for all available
    questionnaires. This is primarily used for running tests on shippable.
    """
    def handle(self, **options):
        """
        Loop over all active configurations, get the mappings and create the
        elasticsearch-indexes.

        Args:
            **options: None

        """
        configurations = Configuration.objects.all()
        for language in dict(settings.LANGUAGES).keys():
            activate(language)
            for configuration in configurations:
                questionnaire_configuration = get_configuration(
                    code=configuration.code, edition=configuration.edition
                )
                mappings = get_mappings()
                create_or_update_index(
                    configuration=questionnaire_configuration,
                    mappings=mappings
                )
