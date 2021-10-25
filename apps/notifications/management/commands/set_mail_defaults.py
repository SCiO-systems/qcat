from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.notifications.models import MailPreferences


class Command(BaseCommand):
    """
    Set default mailpreferences for existing users.
    """
    def handle(self, **options):
        for user in get_user_model().objects.all():
            MailPreferences(user=user).set_defaults()
