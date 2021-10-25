from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings
from django.utils.translation import activate
from django.test import override_settings
from model_mommy import mommy
from apps.qcat.tests import TestCase

from apps.notifications.models import ActionContextQuerySet, Log, StatusUpdate, \
    ReadLog, ContentUpdate, MemberUpdate, InformationUpdate
from apps.questionnaire.models import Questionnaire, QuestionnaireMembership


class ActionContextTest(TestCase):

    def make_user(*permissions, **attributes):
        """
        Helper for user creation, as the method 'get_all_permissions' is crucial,
        but creating groups and permissions is too much overhead.
        """
        user = mommy.make(
            _model=get_user_model(),
            **attributes,
        )
        user.get_all_permissions = lambda: permissions
        return user

    def setUp(self):
        self.qs = ActionContextQuerySet()

        change_permissions = 'questionnaire.change_questionnaire'
        review_permissions = 'questionnaire.review_questionnaire'
        publish_permissions = 'questionnaire.publish_questionnaire'

        # Users with all relevant roles
        self.admin = self.make_user(change_permissions, review_permissions, publish_permissions)
        self.catalyst = self.make_user()
        self.subscriber = self.make_user()
        self.reviewer = self.make_user(change_permissions)
        self.reviewer = self.make_user(review_permissions)
        self.publisher = self.make_user(publish_permissions)

        self.questionnaire = mommy.make(
            _model=Questionnaire,
            status=settings.QUESTIONNAIRE_SUBMITTED
        )

        # Notification for a submitted questionnaire
        self.catalyst_change = mommy.make(
            _model=Log,
            action=settings.NOTIFICATIONS_CHANGE_STATUS,
            catalyst=self.catalyst,
            questionnaire=self.questionnaire
        )
        self.catalyst_change.subscribers.add(self.subscriber)
        mommy.make(
            _model=StatusUpdate,
            log=self.catalyst_change,
            status=settings.QUESTIONNAIRE_SUBMITTED
        )

        # Notification the should not be listed
        self.catalyst_edit = mommy.make(
            _model=Log,
            action=settings.NOTIFICATIONS_EDIT_CONTENT,
            catalyst=self.catalyst,
            questionnaire=self.questionnaire
        )

        self.admin_read_log = mommy.make(
            _model=ReadLog,
            user=self.admin,
            log=self.catalyst_change,
            is_read=True
        )

    # assertQuerysetEqual uses the models 'repr' method to check its 'sameness'.
    # However, this seems not stable, so we use the models id.
    transform = lambda self, x: x.id

    @override_settings(NOTIFICATIONS_CHANGE_STATUS='baz')
    @override_settings(NOTIFICATIONS_QUESTIONNAIRE_STATUS_PERMISSIONS={'foo': 'bar'})
    @patch.object(QuestionnaireMembership, 'objects')
    def test_get_questionnaires_for_permissions(self, mock_membership):
        mock_membership.return_value = []
        user = MagicMock(get_all_permissions=lambda: ['foo'])
        permissions = self.qs.get_questionnaires_for_permissions(user=user)
        # asserting strings is a workaround. tried assertListEqual and
        # assertQuerysetEqual, but they raise errors for unknown reasons.
        self.assertEqual(
            permissions[0].__str__(),
            Q(statusupdate__status='bar', action='baz').__str__()
        )

    @override_settings(NOTIFICATIONS_QUESTIONNAIRE_STATUS_PERMISSIONS={'foo': 'bar'})
    @patch.object(QuestionnaireMembership, 'objects')
    def test_get_questionnaires_without_permissions(self, mock_membership):
        user = MagicMock(get_all_permissions=lambda: ['bar'])
        mock_membership.return_value = []
        permissions = self.qs.get_questionnaires_for_permissions(user=user)
        self.assertEqual(permissions, [])

    def test_permissions_questionnaire_membership(self):
        user = mommy.make(get_user_model())
        mommy.make(
            _model=QuestionnaireMembership,
            questionnaire=self.questionnaire,
            user=user,
            role=settings.QUESTIONNAIRE_REVIEWER
        )
        self.assertEqual(
            Log.actions.user_pending_list(user).count(),
            1
        )

    def test_user_log_list_catalyst(self):
        self.assertQuerysetEqual(
            Log.actions.user_log_list(self.catalyst),
            [self.catalyst_change.id],
            transform=self.transform
        )

    def test_user_log_list_subscriber(self):
        self.assertQuerysetEqual(
            Log.actions.user_log_list(self.subscriber),
            [self.catalyst_change.id],
            transform=self.transform
        )

    def test_user_log_list_admin_permissions(self):
        self.assertQuerysetEqual(
            Log.actions.user_log_list(self.admin),
            [self.catalyst_change.id],
            transform=self.transform
        )

    def test_user_log_list_reviewer_permissions(self):
        self.assertQuerysetEqual(
            Log.actions.user_log_list(self.reviewer),
            [self.catalyst_change.id],
            transform=self.transform
        )

    def test_user_log_list_publisher_permissions(self):
        self.assertFalse(
            Log.actions.user_log_list(self.publisher).exists()
        )

    def test_list_includes_edit_for_compiler(self):
        mommy.make(
            _model=QuestionnaireMembership,
            questionnaire=self.questionnaire,
            user=self.catalyst,
            role=settings.QUESTIONNAIRE_COMPILER
        )
        self.assertTrue(
            self.catalyst_edit in Log.actions.user_log_list(self.catalyst)
        )

    def test_user_pending_list_reviewer_has_log(self):
        self.assertQuerysetEqual(
            Log.actions.user_pending_list(self.reviewer),
            [self.catalyst_change.id],
            transform=self.transform
        )

    def test_user_pending_list_admin_has_no_logs(self):
        # admin has read the notification
        self.assertFalse(
            Log.actions.user_pending_list(self.admin).exists()
        )

    def test_user_pending_list_publisher_has_no_logs(self):
        self.assertFalse(
            Log.actions.user_pending_list(self.publisher).exists()
        )

    def test_user_log_count(self):
        # Test count for all unread questionnaires
        catalyst_change_old = mommy.make(
            _model=Log,
            action=settings.NOTIFICATIONS_CHANGE_STATUS,
            catalyst=self.catalyst,
            questionnaire=self.questionnaire
        )
        mommy.make(
            _model=StatusUpdate,
            log=catalyst_change_old,
            status=settings.QUESTIONNAIRE_SUBMITTED
        )

        self.assertQuerysetEqual(
            Log.actions.user_log_list(self.reviewer),
            [catalyst_change_old.id, self.catalyst_change.id],
            transform=self.transform
        )

        self.assertEqual(
            Log.actions.user_log_count(self.reviewer),
            2
        )

    def test_only_unread_logs(self):
        self.assertQuerysetEqual(
            Log.actions.only_unread_logs(self.catalyst),
            [self.catalyst_edit.id, self.catalyst_change.id],
            transform=self.transform
        )

    def test_only_unread_logs_is_read(self):
        mommy.make(
            _model=ReadLog,
            is_read=True,
            user=self.catalyst,
            log=self.catalyst_edit
        )
        self.assertQuerysetEqual(
            Log.actions.only_unread_logs(self.catalyst),
            [self.catalyst_change.id],
            transform=self.transform
        )

    def test_only_unread_logs_is_not_read(self):
        mommy.make(
            _model=ReadLog,
            is_read=False,
            user=self.catalyst,
            log=self.catalyst_edit
        )
        self.assertQuerysetEqual(
            Log.actions.only_unread_logs(self.catalyst),
            [self.catalyst_edit.id, self.catalyst_change.id],
            transform=self.transform
        )

    def test_user_log_roles(self):
        # subscriber and catalyst should see the log 'catalyst_change'
        roles = {'subscriber': 1, 'catalyst': 1, 'publisher': 0}
        for role, logs in roles.items():
            self.assertEqual(
                Log.actions.user_log_count(getattr(self, role)), logs
            )

    def test_read_logs_admin(self):
        self.assertQuerysetEqual(
            Log.actions.read_logs(user=self.admin),
            [self.admin_read_log.id],
            transform=self.transform
        )

    def test_read_logs_subscriber(self):
        self.assertFalse(
            Log.actions.read_logs(self.catalyst).exists()
        )

    def test_read_id_list(self):
        self.assertListEqual(
            list(Log.actions.read_id_list(self.admin)),
            [self.catalyst_change.id]
        )

    @patch.object(ActionContextQuerySet, 'delete_all_read_logs')
    def test_mark_all_read_deletes_all(self, mock_delete):
        Log.actions.mark_all_read(user=self.subscriber)
        mock_delete.assert_called_once()

    def test_mark_all_read(self):
        Log.actions.mark_all_read(user=self.catalyst)
        self.assertTrue(
            ReadLog.objects.filter(user=self.catalyst, is_read=True).exists()
        )

    def test_delete_all_read_logs(self):
        mommy.make(_model=ReadLog, user=self.subscriber)
        Log.actions.delete_all_read_logs(user=self.subscriber)
        self.assertFalse(
            ReadLog.objects.filter(user=self.subscriber)
        )


