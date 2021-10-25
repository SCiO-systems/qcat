import contextlib
import itertools
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.core.mail.backends.locmem import EmailBackend
from django.core.management import call_command
from django.db import OperationalError
from django.test import override_settings

from model_mommy import mommy

from apps.configuration.models import Configuration
from apps.notifications.models import MailPreferences, Log
from apps.notifications.utils import StatusLog, MemberLog, ContentLog, InformationLog
from apps.qcat.tests import TestCase
from apps.questionnaire.models import Questionnaire, QuestionnaireMembership


@override_settings(DO_SEND_EMAILS=True)
class SendMailRecipientMixin(TestCase):
    """
    Helpers to create logs, mock sending with django email backend, and check
    sent mails.
    """

    fixtures = [
        'groups_permissions',
        'sample_global_key_values',
        'sample'
    ]
    # map user names to their permission-groups.
    user_groups_mapping = {
        'editor': None,
        'compiler': None,
        'reviewer': 3,
        'publisher': 4,
        'secretariat': 5
    }

    def setUp(self):
        self.create_users()

        self.questionnaire = mommy.make(
            _model=Questionnaire, status=settings.QUESTIONNAIRE_DRAFT,
            configuration=Configuration.objects.get(
                code='sample', edition='2015')
        )

        self.editors = [self.editor_none, self.editor_todo, self.editor_all]
        self.compilers = [self.compiler_none, self.compiler_todo, self.compiler_all]
        self.reviewers = [self.reviewer_none, self.reviewer_todo, self.reviewer_all]
        self.publishers = [self.publisher_none, self.publisher_todo, self.publisher_all]
        # secretariat people are not added, they have the roles reviewer and
        # publisher and are not specifcally checked for when handling
        # notifications.
        self.all = [self.editors + self.compilers + self.reviewers + self.publishers]

    def create_users(self):
        for preference in dict(settings.NOTIFICATIONS_EMAIL_SUBSCRIPTIONS).keys():
            for user, group_id in self.user_groups_mapping.items():
                username = '{user}_{preference}'.format(user=user, preference=preference)
                user_kwargs = {
                    'firstname': username, 'email': '{}@example.com'.format(username)
                }
                if group_id:
                    user_kwargs['groups'] = [Group.objects.get(id=group_id)]
                self._create_user(username, preference, **user_kwargs)

    def _create_user(self, username, preference, **user_kwargs):
        setattr(self, username, mommy.make(_model=get_user_model(), **user_kwargs))
        mail_preferences = MailPreferences.objects.get(user__firstname=username)
        mail_preferences.subscription = preference
        mail_preferences.save()

    def add_questionnairememberships(self, role: str, *users):
        for user in users:
            mommy.make(
                _model=QuestionnaireMembership,
                role=role, user=user, questionnaire=self.questionnaire
            )

    def create_log(self, klass, action: int, sender: User, **kwargs) -> Log:
        log = klass(action=action, sender=sender, questionnaire=self.questionnaire)
        log.create(**kwargs)
        return log.log

    def assert_no_unsent_logs(self, all_logs_count: int):
        """
        Ensure the expected number of logs were created, and all have been sent.
        """
        logs = Log.objects.all()
        self.assertEqual(logs.count(), all_logs_count)
        self.assertFalse(logs.filter(was_processed=False).exists())

    def assert_only_expected(self, outbox, *expected):
        for mail in expected:
            self.assertTrue(
                expr=mail in outbox,
                msg='Expected mail: {} not found in the outbox {}'.format(mail, outbox)
            )

    def filter_expected_logs(self, user: User, logs: list):
        for log in logs:
            if user in log.recipients:
                yield {
                    'log_id': str(log.id),
                    'recipient': user.email,
                    'subject': str(log.get_mail_data(user)[1])
                }

    @contextlib.contextmanager
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def send_notification_mails(self):
        """
        Provide access to all sent messages. Provided attributes should match
        the ones tested for in assert_only_expected.
        """
        outbox = []
        with patch.object(EmailBackend, 'send_messages') as mock_send:
            call_command('send_notification_mails')
            for call in mock_send.call_args_list:
                email_obj = call[0][0][0]
                message = email_obj.message()
                outbox.append({
                    'recipient': email_obj.recipients()[0],
                    'subject': message['Subject'].replace('\n', ''),
                    'log_id': message['qcat_log']
                })

            yield outbox


