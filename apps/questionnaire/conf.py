from django.conf import settings  # noqa
from appconf import AppConf
from django.utils.translation import ugettext as _


class QuestionnaireConf(AppConf):
    """
    Verbose names for statuses and roles
    """
    # Status list
    DRAFT = 1
    SUBMITTED = 2
    REVIEWED = 3
    PUBLIC = 4
    REJECTED = 5
    INACTIVE = 6
    # Roles
    COMPILER = 'compiler'
    EDITOR = 'editor'
    REVIEWER = 'reviewer'
    PUBLISHER = 'publisher'
    SECRETARIAT = 'secretariat'
    LANDUSER = 'landuser'
    RESOURCEPERSON = 'resourceperson'
    FLAGGER = 'flagger'

    # Mapping of authorized roles to advance questionnaire to next step.
    PUBLICATION_ROLES = {
        DRAFT: COMPILER,
        SUBMITTED: REVIEWER,
        REVIEWED: PUBLISHER
    }
    WORKFLOW_STEPS = [SUBMITTED, REVIEWED]

    FLAG_UNCCD = 'unccd_bp'

    METADATA_KEYS = [
        'created',
        'updated',
        'compilers',
        'editors',
        'reviewers',
        'code',
        'configuration',
        'translations',
        'status',
        'flags',
        'original_locale',
    ]

    # A list of questiongroups which can be filtered for every configuration.
    # Those configurations that do not have these questiongroups will receive a
    # mapping for them anyways (to prevent ES crashes).
    GLOBAL_QUESTIONGROUPS = [
        'qg_name',
        'qg_location',
        'qg_funding_project',
        'qg_funding_institution',
    ]

    # A list of questiongroups and questions which can be filtered in the GUI
    # for every configuration.
    # (questiongroup_keyword, question_keyword, filter_keyword [as used in the
    # GUI])
    GLOBAL_FILTERS = [
        ('qg_location', 'country', 'countries'),
    ]

    GLOBAL_FILTER_PATHS = [
        ('qg_location', 'country'),
        ('qg_funding_project', 'funding_project'),
        ('qg_funding_institution', 'funding_institution'),
    ]

    SLM_DATA_TYPES = (
        ('wocat', _('ALL SLM Data')),
        ('technologies', _('SLM Technologies')),
        ('approaches', _('SLM Approaches')),
        ('unccd', _('UNCCD PRAIS Practices')),
    )

    LOCK_TIME = 10  # Number of minutes that questionnaires are locked.
