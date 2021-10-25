import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Avg, Sum, Max
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from tabulate import tabulate

from apps.qcat.models import MemoryLog


class Command(BaseCommand):
    help = 'Read log files and show some metrics.'

    # Delimiter in the log files
    delimiter = ';'
    # Glob pattern for log file names
    cache_file_name = 'caches.log*'
    # Number of results to display
    slice_size = 10
    # temporary file path, to store downloaded logs
    tmp = '/tmp/qcat-logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-truncate',
            dest='no-truncate',
            action='store_true',
            default=False,
            help='Do not truncate db if a path for log files is given!'
        )

        parser.add_argument(
            '--download-logs',
            dest='download',
            default='',
            help='SSH path (user@server:/path/to/logs/) to fetch logs from. They are stored in the '
                 'folder as defined in self.tmp (/tmp/qcat-logs).'
        )

        parser.add_argument(
            '--path',
            dest='path',
            default='',
            help='Path to folder containing log files'
        )

    def handle(self, *args, **options):
        if options['download']:
            self.download_logs(ssh_cmd=options['download'])
            options['path'] = f'{self.tmp}'

        if options['path']:
            if not options['no-truncate']:
                self.truncate_logs_in_db()
            self.save_logs_to_db(path=options['path'])

        self.display_stats()

    def download_logs(self, ssh_cmd):
        subprocess.call(
            args=f'rsync -avz --delete -e "ssh" {ssh_cmd} {self.tmp}',
            shell=True
        )

    def save_logs_to_db(self, path):
        """
        Read log files and save them to the DB for easy AVG, SUM and stuff.
        """
        log_files = Path(path).glob(self.cache_file_name)
        for log in log_files:
            with log.open() as f:
                print(f'Importing {log.name}')
                self.parse_lines(*f.readlines())

    @property
    def titles(self):
        """
        Model field names without the ID field.
        """
        return [field.name for field in MemoryLog._meta.get_fields()[1:]]

    def parse_lines(self, *lines):
        """
        Split given lines according to delimiter, and prepare model row generation.
        """
        memory_logs = []
        for line in lines:
            attrs = {}
            for index, param in enumerate(line.split(self.delimiter)):
                # Read datetime from string. Not the nicest approach, but the log is always 'info',
                # so it starts at position 5.
                if index is 0:
                    param = make_aware(parse_datetime(param[5:21]))
                attrs[self.titles[index]] = param
            memory_logs.append(MemoryLog(**attrs))
        MemoryLog.objects.bulk_create(memory_logs)

    @staticmethod
    def truncate_logs_in_db():
        MemoryLog.objects.all().delete()

    def display_stats(self):
        """
        Show:
        - largest absolute increments
        - largest avg increments
        - largest sum of increments

        """
        self.display_largest_increments()
        self.display_largest_distinct_increments()
        self.display_average_increments()
        self.display_sum_increments()

    def display_largest_increments(self):
        qs = MemoryLog.objects.values(
            'params', 'increment'
        ).order_by(
            '-increment'
        )
        self.print_rows(
            title='Largest absolute (single) increments',
            queryset=qs
        )

    def display_largest_distinct_increments(self):
        qs = MemoryLog.objects.values(
            'params'
        ).annotate(
            Max('increment')
        ).order_by(
            '-increment'
        )

        self.print_rows(
            title='Largest absolute (single) distinct increments',
            queryset=qs
        )

    def display_average_increments(self):
        qs = MemoryLog.objects.values(
            'params'
        ).annotate(
            Avg('increment')
        ).order_by(
            '-increment__avg'
        )
        self.print_rows(
            title='Highest average increments',
            queryset=qs
        )

    def display_sum_increments(self):
        qs = MemoryLog.objects.values(
            'params'
        ).annotate(
            Sum('increment')
        ).order_by(
            '-increment__sum'
        )
        self.print_rows(
            title='Highest sum of increments',
            queryset=qs
        )

    def print_rows(self, title, queryset):
        print('\n')
        print(title.upper())
        rows = []
        for item in queryset[0:self.slice_size]:
            # Use 'values', as dict keys may vary (increment, increment__sum, ...)
            values = list(item.values())
            # Meh - cast increment to size in MB.
            values[1] = int(values[1]) >> 20
            rows.append(values)
        print(tabulate(
            tabular_data=rows,
            headers=['Params', 'Increment (MB)'],
            tablefmt='grid')
        )
        print('\n')