class LogTest(TestCase):

    def setUp(self):
        # For some reason other tests activate other locales
        activate('en')
        self.catalyst = mommy.make(
            _model=get_user_model()
        )
        self.status_log = mommy.make(
            _model=Log,
            action=settings.NOTIFICATIONS_CHANGE_STATUS,
            catalyst=self.catalyst
        )
        mommy.make(
            _model=StatusUpdate,
            log=self.status_log
        )
        self.content_log = mommy.make(
            _model=Log,
            action=settings.NOTIFICATIONS_EDIT_CONTENT
        )
        mommy.make(
            _model=ContentUpdate,
            log=self.content_log
        )
        self.member_log = mommy.make(
            _model=Log,
            action=settings.NOTIFICATIONS_ADD_MEMBER
        )
        mommy.make(
            _model=MemberUpdate,
            log=self.member_log
        )
        self.information_log = mommy.make(
            _model=Log,
            action=settings.NOTIFICATIONS_FINISH_EDITING
        )
        mommy.make(
            _model=InformationUpdate,
            log=self.information_log
        )

    def strip(self, input):
        return input.replace('\n', ' ').replace('  ', '')

    def test_is_content_update(self):
        self.assertTrue(self.content_log.is_content_update)

    def test_is_not_content_update(self):
        self.assertFalse(self.status_log.is_content_update)

    @patch('apps.notifications.models.render_to_string')
    @patch.object(Questionnaire, 'get_name')
    @override_settings(BASE_URL='foo')
    def test_get_notification_html(self, mock_get_name, render_to_string):
        self.status_log.get_notification_html(self.catalyst)
        render_to_string.assert_called_with(
            template_name='notifications/notification/{}.html'.format(
                settings.NOTIFICATIONS_CHANGE_STATUS
            ),
            context={
                'log': self.status_log, 'user': self.catalyst, 'base_url': 'foo'
            }
        )

    @patch.object(Questionnaire, 'get_name')
    def test_mail_data_submitted(self, mock_questionnaire_name):
        # Mail data when submitting a draft questionnaire.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.status_log.questionnaire.status = settings.QUESTIONNAIRE_SUBMITTED
        context, subject = self.status_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: This practice has been submitted'
        content = self.strip(context['content'])
        assert 'has been submitted' in content
        assert self.status_log.statusupdate.message in content
        assert self.status_log.get_questionnaire_name_mail() in content

    @patch.object(Questionnaire, 'get_name')
    def test_mail_data_reviewed(self, mock_questionnaire_name):
        # Mail data when reviewing a submitted questionnaire.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.status_log.questionnaire.status = settings.QUESTIONNAIRE_REVIEWED
        context, subject = self.status_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: This practice has been approved and is awaiting final review before it can be published'
        content = self.strip(context['content'])
        assert 'has been approved by the reviewer' in content
        assert self.status_log.statusupdate.message in content

    @patch.object(Questionnaire, 'get_name')
    def test_mail_data_published(self, mock_questionnaire_name):
        # Mail data when reviewing a submitted questionnaire.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.status_log.questionnaire.status = settings.QUESTIONNAIRE_PUBLIC
        context, subject = self.status_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: Congratulations, this practice has been published!'
        content = self.strip(context['content'])
        assert 'has been published' in content
        assert self.status_log.statusupdate.message in content

    @patch.object(Questionnaire, 'get_name')
    def test_mail_data_deleted(self, mock_questionnaire_name):
        # Mail data when deleting a questionnaire.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.status_log.questionnaire.status = settings.QUESTIONNAIRE_PUBLIC
        self.status_log.action = settings.NOTIFICATIONS_DELETE
        context, subject = self.status_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: This practice has been deleted'
        assert 'has been deleted' in context['content']

    @patch.object(Questionnaire, 'get_name')
    def test_mail_data_rejected_submitted(self, mock_questionnaire_name):
        # Mail data when rejecting a *submitted* questionnaire.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.status_log.statusupdate.is_rejected = True
        self.status_log.statusupdate.previous_status = settings.QUESTIONNAIRE_SUBMITTED
        self.status_log.questionnaire.status = settings.QUESTIONNAIRE_DRAFT
        context, subject = self.status_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: This practice has been rejected and needs revision'
        content = self.strip(context['content'])
        assert 'has been rejected' in content
        assert 'If you are a reviewer' not in content
        assert self.status_log.statusupdate.message in content

    @patch.object(Questionnaire, 'get_name')
    def test_mail_data_rejected_reviewed(self, mock_questionnaire_name):
        # Mail data when rejecting a *reviewed* questionnaire.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.status_log.statusupdate.is_rejected = True
        self.status_log.statusupdate.previous_status = settings.QUESTIONNAIRE_REVIEWED
        self.status_log.questionnaire.status = settings.QUESTIONNAIRE_DRAFT
        context, subject = self.status_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: This practice has been rejected and needs revision'
        content = self.strip(context['content'])
        assert 'has been rejected' in content
        assert 'If you are a reviewer' in content
        assert self.status_log.statusupdate.message in content

    @patch.object(Questionnaire, 'get_name')
    def test_mail_editor_added(self, mock_questionnaire_name):
        # Mail data when adding a new editor.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.member_log.memberupdate.role = 'editor'
        self.member_log.action = settings.NOTIFICATIONS_ADD_MEMBER
        context, subject = self.member_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: You are an editor'
        content = self.strip(context['content'])
        assert 'You have been added as an editor of' in content
        assert 'As an editor' in content

    @patch.object(Questionnaire, 'get_name')
    def test_mail_editor_removed(self, mock_questionnaire_name):
        # Mail data when removing an editor.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.member_log.memberupdate.role = 'editor'
        self.member_log.action = settings.NOTIFICATIONS_REMOVE_MEMBER
        context, subject = self.member_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: You have been removed as an editor'
        assert 'You have been removed as an editor of' in self.strip(context['content'])

    @patch.object(Questionnaire, 'get_name')
    def test_mail_reviewer_added(self, mock_questionnaire_name):
        # Mail data when adding a new reviewer.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.member_log.memberupdate.role = 'reviewer'
        self.member_log.action = settings.NOTIFICATIONS_ADD_MEMBER
        context, subject = self.member_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: You are a reviewer'
        content = self.strip(context['content'])
        assert 'You have been added as a reviewer of' in content
        assert 'Please review the SLM practice' in content

    @patch.object(Questionnaire, 'get_name')
    def test_mail_reviewer_removed(self, mock_questionnaire_name):
        # Mail data when removing a reviewer.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.member_log.memberupdate.role = 'reviewer'
        self.member_log.action = settings.NOTIFICATIONS_REMOVE_MEMBER
        context, subject = self.member_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: You have been removed as a reviewer'
        assert 'You have been removed as a reviewer of' in self.strip(context['content'])

    @patch.object(Questionnaire, 'get_name')
    def test_mail_publisher_added(self, mock_questionnaire_name):
        # Mail data when adding a new publisher.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.member_log.memberupdate.role = 'publisher'
        self.member_log.action = settings.NOTIFICATIONS_ADD_MEMBER
        context, subject = self.member_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: You are a publisher'
        content = self.strip(context['content'])
        assert 'You have been added as a publisher of' in content
        assert 'The SLM practice has been reviewed and approved' in content

    @patch.object(Questionnaire, 'get_name')
    def test_mail_publisher_removed(self, mock_questionnaire_name):
        # Mail data when removing a publisher.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.member_log.memberupdate.role = 'publisher'
        self.member_log.action = settings.NOTIFICATIONS_REMOVE_MEMBER
        context, subject = self.member_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: You have been removed as a publisher'
        assert 'You have been removed as a publisher of' in self.strip(context['content'])

    @patch.object(Questionnaire, 'get_name')
    def test_mail_compiler_added(self, mock_questionnaire_name):
        # Mail data when adding a new compiler (replacing the old one).
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.member_log.memberupdate.role = 'compiler'
        self.member_log.action = settings.NOTIFICATIONS_ADD_MEMBER
        self.member_log.questionnaire.add_user(self.catalyst, 'compiler')
        context, subject = self.member_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: You are a compiler'
        content = self.strip(context['content'])
        assert 'You have been added as a compiler of' in content
        assert 'As a compiler' in content
        assert 'compiled by' not in content

    @patch.object(Questionnaire, 'get_name')
    def test_mail_compiler_removed(self, mock_questionnaire_name):
        # Mail data when removing a publisher.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.member_log.memberupdate.role = 'compiler'
        self.member_log.action = settings.NOTIFICATIONS_REMOVE_MEMBER
        self.member_log.questionnaire.add_user(self.catalyst, 'compiler')
        context, subject = self.member_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: You have been removed as a compiler'
        content = self.strip(context['content'])
        assert 'You have been removed as a compiler of' in content
        assert 'compiled by' not in content

    @patch.object(Questionnaire, 'get_name')
    def test_mail_edited(self, mock_questionnaire_name):
        # Mail data when an editor has finished editing the questionnaire.
        mock_questionnaire_name.return_value = 'Questionnaire X'
        self.information_log.action = settings.NOTIFICATIONS_FINISH_EDITING
        context, subject = self.information_log.get_mail_data(recipient=self.catalyst)
        assert subject == '[WOCAT] Questionnaire X: This practice has been edited'
        content = self.strip(context['content'])
        assert 'has been edited' in content
        assert self.information_log.informationupdate.info in content

    @patch.object(Log, 'get_affected')
    @patch.object(Log, 'get_reviewers')
    def test_recipients_no_duplicates(self, mock_reviewers, mock_affected):
        mock_affected.return_value = [self.catalyst]
        mock_reviewers.return_value = [self.catalyst, mommy.make(get_user_model())]
        log = self.get_review_log()
        self.assertEqual(
            set([user.id for user in mock_reviewers.return_value]),
            set([user.id for user in list(log.recipients)]),
        )

    def get_review_log(self):
        """
        Build a log with valid properties to get reviewers
        """
        questionnaire = mommy.make(
            _model=Questionnaire,
            status=settings.QUESTIONNAIRE_WORKFLOW_STEPS[0]
        )
        log = mommy.make(
            _model=Log,
            action=settings.NOTIFICATIONS_CHANGE_STATUS,
            questionnaire=questionnaire
        )
        mommy.make(
            _model=StatusUpdate,
            log=log,
            status=settings.QUESTIONNAIRE_WORKFLOW_STEPS[0]
        )
        return log

    @patch.object(Questionnaire, 'get_wocat_mailbox_user')
    def test_get_reviewers(self, mock_get_wocat_user):
        log = self.get_review_log()
        log.get_reviewers()
        mock_get_wocat_user.assert_called_once()

    @patch.object(Questionnaire, 'get_users_for_next_publish_step')
    def test_get_reviewers_change_log(self, mock_get_users):
        log = self.get_review_log()
        log.action = ''
        log.get_reviewers()
        self.assertFalse(mock_get_users.called)

    @patch.object(Questionnaire, 'get_users_for_next_publish_step')
    def test_get_reviewers_no_update(self, mock_get_users):
        log = self.get_review_log()
        log.questionnaire.status = ''
        log.get_reviewers()
        self.assertFalse(mock_get_users.called)

    @patch.object(Questionnaire, 'get_users_for_next_publish_step')
    def test_get_reviewers_workflow_status(self, mock_get_users):
        log = self.get_review_log()
        log.statusupdate.status = ''
        log.get_reviewers()
        self.assertFalse(mock_get_users.called)

    def test_get_affected(self):
        self.assertFalse(self.content_log.get_affected())
        self.assertFalse(self.status_log.get_affected())
        self.assertTrue(self.member_log.get_affected())


