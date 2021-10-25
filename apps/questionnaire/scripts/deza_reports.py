from datetime import datetime

import collections
import operator

from django.conf import settings
from django.db.models import Q

from apps.questionnaire.models import Questionnaire


def run(*args):

    date_format = '%Y-%m-%d'

    if not len(args) == 2:
        print('\n')
        print(f'You must provide a start and end date in format {date_format}.')
        print('\n')
        print('Usage:')
        print('  python manage.py runscript deza_reports --script-args 2018-01-01 2018-06-30')
        print('\n')
        return

    try:
        start_date, end_date = [datetime.strptime(a, date_format) for a in args]
    except ValueError:
        raise Exception(f'Invalid date. Must be of format {date_format}.')

    ReportStatus(
        start_date.date(),
        end_date.date(),
        'approaches', 'technologies'
    )


class ReportStatus:

    def __init__(self, start, end, *configuration_types):
        self.report_start = start
        self.report_end = end

        for configuration_type in configuration_types:
            self.configuration_type = configuration_type

            self.published = self.get_published()
            self.unpublished = self.get_unpublished()

            self.print_all()

    def get_published(self):
        return Questionnaire.with_status.public().filter(
            updated__gte=self.report_start,
            updated__lte=self.report_end,
            code__startswith=self.configuration_type
        ).exclude(
            status__in=[
                settings.QUESTIONNAIRE_INACTIVE,
                settings.QUESTIONNAIRE_REJECTED
            ]
        )

    def get_unpublished(self):
        return Questionnaire.objects.exclude(
            Q(id__in=self.published.values_list('id', flat=True)) |
            Q(status__in=[
                settings.QUESTIONNAIRE_DRAFT,
                settings.QUESTIONNAIRE_INACTIVE,
                settings.QUESTIONNAIRE_REJECTED
            ])
        ).filter(
            created__gte=self.report_start,
            created__lte=self.report_end,
            code__startswith=self.configuration_type
        ).distinct(
            'code'
        ).order_by(
            'code'
        )

    def print_all(self):
        self.print_status()
        self.print_report(self.published, 'published')
        self.print_report(self.unpublished, 'unpublished')

    def print_status(self):
        all_sum = Questionnaire.with_status.not_deleted().filter(
            code__startswith=self.configuration_type,
            created__gte=self.report_start, created__lte=self.report_end
        ).exclude(
            status__in=[
                settings.QUESTIONNAIRE_DRAFT,
                settings.QUESTIONNAIRE_INACTIVE,
                settings.QUESTIONNAIRE_REJECTED
            ]
        ).count()
        self.format_output(f'{self.configuration_type}: {self.report_start} - {self.report_end}', level=1)
        print(f'total: {all_sum} cases created')

    def print_report(self, queryset, status):
        self.format_output(status, level=2)
        countries, languages = self.count_queryset(queryset)
        print(f'total: {queryset.count()} {self.configuration_type.capitalize()}')
        print(f'{len(countries.keys())} countries')
        print(f'{len(languages.keys())} languages')

        self.format_output('all countries', level=3)
        self.counter_details(countries)

        self.format_output('all languages (some cases are translated and are providing multiple languages)', level=3)
        self.counter_details(languages)
        print('\n')

    def count_queryset(self, qs):
        countries = collections.Counter()
        languages = collections.Counter()

        for qs in qs:
            selected_countries = [str(country) for country in qs.get_countries()]
            countries.update(selected_countries)

            selected_languages = [qs.get_language_display() for qs in qs.questionnairetranslation_set.all()]
            languages.update(selected_languages)

        return countries, languages

    def counter_details(self, counter):
        print(f'total: {sum(counter.values())}\n')
        for name, value in sorted(counter.items(), key=operator.itemgetter(1), reverse=True):
            print(f'{name}: {value}')

    def format_output(self, msg, level):

        if level == 1:
            print('\n')
            print('=' * len(msg))
            print(msg.capitalize())
            print('=' * len(msg))
            print('\n')

        elif level == 2:
            print('\n')
            print('-' * len(msg))
            print(msg.capitalize())
            print('-' * len(msg))
            print('\n')

        elif level == 3:
            print('\n')
            print(msg.capitalize())
            print('~' * len(msg))

        else:
            raise NotImplementedError
