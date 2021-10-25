from django.apps import AppConfig


class QuestionnaireConfig(AppConfig):
    name = 'apps.questionnaire'
    verbose_name = "Questionnaire"

    def ready(self):
        from . import receivers  # noqa
        from . import lookups  # noqa