class MailPreferencesTest(TestCase):

    def setUp(self):
        self.user = mommy.make(_model=get_user_model())
        self.obj = self.user.mailpreferences

    def test_get_defaults_staff(self):
        self.user.is_superuser = True
        self.assertEqual(
            (settings.NOTIFICATIONS_TODO_MAILS, str(settings.NOTIFICATIONS_CHANGE_STATUS)),
            self.obj.get_defaults()
        )

    def test_get_defaults(self):
        self.user.is_superuser = False
        self.assertEqual(
            (settings.NOTIFICATIONS_ALL_MAILS,
             ','.join([str(pref) for pref in settings.NOTIFICATIONS_EMAIL_PREFERENCES])),
            self.obj.get_defaults()
        )

    def test_not_allowed_send_mails_settings(self):
        with override_settings(DO_SEND_EMAILS=False):
            self.assertFalse(self.obj.is_allowed_send_mails)

    def test_is_allowed_send_mails_settings(self):
        self.obj.subscription = settings.NOTIFICATIONS_ALL_MAILS
        with override_settings(DO_SEND_EMAILS=True, DO_SEND_STAFF_ONLY=False):
            self.assertTrue(self.obj.is_allowed_send_mails)

    def test_is_allowed_send_mails_staff_settings_is_no_staff(self):
        user = mommy.make(_model=get_user_model(), is_superuser=False)
        user.mailpreferences.subscription = 'all'
        with override_settings(DO_SEND_STAFF_ONLY=True, DO_SEND_EMAILS=True):
            self.assertFalse(user.mailpreferences.is_allowed_send_mails)

    def test_is_allowed_send_mails_staff_settings_is_staff(self):
        superuser = mommy.make(_model=get_user_model(), is_superuser=True)
        superuser.mailpreferences.subscription = 'all'
        with override_settings(DO_SEND_STAFF_ONLY=True, DO_SEND_EMAILS=True):
            self.assertTrue(superuser.mailpreferences.is_allowed_send_mails)

    def test_not_allowed_send_mails_subscription(self):
        self.obj.subscription = settings.NOTIFICATIONS_NO_MAILS
        with override_settings(DO_SEND_EMAILS=True):
            self.assertFalse(self.obj.is_allowed_send_mails)

    def test_is_wanted_action(self):
        self.obj.wanted_actions = 'coffee,chocolate'
        self.assertTrue(self.obj.is_wanted_action('coffee'))
        self.assertFalse(self.obj.is_wanted_action('bread'))

    @patch.object(ActionContextQuerySet, 'user_pending_list')
    def test_is_todo_log(self, mock_pending_list):
        self.obj.subscription = settings.NOTIFICATIONS_TODO_MAILS
        log = MagicMock()
        mock_pending_list.return_value = [log]
        self.assertTrue(self.obj.is_todo_log(log))
        mock_pending_list.return_value = [MagicMock()]
        self.assertFalse(self.obj.is_todo_log(log))

    def test_is_todo_log_other_prefs(self):
        self.obj.subscription = settings.NOTIFICATIONS_ALL_MAILS
        self.assertTrue(self.obj.is_todo_log(MagicMock()))
