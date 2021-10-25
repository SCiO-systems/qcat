from django.core.cache import cache
from django.core.management.base import BaseCommand

from apps.accounts.client import WocatWebsiteUserClient
from apps.configuration.models import Institution, Country
from apps.configuration.conf import settings


class Command(BaseCommand, WocatWebsiteUserClient):

    created = []
    updated = []
    deleted = []

    def handle(self, **options):

        institutions = self.fetch_institutions()

        for institution in institutions:
            self.create_or_update_institutions(institution)

        self.delete_institutions()

        self.update_cache()

        self.stdout.write(
            f'Created {len(self.created)} institutions, '
            f'updated {len(self.updated)} institutions, '
            f'deleted (set inactive) {len(self.deleted)} institutions')

    def delete_institutions(self):
        active_ids = self.created + self.updated
        self.deleted = Institution.objects.exclude(id__in=active_ids)
        self.deleted.update(active=False)

    def create_or_update_institutions(self, institution: dict):

        # Prepare DB values
        values = {
            'id': int(institution['id']),
            'name': institution['name'],
            'abbreviation': institution['abbreviation'],
            'country': Country.get(institution['country']),
            'active': True,
        }
        institution_object, created = Institution.objects.update_or_create(
            id=values['id'], defaults=values)
        if created is True:
            self.created.append(institution_object.id)
        else:
            self.updated.append(institution_object.id)

    def fetch_institutions(self):
        api_end_point = 'institutions/'

        r = self._get(api_end_point)

        if r.ok:
            return r.json()

        else:
            self.stdout.write(
                f'Error syncing institutions: '
                f'Query to API returned status {r.status_code}')
            return []

    @staticmethod
    def update_cache():
        # Update happens on first call of Institution.as_select()
        cache.delete(settings.CONFIGURATION_CACHE_KEY_INSTITUTION_SELECT)
