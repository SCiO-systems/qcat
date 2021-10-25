from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.search.index import delete_all_indices, put_all_data


class Command(BaseCommand):
    """
    Delete, recreate and fill all indexes.
    """
    def handle(self, **options):
        delete_all_indices()
        call_command('create_es_indexes')
        put_all_data()
