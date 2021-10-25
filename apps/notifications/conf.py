# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.conf import settings  # noqa

from appconf import AppConf


class NotificationsConf(AppConf):
    CREATE = 1
    DELETE = 2
    CHANGE_STATUS = 3
    ADD_MEMBER = 4
    REMOVE_MEMBER = 5
    EDIT_CONTENT = 6
    FINISH_EDITING = 7

    ACTIONS = (
        (CREATE, _('created questionnaire')),
        (DELETE, _('deleted questionnaire')),
        (CHANGE_STATUS, _('changed status')),
        (ADD_MEMBER, _('invited member')),
        (REMOVE_MEMBER, _('removed member')),
        (EDIT_CONTENT, _('edited content')),
        (FINISH_EDITING, _('editor finished'))
    )

    ACTION_ICON = {
        CREATE: 'icon-plus',
        DELETE: 'icon-minus',
        'status-reject': 'icon-rewind',
        'status-approve': 'icon-forward',
        ADD_MEMBER: 'icon-member-add',
        REMOVE_MEMBER: 'icon-member-remove',
        EDIT_CONTENT: 'icon-pencil',
        FINISH_EDITING: 'icon-edit-approve',
    }

    MAIL_SUBJECTS = {
        'edited': _('This practice has been edited'),
        'submitted': _('This practice has been submitted'),
        'reviewed': _('This practice has been approved and is awaiting final review before it can be published'),
        'published': _('Congratulations, this practice has been published!'),
        'deleted': _('This practice has been deleted'),
        'rejected_submitted': _('This practice has been rejected and needs revision'),
        'rejected_reviewed': _('This practice has been rejected and needs revision'),
        'compiler_added': _('You are a compiler'),
        'compiler_removed': _('You have been removed as a compiler'),
        'editor_added': _('You are an editor'),
        'editor_removed': _('You have been removed as an editor'),
        'reviewer_added': _('You are a reviewer'),
        'reviewer_removed': _('You have been removed as a reviewer'),
        'publisher_added': _('You are a publisher'),
        'publisher_removed': _('You have been removed as a publisher'),
    }

    # Mapping of user permissions and allowed questionnaire statuses
    QUESTIONNAIRE_STATUS_PERMISSIONS = {
        'questionnaire.submit_questionnaire': settings.QUESTIONNAIRE_DRAFT,
        'questionnaire.review_questionnaire': settings.QUESTIONNAIRE_SUBMITTED,
        'questionnaire.publish_questionnaire': settings.QUESTIONNAIRE_REVIEWED
    }
    QUESTIONNAIRE_MEMBERSHIP_PERMISSIONS = {
        settings.QUESTIONNAIRE_COMPILER: [settings.QUESTIONNAIRE_DRAFT],
        settings.QUESTIONNAIRE_EDITOR: [],
        settings.QUESTIONNAIRE_REVIEWER: [settings.QUESTIONNAIRE_SUBMITTED],
        settings.QUESTIONNAIRE_PUBLISHER: [settings.QUESTIONNAIRE_REVIEWED],
        settings.QUESTIONNAIRE_SECRETARIAT: [settings.QUESTIONNAIRE_SUBMITTED, settings.QUESTIONNAIRE_REVIEWED],
        settings.ACCOUNTS_UNCCD_ROLE_NAME: [],
        settings.QUESTIONNAIRE_LANDUSER: [],
        settings.QUESTIONNAIRE_RESOURCEPERSON: []
    }

    # All actions that should be listed on 'my slm data' -> notifications.
    # Some actions are depending on the role (i.e. compilers see all edits).
    USER_PROFILE_ACTIONS = [
        CREATE, DELETE, CHANGE_STATUS, ADD_MEMBER, REMOVE_MEMBER, FINISH_EDITING
    ]

    # All actions that should trigger an email
    EMAIL_PREFERENCES = [
        CREATE, DELETE, CHANGE_STATUS, ADD_MEMBER, REMOVE_MEMBER, FINISH_EDITING
    ]
    # email subscriptions
    NO_MAILS = 'none'
    TODO_MAILS = 'todo'
    ALL_MAILS = 'all'

    EMAIL_SUBSCRIPTIONS = (
        (NO_MAILS, _('No emails at all')),
        (TODO_MAILS, _('Only emails that I need to work on')),
        (ALL_MAILS, _('All emails')),
    )

    TEASER_PAGINATE_BY = 5
    LIST_PAGINATE_BY = 10
    SALT = settings.BASE_DIR
