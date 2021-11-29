from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from apps.questionnaire.views import generic_questionnaire_view_step


@login_required
def unccd_data_import(request):
    """
    Call the script for the UNCCD import. This assumes there is a module
    "unccd.data_import" with a function "data_import".

    Redirects to the administration interface to display a success or
    error message.
    """
    if request.user.is_superuser is not True:
        raise PermissionDenied()

    print('$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$')
    redirect_route = 'search:admin'

    try:
        from .data_import import data_import
    except ImportError as e:
        messages.error(
            request, 'No valid import function found. Make sure there is a '
            'function "data_import" in module "unccd.data_import". The error '
            'message was: {}'.format(e))
        return redirect(redirect_route)

    success, objects = data_import()

    if success is True:
        messages.success(
            request, 'The data was parsed correctly. {} questionnaires were '
            'inserted.'.format(len(objects)))
    else:
        messages.error(
            request, 'The following error(s) occured: {}'.format(objects))

    return redirect(redirect_route)


@login_required
def questionnaire_view_step(request, identifier, step):
    """
    View rendering the form of a single step of a new UNCCD
    questionnaire in read-only mode.
    """
    return generic_questionnaire_view_step(
        request, identifier, step, 'unccd',
        page_title=_('UNCCD'))