class SettingsMailTest(SendMailRecipientMixin):

    @override_settings(DO_SEND_STAFF_ONLY=True)
    def test_do_send_staff_only(self):
        previous_status = self.questionnaire.status
        self.questionnaire.status = settings.QUESTIONNAIRE_SUBMITTED
        self.questionnaire.save()
        # Set a staff user - only this one must receive mails.
        self.reviewer_all.is_superuser = True
        self.reviewer_all.save()
        self.questionnaire.add_user(self.reviewer_all, 'reviewer')
        logs = []
        for compiler in self.compilers:
            log = self.create_log(
                klass=StatusLog,
                action=settings.NOTIFICATIONS_CHANGE_STATUS,
                sender=compiler,
                is_rejected=False,
                message='submit',
                previous_status=previous_status
            )
            logs.append(log)

        with self.send_notification_mails() as outbox:
            self.assertEqual(len(outbox), 3)
            expected = list(self.filter_expected_logs(self.reviewer_all, logs))
            self.assert_only_expected(outbox, *expected)
        self.assert_no_unsent_logs(3)

    @override_settings(DO_SEND_STAFF_ONLY=True)
    def test_do_send_all(self):
        previous_status = self.questionnaire.status
        self.questionnaire.status = settings.QUESTIONNAIRE_SUBMITTED
        self.questionnaire.save()
        # no staff user set - send no mails!
        logs = []
        for compiler in self.compilers:
            log = self.create_log(
                klass=StatusLog,
                action=settings.NOTIFICATIONS_CHANGE_STATUS,
                sender=compiler,
                is_rejected=False,
                message='submit',
                previous_status=previous_status
            )
            logs.append(log)

        with self.send_notification_mails() as outbox:
            self.assertEqual(len(outbox), 0)
        self.assert_no_unsent_logs(3)

    @override_settings(DO_SEND_STAFF_ONLY=False)
    def test_wanted_only_all_wanted(self):
        logs = []
        self.compiler_all.mailpreferences.wanted_actions = []
        self.compiler_all.mailpreferences.save()
        for reviewer in self.reviewers:
            log = self.create_log(
                klass=StatusLog,
                action=settings.NOTIFICATIONS_CHANGE_STATUS,
                sender=reviewer,
                is_rejected=True,
                message='submit',
                previous_status=settings.QUESTIONNAIRE_SUBMITTED
            )
            self.add_questionnairememberships('compiler', *self.compilers)
            logs.append(log)

        with self.send_notification_mails() as outbox:
            expected = [{
                'log_id': str(logs[2].id),
                'recipient': self.compiler_todo.email,
                'subject': str(logs[2].get_mail_data(self.compiler_todo)[1])
            }]
            self.assert_only_expected(outbox, *expected)
        self.assert_no_unsent_logs(3)


