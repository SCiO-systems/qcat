from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    """
    This Command handles the creation of the static initial values of
    QCAT, namely:

    * Create groups and permissions as found in
      ``accounts.fixtures.group_permissions.json``.

    Usage::
        (env)$ python3 manage.py load_qcat_data

    .. warning::
        Running this command will erase existing content in the given
        tables and insert new data. Handle with care!
    """
    def handle(self, **options):

        call_command('loaddata', 'groups_permissions')
        call_command('loaddata', 'global_key_values')
        call_command('loaddata', 'flags')
