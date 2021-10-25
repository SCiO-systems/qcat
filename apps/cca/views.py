from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from apps.questionnaire.views import generic_questionnaire_view_step


@login_required
def questionnaire_view_step(request, identifier, step):
    """
    View rendering the form of a single step of a new Climate Change Adaptation
    questionnaire in read-only mode.
    """
    return generic_questionnaire_view_step(
        request, identifier, step, 'cca',
        page_title=_('Climate Change Adaptation'))
