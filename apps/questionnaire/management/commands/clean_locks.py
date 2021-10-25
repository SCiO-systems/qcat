from datetime import timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from django.utils.timezone import now
from apps.questionnaire.models import Lock


class Command(BaseCommand):
    """
    Purge stale locks.
    """
    def handle(self, **options):
        expired = now() - timedelta(minutes=settings.QUESTIONNAIRE_LOCK_TIME)
        Lock.objects.filter(
            Q(is_finished=True) | Q(start__lte=expired)
        ).delete()
