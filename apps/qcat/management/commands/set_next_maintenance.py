from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now


class Command(BaseCommand):
    """
    Set the datetime for the next maintenance window, so the users can be
    informed.
    """
    def handle(self, **options):
        with open(settings.NEXT_MAINTENANCE, 'w+') as f:
            f.write(
                (now() + timedelta(seconds=settings.DEPLOY_TIMEOUT)).isoformat()
            )
