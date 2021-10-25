from apps.configuration.cache import get_configuration
from django.apps import apps
from django.conf import settings
from django.db.models import Q
from apps.questionnaire.models import Questionnaire
from apps.search.utils import check_aliases


def get_configuration_query_filter(configuration, only_current=False):
    """
    Return a Django ``Q`` object used to encapsulate SQL expressions.
    This object can be used to filter Questionnaires based on their
    configuration code.

    .. seealso::
        https://docs.djangoproject.com/en/1.7/topics/db/queries/#complex-lookups-with-q-objects

    The following rules apply:

    * By default, only questionnaires of the provided configuration are
      visible.

    * Use ``all`` to not filter Questionnaires by configurations at all.

    * For ``wocat``, additionally configuration ``unccd`` is visible (
      combined through an ``OR`` statement)

    Args:
        ``configuration`` (str): The code of the (current)
        configuration.

    Kwargs:
        ``only_current`` (bool): If ``True``, always only the current
        configuration is returned as filter. Defaults to ``False``.

    Returns:
        ``django.db.models.Q``. A filter object.
    """
    if only_current is True:
        return Q(configuration__code=configuration)

    if configuration == 'wocat':
        return Q()

    return Q(configuration__code=configuration)


def get_configuration_index_filter(configuration: str):
    """
    Return the name of the index / indices to be searched by
    Elasticsearch based on their configuration code.

    The following rules apply:

    * By default, only questionnaires of the provided configuration
      are visible.

    Args:
        ``configuration`` (str): The code of the (current)
        configuration.

    Returns:
        ``list``. A list of configuration codes (the index/indices) to
        be searched.
    """
    default_configurations = [
        'unccd_*', 'technologies_*', 'approaches_*', 'watershed_*'
    ]
    configurations = [configuration.lower()]

    is_valid_configuration = check_aliases(configurations) and configurations != ['wocat']

    is_test_running = getattr(settings, 'IS_TEST_RUN', False) is True
    if is_test_running and configuration in ['sample', 'samplemulti', 'samplemodule']:
        return configurations

    return configurations if is_valid_configuration else default_configurations


def create_new_code(questionnaire, configuration):
    """
    Create a new code for a Questionnaire based on the configuration.

    Args:
        questionnaire (Questionnaire): The Questionnaire object.
        configuration (str): The code of the configuration.

    Returns:
        str.
    """
    return '{}_{}'.format(configuration, questionnaire.id)


def get_choices_from_model(model_name, only_active=True):
    """
    Return the values of a model as choices to be used in the form.

    Args:
        model_name: (str) The name of the model inside the ``configuration`` app
        only_active: (bool) If True, a filter is set to return only instances of
          the model with "active" = True

    Returns:
        list. A list of tuples where
            [0] The ID of the model instance
            [1] The string representation of the instance
    """
    choices = []
    try:
        model = apps.get_model(
            app_label='configuration', model_name=model_name)
        if only_active is True:
            objects = model.objects.filter(active=True).all()
        else:
            objects = model.objects.all()
        for o in objects:
            choices.append((o.id, str(o)))
    except LookupError:
        pass
    return choices


def get_choices_from_questiongroups(
        questionnaire_data: dict, questiongroups: list, configuration_code: str,
        configuration_edition: str) -> list:
    """
    Return a list of valid choices based on the presence of certain
    questiongroups within a questionnaire data JSON.

    Args:
        questionnaire_data: The questionnaire data dict
        questiongroups: A list of questiongroup keywords (basically a list of
          all possible choices)
        configuration: QuestionnaireConfiguration

    Returns:
        A list of possible choices [(keyword, label)]
    """
    choices = []
    configuration = get_configuration(
        code=configuration_code, edition=configuration_edition)
    for questiongroup in questiongroups:
        if questiongroup in questionnaire_data:
            questiongroup_object = configuration.get_questiongroup_by_keyword(
                questiongroup)
            choices.append((questiongroup, questiongroup_object.label))
    return choices
