import json

from apps.configuration.structure import ConfigurationStructure
from django.core.management import BaseCommand


class Command(BaseCommand):

    help = 'Get the structure of a questionnaire configuration. The structure' \
           ' is stored in a file (by default called ' \
           'configuration_structure_[code]_[edition].json) in the root ' \
           'directory of the project.'

    def add_arguments(self, parser):
        parser.add_argument(
            'code',
            type=str,
            help='The code of the configuration (e.g. technologies).'
        )
        parser.add_argument(
            'edition',
            type=str,
            help='The edition of the configuration (e.g. 2018).'
        )
        parser.add_argument(
            '-o',
            '--output',
            default=None,
            dest='output',
            help='Specifies file to which the output is written.'
        )
        parser.add_argument(
            '--flat',
            action='store_true',
            default=False,
            help='Return the structure as a flat list of questions instead of '
                 'a nested JSON.'
        )

    def handle(self, *args, **options):

        structure_obj = ConfigurationStructure(
            code=options['code'],
            edition=options['edition'],
            flat=options['flat'],
        )

        if structure_obj.error:
            print('\nError:')
            print(structure_obj.error)
            return

        output_file = options['output']
        if output_file is None:
            output_file = f'configuration_structure_{options["code"]}_' \
                          f'{options["edition"]}.json'

        with open(output_file, 'w') as f:
            json.dump(structure_obj.structure, f, indent=2)

        print(f'File {output_file} written.')
