"""
Helper script to extract the names of all Questionnaires.
"""

from django.core.management.base import BaseCommand

from apps.questionnaire.models import Questionnaire


class Command(BaseCommand):

    def handle(self, **options):

        for questionnaire in Questionnaire.objects.all():

            name_dict = questionnaire.configuration_object.get_questionnaire_name(
                questionnaire.data)

            print("\nQuestionnaire [ID: {}, code: {}, status: {}]".format(
                        questionnaire.id, questionnaire.code,
                        questionnaire.get_status_display()))
            for locale, name in name_dict.items():
                print("[{}] {}".format(locale, name))