@override_settings(DO_SEND_STAFF_ONLY=False)
class PublicationWorkflowMailTest(SendMailRecipientMixin):
    """
    Tests for the typical publication workflow of a questionnaire.
    """
    def test_questionnaire_created(self):
        for compiler in self.compilers:
            self.create_log(
                klass=StatusLog,
                action=settings.NOTIFICATIONS_CREATE,
                sender=compiler,
                is_rejected=False,
                message='created',
                previous_status=settings.QUESTIONNAIRE_SUBMITTED
            )

        with self.send_notification_mails() as outbox:
            self.assertEqual(outbox, [])
        self.assert_no_unsent_logs(all_logs_count=3)

    def test_editor_added(self):
        logs = []
        for compiler in self.compilers:
            for editor in self.editors:
                log = self.create_log(
                    klass=MemberLog,
                    action=settings.NOTIFICATIONS_ADD_MEMBER,
                    sender=compiler,
                    affected=editor,
                    role='editor'
                )
                logs.append(log)

        with self.send_notification_mails() as outbox:
            self.assertEqual(len(outbox), 3)
            expected = self.filter_expected_logs(self.editor_all, logs)
            self.assert_only_expected(outbox, *expected)
        self.assert_no_unsent_logs(all_logs_count=9)

    def test_editor_edited(self):
        for editor in self.editors:
            self.create_log(
                klass=ContentLog,
                action=settings.NOTIFICATIONS_EDIT_CONTENT,
                sender=editor
            )

        self.add_questionnairememberships('compiler', *self.compilers)
        with self.send_notification_mails() as outbox:
            self.assertEqual(outbox, [])
        self.assert_no_unsent_logs(all_logs_count=3)

    def test_editor_finished(self):
        logs = []
        for editor in self.editors:
            for compiler in self.compilers:
                information_log = InformationLog(
                    action=settings.NOTIFICATIONS_FINISH_EDITING,
                    sender=editor,
                    questionnaire=self.questionnaire,
                    receiver=compiler
                )
                information_log.create('finished')
                logs.append(information_log.log)

        self.add_questionnairememberships('compiler', *self.compilers)
        with self.send_notification_mails() as outbox:
            expected = self.filter_expected_logs(self.compiler_all, logs)
            self.assert_only_expected(outbox, *expected)
        self.assert_no_unsent_logs(all_logs_count=9)

    # def test_questionnaire_submitted(self):
        """
    #     As 'todo' checks for questionnaire-uniqueness, only one 'todo' log is
    #     sent.
        """
    #     previous_status = self.questionnaire.status
    #     self.questionnaire.status = settings.QUESTIONNAIRE_SUBMITTED
    #     self.questionnaire.save()
    #     logs = []
    #     for compiler in self.compilers:
    #         log = self.create_log(
    #             klass=StatusLog,
    #             action=settings.NOTIFICATIONS_CHANGE_STATUS,
    #             sender=compiler,
    #             is_rejected=False,
    #             message='submit',
    #             previous_status=previous_status
    #         )
    #         logs.append(log)
    #
    #     with self.send_notification_mails() as outbox:
    #         self.assertEqual(len(outbox), 4)
    #         expected = list(self.filter_expected_logs(self.reviewer_all, logs))
    #         expected.append({
    #             'log_id': str(logs[2].id),
    #             'recipient': self.reviewer_todo.email,
    #             'subject': str(logs[2].get_mail_data(self.reviewer_todo)[1])
    #         })
    #         self.assert_only_expected(outbox, *expected)
    #     self.assert_no_unsent_logs(3)

    def test_questionnaire_review_rejected(self):
        logs = []
        for reviewer in self.reviewers:
            log = self.create_log(
                klass=StatusLog,
                action=settings.NOTIFICATIONS_CHANGE_STATUS,
                sender=reviewer,
                is_rejected=True,
                message='submit',
                previous_status=settings.QUESTIONNAIRE_SUBMITTED
            )
            self.add_questionnairememberships('compiler', *self.compilers)
            logs.append(log)

        with self.send_notification_mails() as outbox:
            expected = self.filter_expected_logs(self.compiler_all, logs)
            self.assert_only_expected(outbox, *expected)
        self.assert_no_unsent_logs(3)

    # def test_questionnaire_review_accepted(self):
    #     previous_status = self.questionnaire.status
    #     self.questionnaire.status = settings.QUESTIONNAIRE_REVIEWED
    #     self.questionnaire.save()
    #     self.add_questionnairememberships('compiler', *self.compilers)
    #     self.add_questionnairememberships('editor', *self.editors)
    #     logs = []
    #     for reviewer in self.reviewers:
    #         log = self.create_log(
    #             klass=StatusLog,
    #             action=settings.NOTIFICATIONS_CHANGE_STATUS,
    #             sender=reviewer,
    #             is_rejected=False,
    #             message='review accepted',
    #             previous_status=previous_status
    #         )
    #         logs.append(log)
    #
    #     with self.send_notification_mails() as outbox:
    #         expected = itertools.chain(
    #             self.filter_expected_logs(self.compiler_all, logs),
    #             self.filter_expected_logs(self.editor_all, logs),
    #             self.filter_expected_logs(self.publisher_all, logs),
    #             [{
    #                 'log_id': str(logs[2].id),
    #                 'recipient': self.publisher_todo.email,
    #                 'subject': str(logs[2].get_mail_data(self.publisher_todo)[1])
    #             }]
    #         )
    #         self.assertEqual(len(outbox), 10)
    #         self.assert_only_expected(outbox, *expected)
    #     self.assert_no_unsent_logs(3)
    #
    # def test_questionnaire_publication_rejected(self):
    #     previous_status = self.questionnaire.status
    #     self.questionnaire.status = settings.QUESTIONNAIRE_SUBMITTED
    #     self.questionnaire.save()
    #     self.add_questionnairememberships('compiler', *self.compilers)
    #     self.add_questionnairememberships('editor', *self.editors)
    #     logs = []
    #     for reviewer in self.reviewers:
    #         log = self.create_log(
    #             klass=StatusLog,
    #             action=settings.NOTIFICATIONS_CHANGE_STATUS,
    #             sender=reviewer,
    #             is_rejected=True,
    #             message='review rejected',
    #             previous_status=previous_status
    #         )
    #         logs.append(log)
    #
    #     with self.send_notification_mails() as outbox:
    #         expected = itertools.chain(
    #             self.filter_expected_logs(self.compiler_all, logs),
    #             self.filter_expected_logs(self.editor_all, logs),
    #             self.filter_expected_logs(self.reviewer_all, logs),
    #             [{
    #                 'log_id': str(logs[2].id),
    #                 'recipient': self.reviewer_todo.email,
    #                 'subject': str(logs[2].get_mail_data(self.reviewer_todo)[1])
    #             }]
    #         )
    #         self.assertEqual(len(outbox), 10)
    #         self.assert_only_expected(outbox, *expected)
    #
    #     self.assert_no_unsent_logs(3)

    @patch('apps.notifications.models.render_to_string')
    def test_questionnaire_publication_accepted(self, mock_render_to_string):
        previous_status = self.questionnaire.status
        self.questionnaire.status = settings.QUESTIONNAIRE_PUBLIC
        self.questionnaire.save()
        self.add_questionnairememberships('reviewer', *self.compilers)
        self.add_questionnairememberships('compiler', *self.compilers)
        self.add_questionnairememberships('editor', *self.editors)
        logs = []
        for publisher in self.publishers:
            log = self.create_log(
                klass=StatusLog,
                action=settings.NOTIFICATIONS_CHANGE_STATUS,
                sender=publisher,
                is_rejected=False,
                message='review accepted',
                previous_status=previous_status
            )
            logs.append(log)

        with self.send_notification_mails() as outbox:
            self.assertEqual(len(outbox), 6)
            expected = itertools.chain(
                self.filter_expected_logs(self.compiler_all, logs),
                self.filter_expected_logs(self.editor_all, logs),
            )
            self.assert_only_expected(outbox, *expected)
            mock_render_to_string.mock_assert_any_calls(
                'notifications/mail/publish_addendum.html'
            )
        self.assert_no_unsent_logs(3)


