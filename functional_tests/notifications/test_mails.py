from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import override_settings
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from model_mommy import mommy
from unittest.mock import patch, Mock

from apps.configuration.models import Configuration
from apps.questionnaire.models import Questionnaire
from functional_tests.base import FunctionalTest
from functional_tests.pages.sample import SampleDetailPage

driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver")
WOCAT_MAILBOX_USER_ID = 999


@override_settings(
    DO_SEND_EMAILS=True,
    DO_SEND_STAFF_ONLY=False,
    WOCAT_MAILBOX_USER_ID=WOCAT_MAILBOX_USER_ID
)
@patch('notifications.models.EmailMultiAlternatives')
class MailsTest(FunctionalTest):
    fixtures = [
        'groups_permissions',
        'sample_global_key_values',
        'sample',
    ]

    def setUp(self):
        super().setUp()

        self.set_expected_mails()
        self.set_users()
        self.set_questionnaires()

    def set_expected_mails(self):
        # Get the expected mail subject and body parts, as well as body parts
        # which should be missing.

        def add_default_parts(parts, omit: list=None):
            # Add the default body parts to the existing list. If remove is
            # provided, remove these from the body parts.
            body_parts = parts + [
                "This is an automated message",
                "You're getting this message",
                "compiled by"
            ]
            if omit:
                for r in omit:
                    body_parts.remove(r)
            return body_parts

        self.expected_mails = {
            # Editor has finished editing
            'edited': {
                'parts': add_default_parts([
                    'has been edited',
                ])
            },
            # Draft questionnaire was submitted
            'submitted': {
                'parts': add_default_parts([
                    'has been submitted',
                ])
            },
            # Submitted questionnaire was reviewed
            'reviewed': {
                'parts': add_default_parts([
                    'has been approved by the reviewer',
                    'If you are a publisher'
                ])
            },
            # Reviewed questionnaire was published
            'published': {
                'parts': add_default_parts([
                    'has been published',
                ])
            },
            # Questionnaire was deleted
            'deleted': {
                'parts': add_default_parts([
                    'has been deleted',
                ])
            },
            # Compiler was added
            'compiler_added': {
                'parts': add_default_parts([
                    'You have been added',
                    'a compiler',
                    'As a compiler',
                ], omit=['compiled by']),
                'missing': [
                    'compiled by',
                ]
            },
            # Compiler was removed
            'compiler_removed': {
                'parts': add_default_parts([
                    'You have been removed',
                    'a compiler',
                ], omit=['compiled by']),
                'missing': [
                    'compiled by',
                ]
            },
            # Editor was added
            'editor_added': {
                'parts': add_default_parts([
                    'You have been added',
                    'an editor',
                    'As an editor',
                ]),
            },
            # Editor was removed
            'editor_removed': {
                'parts': add_default_parts([
                    'You have been removed',
                    'an editor',
                ]),
            },
            # Reviewer was added
            'reviewer_added': {
                'parts': add_default_parts([
                    'You have been added',
                    'a reviewer',
                    'Please review',
                ]),
            },
            # Reviewer was removed
            'reviewer_removed': {
                'parts': add_default_parts([
                    'You have been removed',
                    'a reviewer',
                ]),
            },
            # Publisher was added
            'publisher_added': {
                'parts': add_default_parts([
                    'You have been added',
                    'a publisher',
                    'Please complete the final review',
                ]),
            },
            # Publisher was removed
            'publisher_removed': {
                'parts': add_default_parts([
                    'You have been removed',
                    'a publisher',
                ]),
            },
            # Submitted questionnaire was rejected
            'rejected_submitted': {
                'parts': add_default_parts([
                    'has been rejected',
                    'Please revise the SLM practice',
                ]),
                'missing': [
                    'If you are a reviewer',
                ]
            },
            # Reviewed questionnaire was rejected
            'rejected_reviewed': {
                'parts': add_default_parts([
                    'has been rejected',
                    'Please revise the SLM practice',
                    'If you are a reviewer',
                ])
            },
        }

    def set_users(self):
        # Set the users used for testing.
        reviewer_group = Group.objects.get(pk=3)
        publisher_group = Group.objects.get(pk=4)
        secretariat_group = Group.objects.get(pk=5)

        self.user_alice = mommy.make(
            _model=get_user_model(),
            firstname='Alice',
            email='alice@foo.com'
        )
        self.user_bob = mommy.make(
            _model=get_user_model(),
            firstname='Bob',
            email='bob@foo.com'
        )
        self.user_chris = mommy.make(
            _model=get_user_model(),
            firstname='Chris',
            email='chris@foo.com'
        )
        self.user_compiler = mommy.make(
            _model=get_user_model(),
            firstname='Compiler',
            email='compiler@foo.com'
        )
        self.user_editor_assigned = mommy.make(
            _model=get_user_model(),
            firstname='Editor',
            lastname='Assigned',
            email='editor_assigned@foo.com'
        )
        self.user_reviewer_group = mommy.make(
            _model=get_user_model(),
            firstname='Reviewer',
            lastname='Group',
            email='reviewer_group@foo.com',
            groups=[reviewer_group]
        )
        self.user_reviewer_assigned = mommy.make(
            _model=get_user_model(),
            firstname='Reviewer',
            lastname='Assigned',
            email='reviewer_assigned@foo.com'
        )
        self.user_publisher_group = mommy.make(
            _model=get_user_model(),
            firstname='Publisher',
            email='publisher@foo.com',
            groups=[publisher_group]
        )
        self.user_publisher_assigned = mommy.make(
            _model=get_user_model(),
            firstname='Publisher',
            lastname='Assigned',
            email='publisher_assigned@foo.com'
        )
        self.user_secretariat = mommy.make(
            _model=get_user_model(),
            firstname='Secretariat',
            email='secretariat@foo.com',
            groups=[secretariat_group]
        )
        self.user_wocat_mailbox = mommy.make(
            _model=get_user_model(),
            id=WOCAT_MAILBOX_USER_ID,
            firstname='WOCAT',
            lastname='Mailbox',
            email='wocat@foo.com',
        )

    def set_questionnaires(self):
        # Set the questionnaires used for testing.
        for status_code, status_name, code in [
            # Status_name will be used to set the attribute, e.g.:
            # self.questionnaire_draft
            (settings.QUESTIONNAIRE_DRAFT, 'draft', 'sample_1'),
            (settings.QUESTIONNAIRE_SUBMITTED, 'submitted', 'sample_2'),
            (settings.QUESTIONNAIRE_REVIEWED, 'reviewed', 'sample_3'),
        ]:
            questionnaire = mommy.make(
                _model=Questionnaire,
                data={},
                code=code,
                status=status_code,
                configuration=Configuration.objects.filter(code='sample').first()
            )
            for user, role in [
                (self.user_compiler, 'compiler'),
                (self.user_editor_assigned, 'editor'),
                (self.user_reviewer_assigned, 'reviewer'),
                (self.user_publisher_assigned, 'publisher'),
            ]:
                questionnaire.add_user(user, role)
            setattr(self, f'questionnaire_{status_name}', questionnaire)

    def check_mails(self, mock_mail: Mock, expected_mails: list):
        # Check that mocked mails sent match the expected mails. Mocked and
        # expected mails will be sorted first (by "to" and "subject" to allow
        # more flexible testing.
        expected_list = []
        for mail in expected_mails:
            expected = {}
            expected.update({
                **self.expected_mails[mail['mail']],
                **{
                    'to': [mail['to'].email],
                    'subject': str(settings.NOTIFICATIONS_MAIL_SUBJECTS[
                        mail['mail']])
                }
            })
            if 'message' in mail:
                expected['parts'].append(mail['message'])
            expected_list.append(expected)
        sorted_expected_list = sorted(
            expected_list, key=lambda c: (c['to'], c['subject'])
        )

        # Important: Use the same order for both mocked calls (html and plain
        # text calls) Merge both lists and sort them based on the first list.
        # Then separate them again.
        mock_mail_call_args = [call[1] for call in mock_mail.call_args_list]
        mock_alt_mail_call_args = [
            call[1] for call
            in mock_mail.return_value.attach_alternative.call_args_list]
        merged_calls = zip(mock_mail_call_args, mock_alt_mail_call_args)
        sorted_calls = sorted(
            merged_calls, key=lambda c: (c[0]['to'], c[0]['subject']))
        sorted_mock_mail_calls, sorted_mock_alt_mail_calls = zip(
            *sorted_calls)

        assert len(sorted_mock_mail_calls) == len(sorted_expected_list)
        for i, expected_args in enumerate(sorted_expected_list):
            call_args = sorted_mock_mail_calls[i]
            alt_call_args = sorted_mock_alt_mail_calls[i]
            if 'to' in expected_args:
                assert call_args['to'] == expected_args['to']
            if 'subject' in expected_args:
                self.assertIn(
                    expected_args['subject'],
                    call_args['subject'],
                    msg='Not found in subject')
            if 'parts' in expected_args:
                for part in expected_args['parts']:
                    self.assertIn(
                        part,
                        call_args['body'],
                        msg='Not found in mail body (plain text)')
                    self.assertIn(
                        part,
                        alt_call_args['content'],
                        msg='Not found in mail content (HTML)')
            if 'missing' in expected_args:
                for missing in expected_args['missing']:
                    self.assertNotIn(missing, call_args['body'])
                    self.assertNotIn(missing, alt_call_args['content'])

    def test_mails_submit(self, mock_mail):
        # Submitting a draft questionnaire sends an email to all reviewers.
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': self.questionnaire_draft.code}
        detail_page.open(login=True, user=self.user_compiler)
        detail_page.submit_questionnaire()

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_reviewer_assigned,
                'mail': 'submitted'
            },
            {
                'to': self.user_wocat_mailbox,
                'mail': 'submitted'
            },
        ])

        # In order to always access the same mail, do some ordering first
        mock_mail_call_args = [call[1] for call in mock_mail.call_args_list]
        mock_alt_mail_call_args = [
            call[1] for call
            in mock_mail.return_value.attach_alternative.call_args_list]
        merged_calls = zip(mock_mail_call_args, mock_alt_mail_call_args)
        sorted_calls = sorted(
            merged_calls, key=lambda c: (c[0]['to'], c[0]['subject']))
        sorted_mock_mail_calls, sorted_mock_alt_mail_calls = zip(
            *sorted_calls)
        mail_body_plain = sorted_mock_mail_calls[1]['body']
        mail_body_html = sorted_mock_alt_mail_calls[1]['content']

        for mail_body in [mail_body_plain, mail_body_html]:
            assert self.questionnaire_draft.get_absolute_url() in mail_body
            assert self.user_wocat_mailbox.get_display_name() in mail_body
            assert self.user_compiler.get_display_name() in mail_body
            assert str(settings.BASE_URL) in mail_body
            assert str(self.user_wocat_mailbox.mailpreferences.get_signed_url()) in \
                   mail_body

    def test_mails_submit_message(self, mock_mail):
        # Submitting a draft questionnaire sends an email to all reviewers which
        # includes the message entered upon submission
        submit_message = 'Message for the reviewer'

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': self.questionnaire_draft.code}
        detail_page.open(login=True, user=self.user_compiler)
        detail_page.submit_questionnaire(message=submit_message)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_wocat_mailbox,
                'mail': 'submitted',
                'message': submit_message
            },
            {
                'to': self.user_reviewer_assigned,
                'mail': 'submitted',
                'message': submit_message
            }
        ])

    def test_mails_review(self, mock_mail):
        # Reviewing a submitted questionnaire sends an email to all publishers,
        # as well as to the compiler.
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_submitted.code
        }
        detail_page.open(login=True, user=self.user_reviewer_group)
        detail_page.review_questionnaire()

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'reviewed'
            },
            {
                'to': self.user_editor_assigned,
                'mail': 'reviewed'
            },
            {
                'to': self.user_publisher_assigned,
                'mail': 'reviewed',
            },
            {
                'to': self.user_wocat_mailbox,
                'mail': 'reviewed'
            },
        ])

    def test_mails_review_message(self, mock_mail):
        # The message written when reviewing the questionnaire is in the mail.
        review_message = 'Message for the publisher'

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_submitted.code
        }
        detail_page.open(login=True, user=self.user_reviewer_group)
        detail_page.review_questionnaire(message=review_message)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'reviewed',
                'message': review_message
            },
            {
                'to': self.user_editor_assigned,
                'mail': 'reviewed',
                'message': review_message
            },
            {
                'to': self.user_publisher_assigned,
                'mail': 'reviewed',
                'message': review_message
            },
            {
                'to': self.user_wocat_mailbox,
                'mail': 'reviewed',
                'message': review_message
            },
        ])

    def test_mails_publish(self, mock_mail):
        # Publishing a reviewed questionnaire sends an email to the compiler.
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_reviewed.code
        }
        detail_page.open(login=True, user=self.user_publisher_group)
        detail_page.publish_questionnaire()

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'published'
            },
            {
                'to': self.user_editor_assigned,
                'mail': 'published'
            },
            {
                'to': self.user_reviewer_assigned,
                'mail': 'published'
            },
            {
                'to': self.user_wocat_mailbox,
                'mail': 'published'
            },
        ])

    def test_mails_publish_message(self, mock_mail):
        # Publishing a reviewed questionnaire adds the message to the email.
        publish_message = 'Success message'

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_reviewed.code
        }
        detail_page.open(login=True, user=self.user_publisher_group)
        detail_page.publish_questionnaire(message=publish_message)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'published',
                'message': publish_message,
            },
            {
                'to': self.user_editor_assigned,
                'mail': 'published',
                'message': publish_message,
            },
            {
                'to': self.user_reviewer_assigned,
                'mail': 'published',
                'message': publish_message,
            },
            {
                'to': self.user_wocat_mailbox,
                'mail': 'published',
                'message': publish_message,
            },
        ])

    def test_mails_delete(self, mock_mail):
        # Deleting a questionnaire sends an email to the compiler.
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_reviewed.code
        }
        detail_page.open(login=True, user=self.user_secretariat)
        detail_page.delete_questionnaire()

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'deleted'
            },
            {
                'to': self.user_editor_assigned,
                'mail': 'deleted'
            },
            {
                'to': self.user_reviewer_assigned,
                'mail': 'deleted'
            },
            {
                'to': self.user_publisher_assigned,
                'mail': 'deleted'
            },
            {
                'to': self.user_wocat_mailbox,
                'mail': 'deleted'
            },
        ])

    def test_mails_edit(self, mock_mail):
        # Notifying about having finished editing a draft questionnaire sends an
        # email to the compiler.
        self.questionnaire_draft.add_user(self.user_alice, 'editor')
        # Reviewer should not receive an email
        self.questionnaire_draft.add_user(self.user_bob, 'reviewer')

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': self.questionnaire_draft.code}
        detail_page.open(login=True, user=self.user_alice)
        detail_page.finish_editing()

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'edited'
            }
        ])

    def test_mails_edit_message(self, mock_mail):
        # Notifying about having finished editing a draft questionnaire sends an
        # email to the compiler, including the message.
        edit_message = 'Done editing.'

        self.questionnaire_draft.add_user(self.user_alice, 'editor')
        # Reviewer should not receive an email
        self.questionnaire_draft.add_user(self.user_bob, 'reviewer')

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': self.questionnaire_draft.code}
        detail_page.open(login=True, user=self.user_alice)
        detail_page.finish_editing(message=edit_message)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'edited'
            }
        ])

    @patch('apps.accounts.views.remote_user_client.search_users')
    @patch('apps.questionnaire.utils.remote_user_client.get_user_information')
    def test_mails_editor_added(
            self, mock_user_information, mock_search_users, mock_mail):
        # Inviting an editor sends a mail to this editor.
        mock_search_users.side_effect = self.get_mock_remote_user_client_search
        mock_user_information.side_effect = self.get_mock_remote_user_client_user_information

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': self.questionnaire_draft.code}
        detail_page.open(login=True, user=self.user_compiler)
        detail_page.assign_user(self.user_bob.firstname)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_bob,
                'mail': 'editor_added',
            }
        ])

    @patch('apps.accounts.views.remote_user_client.search_users')
    @patch('apps.questionnaire.utils.remote_user_client.get_user_information')
    def test_mails_editor_removed(
            self, mock_user_information, mock_search_users, mock_mail):
        # Removing an editor sends a mail to the removed editor.
        mock_search_users.side_effect = self.get_mock_remote_user_client_search
        mock_user_information.side_effect = self.get_mock_remote_user_client_user_information

        self.questionnaire_draft.add_user(self.user_bob, 'editor')

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': self.questionnaire_draft.code}
        detail_page.open(login=True, user=self.user_compiler)
        detail_page.remove_user(self.user_bob.firstname)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_bob,
                'mail': 'editor_removed'
            }
        ])

    @patch('apps.accounts.views.remote_user_client.search_users')
    @patch('apps.questionnaire.utils.remote_user_client.get_user_information')
    def test_mails_reviewer_added(
            self, mock_user_information, mock_search_users, mock_mail):
        # Inviting a reviewer sends a mail to this reviewer and to the compiler.
        mock_search_users.side_effect = self.get_mock_remote_user_client_search
        mock_user_information.side_effect = self.get_mock_remote_user_client_user_information

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_submitted.code
        }
        detail_page.open(login=True, user=self.user_secretariat)
        detail_page.assign_user(self.user_bob.firstname)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_bob,
                'mail': 'reviewer_added'
            },
        ])

    @patch('apps.accounts.views.remote_user_client.search_users')
    @patch('apps.questionnaire.utils.remote_user_client.get_user_information')
    def test_mails_reviewer_removed(
            self, mock_user_information, mock_search_users, mock_mail):
        # Removing a reviewer sends a mail to the removed reviewer and to the
        # compiler.
        mock_search_users.side_effect = self.get_mock_remote_user_client_search
        mock_user_information.side_effect = self.get_mock_remote_user_client_user_information

        self.questionnaire_submitted.add_user(self.user_bob, 'reviewer')

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_submitted.code
        }
        detail_page.open(login=True, user=self.user_secretariat)
        detail_page.remove_user(self.user_bob.firstname)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_bob,
                'mail': 'reviewer_removed'
            },
        ])

    @patch('apps.accounts.views.remote_user_client.search_users')
    @patch('apps.questionnaire.utils.remote_user_client.get_user_information')
    def test_mails_publisher_added(
            self, mock_user_information, mock_search_users, mock_mail):
        # Inviting a publisher sends a mail to this publisher and to the
        # compiler.
        mock_search_users.side_effect = self.get_mock_remote_user_client_search
        mock_user_information.side_effect = self.get_mock_remote_user_client_user_information

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_reviewed.code
        }
        detail_page.open(login=True, user=self.user_secretariat)
        detail_page.assign_user(self.user_bob.firstname)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_bob,
                'mail': 'publisher_added'
            },
        ])

    @patch('apps.accounts.views.remote_user_client.search_users')
    @patch('apps.questionnaire.utils.remote_user_client.get_user_information')
    def test_mails_publisher_removed(
            self, mock_user_information, mock_search_users, mock_mail):
        # Removing a publisher sends a mail to the removed publisher and to the
        # compiler.
        mock_search_users.side_effect = self.get_mock_remote_user_client_search
        mock_user_information.side_effect = self.get_mock_remote_user_client_user_information

        self.questionnaire_reviewed.add_user(self.user_bob, 'publisher')

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_reviewed.code
        }
        detail_page.open(login=True, user=self.user_secretariat)
        detail_page.remove_user(self.user_bob.firstname)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_bob,
                'mail': 'publisher_removed'
            },
        ])

    @patch('apps.accounts.views.remote_user_client.search_users')
    @patch('apps.questionnaire.utils.remote_user_client.get_user_information')
    def test_mails_compiler_added(
            self, mock_user_information, mock_search_users, mock_mail):
        # Changing the compiler sends a mail to the previous compiler and to the
        # new one.
        mock_search_users.side_effect = self.get_mock_remote_user_client_search
        mock_user_information.side_effect = self.get_mock_remote_user_client_user_information

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': self.questionnaire_draft.code}
        detail_page.open(login=True, user=self.user_secretariat)
        detail_page.change_compiler(
            self.user_bob.firstname, keep_as_editor=False)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'compiler_removed'
            },
            {
                'to': self.user_bob,
                'mail': 'compiler_added'
            },
        ])

    @patch('apps.accounts.views.remote_user_client.search_users')
    @patch('apps.questionnaire.utils.remote_user_client.get_user_information')
    def test_mails_compiler_added_keep_as_editor(
            self, mock_user_information, mock_search_users, mock_mail):
        # Changing the compiler sends a mail to the previous compiler and to the
        # new one. If the previous compiler is now an editor, another mail is
        # sent (also to the new compiler).
        mock_search_users.side_effect = self.get_mock_remote_user_client_search
        mock_user_information.side_effect = self.get_mock_remote_user_client_user_information

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': self.questionnaire_draft.code}
        detail_page.open(login=True, user=self.user_secretariat)
        detail_page.change_compiler(
            self.user_bob.firstname, keep_as_editor=True)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'compiler_removed'
            },
            {
                'to': self.user_bob,
                'mail': 'compiler_added'
            },
            {
                'to': self.user_compiler,
                'mail': 'editor_added'
            },
        ])

    def test_mails_rejected_submitted(self, mock_mail):
        # Rejecting a submitted questionnaire sends an email to the compiler.
        reject_message = 'Rejected because it is incomplete.'

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_submitted.code
        }
        detail_page.open(login=True, user=self.user_reviewer_group)
        detail_page.reject_questionnaire(reject_message)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'rejected_submitted',
                'message': reject_message,
            },
            {
                'to': self.user_editor_assigned,
                'mail': 'rejected_submitted',
                'message': reject_message,
            },
            {
                'to': self.user_wocat_mailbox,
                'mail': 'rejected_submitted',
                'message': reject_message,
            },
        ])

    def test_mails_rejected_reviewed(self, mock_mail):
        # Rejecting a reviewed questionnaire sends an email to the compiler.
        reject_message = 'Rejected because it is incomplete.'

        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {
            'identifier': self.questionnaire_reviewed.code
        }
        detail_page.open(login=True, user=self.user_publisher_group)
        detail_page.reject_questionnaire(reject_message)

        call_command('send_notification_mails')

        self.check_mails(mock_mail, [
            {
                'to': self.user_compiler,
                'mail': 'rejected_reviewed',
                'message': reject_message,
            },
            {
                'to': self.user_editor_assigned,
                'mail': 'rejected_reviewed',
                'message': reject_message,
            },
            {
                'to': self.user_reviewer_assigned,
                'mail': 'rejected_reviewed',
                'message': reject_message,
            },
            {
                'to': self.user_wocat_mailbox,
                'mail': 'rejected_reviewed',
                'message': reject_message,
            },
        ])
