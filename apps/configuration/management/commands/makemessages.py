# -*- coding: utf-8 -*-
import os
import subprocess

from django.core.management import call_command
from django.core.management.commands import makemessages
from django.db.models import Q

from apps.configuration.cache import get_configuration
from apps.configuration.models import Translation, TranslationContent, Configuration


class Command(makemessages.Command):
    """
    Extended version of the default 'makemessages' command.

    - Pull the latest files from transifex
    - Compile the .po files
    - Create new model entries (TranslatedContent) if necessary, create a
      temporary file which will be parsed by djangos 'makemessages'
    - Create po files
    - Ask the user, if uploading the files to transifex is desired.
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--create-only', '-co', action='store_true',
                            dest='do_create_only', default=False,
                            help='Create new po files only - omit pulling from'
                                 'transifex and compiling new mo files.')

        parser.add_argument('--force-pull', '-fp', action='store_true',
                            dest='do_force_pull', default=False,
                            help='Force pull from transifex.')

    def handle(self, *args, **options):
        self.only_on_develop()

        # Pull latest translations from transifex - unless specified otherwise.
        if not options.get('do_create_only'):
            print('Pulling latest from transifex')
            subprocess.call('tx pull --mode=developer{}'.format(
                ' -f' if options.get('do_force_pull') else ' '
            ), shell=True)

            print('Compiling latest po files')
            call_command('compilemessages')

        configuration_helper_file = os.path.join(
            'apps', 'configuration', 'configuration_translations.py'
        )

        # Get a list of all used Translations by all configurations. This can
        # then be used to remove unused translations.
        used_translation_ids = []
        for configuration in Configuration.objects.all():
            questionnaire_configuration = get_configuration(
                code=configuration.code, edition=configuration.edition)
            used_translation_ids.extend(
                questionnaire_configuration.get_translation_ids())

        # Remove duplicates
        used_translation_ids = set(used_translation_ids)

        # It is not enough to check for new 'Translation' rows as new
        # configuration editions can update only the translation for the new
        # edition which creates a new entry in the existing 'Translation' data
        # json.
        # Instead, first get all existing content of TranslationContent, group
        # it by configuration and keyword. Then extract all entries in the
        # 'Translation' table and see if they are already available in the
        # 'TranslationContent' table. If not, create them later.
        existing_translation_content = {}
        for existing in TranslationContent.objects.all():
            (existing_translation_content
                .setdefault(existing.configuration, {})
                .setdefault(existing.keyword, [])
                .append(existing.text))

        unused_translation_ids = []
        for translation in Translation.objects.all():

            if translation.id not in used_translation_ids:
                unused_translation_ids.append(translation.id)
                continue

            for configuration, contents in translation.data.items():
                for keyword, translated_items in contents.items():

                    # Only English texts are expected. If 'en' is not available,
                    # this must raise an exception.
                    translation_string = translated_items['en']

                    if translation_string in existing_translation_content.get(
                            configuration, {}).get(keyword, []):
                        # String already in TranslationContent, do nothing.
                        continue

                    # Add new strings to TranslationContent
                    TranslationContent(
                        translation=translation,
                        configuration=configuration,
                        keyword=keyword,
                        text=translation_string
                    ).save()

                    if len(translated_items.keys()) != 1:
                        print(u'Warning: More than one translation in the'
                              u'fixtures. Only the English text is used.')

        if unused_translation_ids:
            print(
                'The following translations are not needed anymore. They will '
                'be deleted. You should also remove these from the fixtures, '
                'along with the keys/values/categories they belong to (if they '
                'still exist). \n%s' %
                '\n'.join([str(i) for i in sorted(unused_translation_ids)]))
            TranslationContent.objects.filter(
                translation__id__in=unused_translation_ids).delete()
            Translation.objects.filter(id__in=unused_translation_ids).delete()

        # All translations must be written to the file again.
        # By using pgettext and contextual markers, one separate
        # translation per configuration and keyword is ensured.
        all_translations = TranslationContent.objects.exclude(
            text=''
        ).filter(
            Q(translation__category__isnull=False) |
            Q(translation__questiongroup__isnull=False) |
            Q(translation__key__isnull=False) |
            Q(translation__value__isnull=False)
        ).order_by(
            'translation__id', 'id'
        )
        with open(configuration_helper_file, 'w') as f:
            line_number = 1
            for translation in all_translations:
                while line_number < translation.translation.id:
                    f.write('\n')
                    line_number += 1
                f.write('pgettext("{0} {1}", {2!r})\n'.format(
                    translation.configuration, translation.keyword,
                    translation.text.replace('\r', '').replace('%', '%%')
                ))
                line_number += 1

        self.call_parent_makemessages(*args, **options)

        # Remove temporary file.
        os.unlink(configuration_helper_file)

        do_upload_to_transifex = input('Do you want to push the new '
                                       'translations to transifex? (y/n)')
        if do_upload_to_transifex == 'y':
            subprocess.call('tx push -s -t', shell=True)

    def call_parent_makemessages(self, *args, **options):
        # Create the .po files.
        print('Writing po files.')
        options['ignore_patterns'].extend(['node_modules/*',
                                           'bower_components/*'])
        super(Command, self).handle(*args, **options)

    def only_on_develop(self):
        """
        This command must be executed on the 'develop' branch only. This should
        help to developers about 'string freezes'.
        """
        git_branch = subprocess.check_output(
            ['git', 'symbolic-ref', '--short', '-q', 'HEAD'],
            stderr=subprocess.STDOUT
        )
        if git_branch != b'develop\n':
            raise Exception('This command can only be exectured on the '
                            '"develop" branch. See the docs for more info.')