@override_settings(DO_SEND_EMAILS=False)
@patch('apps.notifications.management.commands.send_notification_mails.logger')
class SendNotificationMailsTest(TestCase):

    def check_calls_contain(self, expected, log_calls):
        for i, e in enumerate(expected):
            assert e in log_calls[i][0][0]

    def test_log_empty(self, mock_logger):
        call_command('send_notification_mails')

        log_calls = mock_logger.info.call_args_list
        assert len(log_calls) == 2
        self.check_calls_contain([
            'start processing 0 logs',
            'finished processing logs',
        ], log_calls)

    def test_log_processed(self, mock_logger):
        log_1 = mommy.make(
            _model=Log,
        )
        call_command('send_notification_mails')

        log_calls = mock_logger.info.call_args_list
        assert len(log_calls) == 3
        self.check_calls_contain([
            'start processing 1 logs',
            f'sent log {log_1.id}',
            'finished processing logs',
        ], log_calls)

    @patch.object(Log, 'send_mails')
    def test_log_blocked(self, mock_send_mails, mock_logger):
        mock_send_mails.side_effect = OperationalError
        mommy.make(
            _model=Log,
        )
        call_command('send_notification_mails')

        log_calls = mock_logger.info.call_args_list
        assert len(log_calls) == 3
        self.check_calls_contain([
            'start processing 1 logs',
            f'could not process logs',
            'canceled processing logs',
        ], log_calls)
