import re

import pytest
from django.conf import settings
from django.urls import reverse
from django.test.utils import override_settings
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from unittest.mock import patch
from elasticmock import elasticmock

from apps.accounts.models import User
from functional_tests.base import FunctionalTest
from apps.questionnaire.models import Questionnaire
from apps.sample.tests.test_views import (
    route_questionnaire_details,
    get_position_of_category)
from apps.wocat.tests.test_views import route_home
from apps.search.tests.test_index import create_temp_indices

from functional_tests.pages.qcat import MyDataPage
from functional_tests.pages.sample import SampleDetailPage, SampleListPage, \
    SampleNewPage, SampleEditPage, SampleStepPage


@elasticmock
@override_settings(
    NOTIFICATIONS_CREATE='create_foo',
    NOTIFICATIONS_CHANGE_STATUS='change_foo'
)
class ModerationTest(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'sample_global_key_values',
        'sample',
    ]

    def setUp(self):
        super(ModerationTest, self).setUp()
        create_temp_indices([('sample', '2015')])

    @patch('apps.questionnaire.signals.create_questionnaire.send')
    @patch('apps.questionnaire.signals.change_status.send')
    def test_questionnaire_permissions(
            self, mock_change_status, mock_create_signal):

        key_1 = 'Foo'
        key_3 = 'Bar'

        user_1 = self.create_new_user(email='user_1@foo.com')
        user_2 = self.create_new_user(email='user_2@foo.com')
        user_moderator = self.create_new_user(
            email='moderator@foo.com', groups=['Reviewers', 'Publishers'])

        # User 1 logs in and creates a questionnaire
        new_page = SampleNewPage(self)
        new_page.open(login=True, user=user_1)
        new_page.create_new_questionnaire(key_1=key_1, key_3=key_3)

        # A new notification should be created
        mock_create_signal.assert_called_once_with(
            questionnaire=Questionnaire.objects.latest('created'),
            sender='create_foo',
            user=user_1
        )

        # User 1 changes to the view mode
        new_page.view_questionnaire()

        # User 1 refreshes the page and sees the questionnaire
        view_page = SampleDetailPage(self)
        view_page.route_kwargs = {
            'identifier': Questionnaire.objects.latest('pk').code}
        view_page.open()
        view_page.has_text(key_1)

        # User 1 logs out and cannot see the questionnaire
        view_page.logout()
        view_page.open()
        assert new_page.is_not_found_404()

        # User 2 logs in and cannot see the questionnaire
        view_page.open(login=True, user=user_2)
        assert view_page.is_not_found_404()

        # Moderator logs in and cannot see the questionnaire
        view_page.open(login=True, user=user_moderator)
        assert view_page.is_not_found_404()

        # User 1 submits the questionnaire
        view_page.open(login=True, user=user_1)
        view_page.submit_questionnaire()

        # A notification for the new status is created
        mock_change_status.assert_called_once_with(
            message='',
            questionnaire=Questionnaire.objects.latest('created'),
            sender='change_foo',
            user=user_1,
            previous_status=settings.QUESTIONNAIRE_DRAFT
        )

        # User 1 logs out and cannot see the questionnaire
        view_page.logout()
        view_page.open()
        assert view_page.is_not_found_404()

        # User 2 logs in and cannot see the questionnaire
        view_page.open(login=True, user=user_2)
        assert view_page.is_not_found_404()

        # Moderator logs in and sees the questionnaire
        view_page.open(login=True, user=user_moderator)
        assert view_page.has_text(key_1)

        # Moderator publishes the questionnaire
        view_page.review_questionnaire()
        view_page.publish_questionnaire()

        # The moderator cannot create a new version
        assert not view_page.can_create_new_version()

        # Logged out users can see the questionnaire
        view_page.logout()
        view_page.open()
        assert view_page.has_text(key_1)

        # Logged out users cannot create a new version
        assert not view_page.can_create_new_version()

        # User 2 cannot edit the questionnaire
        view_page.open(login=True, user=user_2)
        assert view_page.has_text(key_1)
        assert not view_page.can_create_new_version()

        # User 1 can edit the questionnaire
        view_page.open(login=True, user=user_1)
        assert view_page.has_text(key_1)
        assert view_page.can_create_new_version()


@elasticmock
class ModerationTestFixture(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'sample_global_key_values',
        'sample',
        'sample_questionnaire_status',
        'sample_user',
    ]

    def setUp(self):
        super(ModerationTestFixture, self).setUp()
        create_temp_indices([('sample', '2015')])

        self.user_compiler = User.objects.get(pk=101)
        self.user_editor = User.objects.get(pk=102)
        self.user_reviewer = User.objects.get(pk=103)
        self.user_publisher = User.objects.get(pk=104)
        self.user_secretariat = User.objects.get(pk=107)

        self.sample_2_text = 'Foo 2'

    def test_review_locked_questionnaire(self):
        # Secretariat user logs in and goes to the details of a SUBMITTED
        # questionnaire
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': 'sample_2'}
        detail_page.open(login=True, user=self.user_secretariat)
        assert detail_page.has_text(self.sample_2_text)

        # User starts to edit the first section (this sets a lock on the
        # questionnaire)
        detail_page.edit_questionnaire()
        edit_page = SampleEditPage(self)
        edit_page.click_edit_category(edit_page.CATEGORIES[0][0])

        # User goes back to the details (without saving!)
        detail_page.open()

        # User reviews the questionnaire and sees there is no exception thrown
        detail_page.review_questionnaire()

        # He sees the questionnaire is now reviewed
        detail_page.check_status('reviewed')

    def test_review_locked_questionnaire_blocked_by_other(self):

        # Reviewer logs in and goes to the details of a SUBMITTED questionnaire
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': 'sample_2'}
        detail_page.open(login=True, user=self.user_reviewer)
        assert detail_page.has_text('Foo 2')

        # He starts to edit the first section (this sets a lock on the
        # questionnaire)
        detail_page.edit_questionnaire()
        edit_page = SampleEditPage(self)
        edit_page.click_edit_category('cat_1')

        # Secretariat user logs in and goes to the details of the same
        # questionnaire
        detail_page.open(login=True, user=self.user_secretariat)
        assert detail_page.has_text('Foo 2')

        # The user sees a message that the questionnaire is currently locked
        assert detail_page.is_locked_by(user=self.user_reviewer)

        # He reviews the questionnaire which is still locked and sees there is
        # no exception thrown, however she sees a warning.
        detail_page.review_questionnaire(check_success=False)
        assert detail_page.is_locked_by(user=self.user_reviewer)

        # He sees the questionnaire is still submitted
        detail_page.check_status('submitted')

    def test_secretariat_edit(self):

        # Secretariat user logs in
        # He goes to the details of a DRAFT questionnaire which he did not enter
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': 'sample_1'}
        detail_page.open(login=True, user=self.user_secretariat)
        assert detail_page.has_text('Foo 1')

        # He sees a button to edit the questionnaire, he clicks it
        detail_page.edit_questionnaire()

        # In edit mode, he sees that he can edit the first section
        edit_page = SampleEditPage(self)
        edit_page.click_edit_category('cat_1')

        # He saves the step and returns
        step_page = SampleStepPage(self)
        step_page.submit_step()

        # He also opens a public questionnaire which he did not enter
        detail_page.route_kwargs = {'identifier': 'sample_3'}
        detail_page.open()
        assert detail_page.has_text('Foo 3')

        # In the database, there is only 1 version
        assert Questionnaire.objects.filter(code='sample_3').count() == 1

        # He sees a button to edit the questionnaire, he clicks it and creates a
        # new version
        detail_page.create_new_version()

        # In the database, there are now 2 versions
        assert Questionnaire.objects.filter(code='sample_3').count() == 2

    def test_secretariat_delete(self):
        # Secretariat user logs in
        # He goes to the details of a DRAFT questionnaire which he did not enter
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': 'sample_1'}
        detail_page.open(login=True, user=self.user_secretariat)
        assert detail_page.has_text('Foo 1')
        detail_page.check_status('draft')

        # He deletes the questionnaire.
        detail_page.delete_questionnaire()

        # He sees that he has been redirected to the "My SLM Practices" page
        my_data_page = MyDataPage(self)
        assert my_data_page.get_url() in self.browser.current_url

        # He goes to the details of a SUBMITTED questionnaire which he did not
        # enter
        detail_page.route_kwargs = {'identifier': 'sample_2'}
        detail_page.open()
        assert detail_page.has_text('Foo 2')
        detail_page.check_status('submitted')

        # He deletes the questionnaire.
        detail_page.delete_questionnaire()

        # He sees that he has been redirected to the "My SLM Practices" page
        assert my_data_page.get_url() in self.browser.current_url

        # He goes to the details of a REVIEWED questionnaire which he did not
        # enter
        detail_page.route_kwargs = {'identifier': 'sample_7'}
        detail_page.open()
        assert detail_page.has_text('Foo 7')
        detail_page.check_status('reviewed')

        # He deletes the questionnaire.
        detail_page.delete_questionnaire()

        # He sees that he has been redirected to the "My SLM Practices" page
        assert my_data_page.get_url() in self.browser.current_url

        # He also opens a PUBLIC questionnaire which he did not enter
        detail_page.route_kwargs = {'identifier': 'sample_3'}
        detail_page.open()
        assert detail_page.has_text('Foo 3')

        # In the database, there is only 1 version
        query_sample_3 = Questionnaire.objects.get(code='sample_3')
        assert query_sample_3.status == settings.QUESTIONNAIRE_PUBLIC
        assert not query_sample_3.is_deleted

        # He deletes the questionnaire.
        detail_page.delete_questionnaire()

        # He sees that he has been redirected to the "My SLM Practices" page
        assert my_data_page.get_url() in self.browser.current_url

        # In the database, there is still only 1 version
        query_sample_3 = Questionnaire.objects.get(code='sample_3')
        assert query_sample_3.status == settings.QUESTIONNAIRE_PUBLIC
        assert query_sample_3.is_deleted

        # He opens another PUBLIC questionnaire and edits it
        detail_page.route_kwargs = {'identifier': 'sample_5'}
        detail_page.open()
        assert detail_page.has_text('Foo 5')

        detail_page.create_new_version()

        # He deletes the newly created draft version
        detail_page.check_status('draft')
        detail_page.delete_questionnaire()

        # He sees that he has been redirected to the PUBLIC version of the
        # questionnaire, not the "My SLM Practices" page
        assert detail_page.get_url() in self.browser.current_url

        # He creates another version by editing it
        detail_page.create_new_version()

        # This time, he publishes the new version
        detail_page.submit_questionnaire()
        detail_page.review_questionnaire()
        detail_page.publish_questionnaire()

        # Now he deletes it
        detail_page.delete_questionnaire()

        # He is now redirected to the "My SLM Practices" page as there is no
        # version to show
        assert my_data_page.get_url() in self.browser.current_url

    def test_review_panel(self):

        # An Editor logs in and goes to the details page of a questionnaire
        # which he did not enter
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': 'sample_5'}
        detail_page.open(login=True, user=self.user_editor)
        assert detail_page.has_text('Foo 5')

        # He does see the review panel but no actions are possible
        detail_page.check_review_actions(
            create_new=False,
            edit=False,
            submit=False,
            review=False,
            publish=False,
            delete=False,
            change_compiler=False,
        )

        # He goes to the details of a questionnaire where he is editor (only!).
        detail_page.route_kwargs = {'identifier': 'sample_3'}
        detail_page.open()
        assert detail_page.has_text('Foo 3')

        # He does see the review panel but can only edit
        detail_page.check_review_actions(
            create_new=True,
            edit=False,
            submit=False,
            review=False,
            publish=False,
            delete=False,
            change_compiler=False,
        )

        # He creates a new version
        detail_page.create_new_version()
        edit_page = SampleEditPage(self)

        # He makes some changes and saves the questionnaire
        edit_page.click_edit_category('cat_1')
        step_page = SampleStepPage(self)
        step_page.enter_text(step_page.LOC_FORM_INPUT_KEY_1, ' (by Editor)')
        step_page.submit_step()

        # He sees a review panel but he does not see the button to
        # submit the questionnaire for review
        edit_page.check_review_actions(
            create_new=False,
            edit=False,
            submit=False,
            review=False,
            publish=False,
            delete=False,
            change_compiler=False,
        )

        # He sees the buttons to edit each section
        assert edit_page.can_edit_category('cat_1')

        # User decides to view the questionnaire
        edit_page.view_questionnaire()

        # He does not see the button to edit each section anymore
        assert not edit_page.can_edit_category('cat_1')

        # Now the compiler logs in and goes to the detail page of the
        # questionnaire
        detail_page.open(login=True, user=self.user_compiler)

        # The compiler does see the button to submit the questionnaire
        detail_page.check_review_actions(
            create_new=False,
            edit=True,
            submit=True,
            review=False,
            publish=False,
            delete=True,
            change_compiler=False,
        )

        # On the detail page, the compiler does not see buttons to edit the
        # categories
        assert not detail_page.can_edit_category('cat_1')

        # The compiler goes to the edit page and now sees the category buttons
        detail_page.edit_questionnaire()
        assert edit_page.can_edit_category('cat_1')

        # She submits the questionnaire to review
        assert edit_page.can_delete_questionnaire()
        edit_page.submit_questionnaire()

        # The questionnaire is now pending for review. The review panel
        # is visible but Compiler cannot do any actions.
        detail_page.check_review_actions(
            create_new=False,
            edit=False,
            submit=False,
            review=False,
            publish=False,
            delete=False,
            change_compiler=False,
        )

        # The editor logs in again and opens the same page
        detail_page.open(login=True, user=self.user_editor)

        # He goes to the page and he also sees the review panel but no
        # actions can be taken.
        detail_page.check_review_actions(
            create_new=False,
            edit=False,
            submit=False,
            review=False,
            publish=False,
            delete=False,
            change_compiler=False,
        )

        # Reviewer logs in and opens the page
        detail_page.open(login=True, user=self.user_reviewer)

        # He goes to the page and sees the review panel. There is a
        # button to do the review.
        detail_page.check_review_actions(
            create_new=False,
            edit=True,
            submit=False,
            review=True,
            publish=False,
            delete=False,
            change_compiler=False,
        )

        # He is on the detail page and does not see the buttons to edit each
        # section
        assert not detail_page.can_edit_category('cat_1')

        # He goes to the edit page and now she sees the buttons
        detail_page.edit_questionnaire()
        assert edit_page.can_edit_category('cat_1')

        # He clicks the button to do the review
        edit_page.review_questionnaire()

        # He sees the review panel but no action is possible.
        detail_page.check_review_actions(
            create_new=False,
            edit=False,
            submit=False,
            review=False,
            publish=False,
            delete=False,
            change_compiler=False,
        )

        # Compiler logs in and goes to the page, sees the review panel
        # but no actions possible
        detail_page.open(login=True, user=self.user_compiler)
        detail_page.check_review_actions(
            create_new=False,
            edit=False,
            submit=False,
            review=False,
            publish=False,
            delete=False,
            change_compiler=False,
        )

        # Editor logs in and goes to the page, sees the review panel but
        # no actions possible.
        detail_page.open(login=True, user=self.user_editor)
        detail_page.check_review_actions(
            create_new=False,
            edit=False,
            submit=False,
            review=False,
            publish=False,
            delete=False,
            change_compiler=False,
        )

        # Publisher logs in and goes to the page. He sees the review
        # panel with a button to publish.
        detail_page.open(login=True, user=self.user_publisher)
        detail_page.check_review_actions(
            create_new=False,
            edit=True,
            submit=False,
            review=False,
            publish=True,
            delete=False,
            change_compiler=False,
        )

        # He is on the detail page and does not see the buttons to edit each
        # section
        assert not detail_page.can_edit_category('cat_1')

        # He goes to the edit page and now she sees the buttons
        detail_page.edit_questionnaire()

        # He clicks the button to publish the questionnaire.
        detail_page.publish_questionnaire()

        # The review panel is there but he cannot edit
        detail_page.check_review_actions(
            create_new=False,
            edit=False,
            submit=False,
            review=False,
            publish=False,
            delete=False,
            change_compiler=False,
        )

    @override_settings(
        NOTIFICATIONS_ADD_MEMBER='add_member',
        NOTIFICATIONS_REMOVE_MEMBER='delete_member'
    )
    @patch('apps.questionnaire.utils.remote_user_client.get_user_information')
    @patch('apps.accounts.views.remote_user_client.search_users')
    @patch('apps.questionnaire.signals.change_member.send')
    def test_secretariat_can_assign_reviewer(
            self, mock_member_change, mock_search_users, mock_user_information):
        mock_search_users.side_effect = self.get_mock_remote_user_client_search
        mock_user_information.side_effect = self.get_mock_remote_user_client_user_information

        identifier = 'sample_2'

        user_alice = self.create_new_user(
            email='alice@foo.com',
            last_name='Alice',
            first_name='Cooper'
        )
        user_bob = self.create_new_user(
            email='bob@foo.com',
            last_name='Bob',
            first_name='Tables'
        )
        user_chris = self.create_new_user(
            email='chris@foo.com',
            last_name='Chris',
            first_name='Cornell'
        )

        # A user logs in
        self.doLogin(user=self.user_editor)

        # He goes to a submitted questionnaire
        url = self.live_server_url + reverse(
            route_questionnaire_details, kwargs={'identifier': identifier}
        )
        self.browser.get(url)
        self.findBy('xpath', '//span[contains(@class, "is-submitted")]')

        # He sees he can neither edit, review or assign users
        self.findByNot('xpath', '//a[contains(text(), "Edit")]')
        self.findByNot('id', 'button-review')
        self.findByNot('id', 'review-list-assigned-users')

        # A reviewer logs in
        self.doLogin(user=self.user_reviewer)

        # He goes to a submitted questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_details, kwargs={'identifier': identifier}))
        self.findBy('xpath', '//span[contains(@class, "is-submitted")]')

        # He sees he can edit and review, but not assign users
        self.findBy('xpath', '//a[contains(text(), "Edit")]')
        self.findBy('id', 'button-review')
        self.findByNot('id', 'review-list-assigned-users')

        # Secretariat logs in
        self.doLogin(user=self.user_secretariat)

        # She goes to a submitted questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_details, kwargs={'identifier': identifier}))
        self.findBy('xpath', '//span[contains(@class, "is-submitted")]')

        # She sees he can edit and review and assign users
        self.findBy('xpath', '//a[contains(text(), "Edit")]')
        self.findBy('id', 'button-review')
        self.findBy('id', 'review-list-assigned-users')

        # She decides to add two users as reviewers
        self.findBy(
            'xpath', '//a[contains(@class, "js-toggle-edit-assigned-users")]').\
            click()

        selected_users = self.findManyBy(
            'xpath', '//div[@id="review-new-user"]/div[contains(@class, '
                     '"alert-box")]')
        self.assertEqual(len(selected_users), 0)

        self.findBy('id', 'review-search-user').send_keys(user_alice.firstname)
        WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "ui-menu-item")))
        self.findBy(
            'xpath',
            f'//li[@class="ui-menu-item"]//strong[text()="'
            f'{user_alice.get_display_name()}"]'
        ).click()

        selected_users = self.findManyBy(
            'xpath', '//div[@id="review-new-user"]/div[contains(@class, '
                     '"alert-box")]')
        self.assertEqual(len(selected_users), 1)

        self.findBy('id', 'review-search-user').send_keys(user_bob.lastname)
        WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "ui-menu-item")))
        self.findBy(
            'xpath',
            f'//li[@class="ui-menu-item"]//strong[text()="'
            f'{user_bob.get_display_name()}"]'
        ).click()

        selected_users = self.findManyBy(
            'xpath', '//div[@id="review-new-user"]/div[contains(@class, '
                     '"alert-box")]')
        self.assertEqual(len(selected_users), 2)
        self.assertTrue(user_alice.get_display_name() in selected_users[0].text)
        self.assertTrue(user_bob.get_display_name() in selected_users[1].text)

        # She updates the users
        btn = self.findBy('id', 'button-assign')
        self.scroll_to_element(btn)
        btn.click()
        self.findBy('xpath', '//div[contains(@class, "success")]')

        # Two notifications are created
        self.assertEqual(mock_member_change.call_count, 2)
        mock_member_change.assert_called_with(
            sender='add_member',
            questionnaire=Questionnaire.objects.get(code=identifier),
            user=self.user_secretariat,
            affected=User.objects.get(email=user_bob.email),
            role='reviewer'
        )
        mock_member_change.reset_mock()

        # She sees the users were added
        assigned_users = self.findManyBy(
            'xpath', '//div[@id="review-list-assigned-users"]/ul/li')
        self.assertEqual(len(assigned_users), 2)
        users = [self.get_text_excluding_children(user).strip() for user in
                 assigned_users]
        self.assertEqual(sorted(users), [
            user_alice.get_display_name(), user_bob.get_display_name()])
        self.assertNotEqual(users[0], users[1])

        # She edits the users again
        self.findBy(
            'xpath', '//a[contains(@class, "js-toggle-edit-assigned-users")]').\
            click()
        selected_users = self.findManyBy(
            'xpath', '//div[@id="review-new-user"]/div[contains(@class, '
                     '"alert-box")]')
        self.assertEqual(len(selected_users), 2)
        users = [self.get_text_excluding_children(user).strip() for user in
                 selected_users]
        self.assertEqual(sorted(users), [
            user_alice.get_display_name(), user_bob.get_display_name()])
        self.assertNotEqual(users[0], users[1])

        # She removes one of the user
        remove_button = self.findBy(
            'xpath', '//div[@id="review-new-user"]/div[contains(@class, '
                     f'"alert-box") and contains(text(), "'
                     f'{user_alice.get_display_name()}")]/a'
        )
        delete_user = re.findall('\d+', remove_button.get_attribute('onclick'))

        self.hide_notifications()
        remove_button.click()
        selected_users = self.findManyBy(
            'xpath',
            '//div[@id="review-new-user"]/div[contains(@class, "alert-box")]'
        )

        self.assertEqual(len(selected_users), 1)

        # She adds another user
        self.findBy('id', 'review-search-user').send_keys(user_chris.firstname)
        WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "ui-menu-item")))
        self.findBy(
            'xpath',
            f'//li[@class="ui-menu-item"]//strong[text()="'
            f'{user_chris.get_display_name()}"]'
        ).click()

        selected_users = self.findManyBy(
            'xpath', '//div[@id="review-new-user"]/div[contains(@class, '
                     '"alert-box")]')
        self.assertEqual(len(selected_users), 2)
        users = [self.get_text_excluding_children(user).strip() for user in
                 selected_users]
        self.assertEqual(sorted(users), [
            user_chris.get_display_name(), user_bob.get_display_name()])
        self.assertNotEqual(users[0], users[1])

        # She updates the users
        btn = self.findBy('id', 'button-assign')
        self.scroll_to_element(btn)
        btn.click()
        self.findBy('xpath', '//div[contains(@class, "success")]')

        # She sees the users were added
        assigned_users = self.findManyBy(
            'xpath', '//div[@id="review-list-assigned-users"]/ul/li')
        self.assertEqual(len(assigned_users), 2)
        users = [self.get_text_excluding_children(user).strip() for user in
                 assigned_users]
        self.assertEqual(sorted(users), [
            user_chris.get_display_name(), user_bob.get_display_name()])
        self.assertNotEqual(users[0], users[1])

        # Users are deleted after submitting the page
        self.browser.get(url)
        mock_member_change.assert_called_with(
            sender='delete_member',
            questionnaire=Questionnaire.objects.get(code=identifier),
            user=self.user_secretariat,
            affected=User.objects.get(id=delete_user[-1]),
            role='reviewer'
        )

    @override_settings(
        NOTIFICATIONS_ADD_MEMBER='add_member',
        NOTIFICATIONS_REMOVE_MEMBER='delete_member',
        QUESTIONNAIRE_COMPILER = 'compiler',
        QUESTIONNAIRE_EDITOR = 'editor'
    )
    @patch('apps.questionnaire.utils.remote_user_client.get_user_information')
    @patch('apps.accounts.views.remote_user_client.search_users')
    @patch('apps.questionnaire.signals.change_member.send')
    def test_secretariat_can_assign_reviewer_2(
            self, mock_member_change, mock_search_users, mock_user_information):
        mock_search_users.side_effect = self.get_mock_remote_user_client_search
        mock_user_information.side_effect = self.get_mock_remote_user_client_user_information

        identifier = 'sample_3'
        editor = User.objects.get(pk=102)
        old_compiler = User.objects.get(pk=101)
        new_compiler_1 = self.create_new_user(
            email='new_compiler_1@foo.com',
            last_name='wocat',
            first_name='test2'
        )
        new_compiler_2 = self.create_new_user(
            email='new_compiler_2@foo.com',
            last_name='wocat',
            first_name='test3'
        )

        # User (publisher) opens the details of a public questionnaire
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': identifier}
        detail_page.open(login=True, user=self.user_publisher)

        # User (publisher) sees he can neither edit nor change compiler
        assert not detail_page.can_create_new_version()
        assert not detail_page.can_change_compiler()
        assert not detail_page.can_delete_questionnaire()

        # User (secretariat) opens the details of a public questionnaire
        detail_page.route_kwargs = {'identifier': identifier}
        detail_page.open(login=True, user=self.user_secretariat)

        # User (secretariat) can edit and review and assign users
        assert detail_page.can_create_new_version()
        assert detail_page.can_change_compiler()
        assert detail_page.can_delete_questionnaire()

        # The compiler and the editors are correct.
        assert detail_page.get_compiler() == old_compiler.get_display_name()
        assert detail_page.get_editors() == [editor.get_display_name()]

        # User goes to the list view and sees the compiler there
        list_page = SampleListPage(self)
        list_page.open()

        list_results = [
            {
            },
            {
                'title': 'Foo 3',
                'compiler': old_compiler
            }
        ]
        list_page.check_list_results(list_results)

        # User goes back to the questionnaire details
        detail_page.open()
        detail_page.hide_notifications()

        # User changes compiler but does not enter a name
        detail_page.open_change_compiler_panel()
        detail_page.click_change_compiler()

        # No notifications were created
        self.assertEqual(mock_member_change.call_count, 0)
        assert detail_page.has_error_message(
            detail_page.TEXT_MESSAGE_NO_VALID_NEW_COMPILER)
        detail_page.hide_notifications()

        # User selects a new compiler
        detail_page.change_compiler(
            new_compiler_1.get_display_name(), submit=False
        )

        # The new compiler is listed
        assert detail_page.get_selected_compilers() == [
            new_compiler_1.get_display_name()]

        # User confirms and sees a success message
        detail_page.click_change_compiler()
        assert detail_page.has_success_message(
            detail_page.TEXT_MESSAGE_COMPILER_CHANGED)

        # Two notifications were created
        self.assertEqual(mock_member_change.call_count, 2)
        mock_member_change.assert_any_call(
            sender='delete_member',
            questionnaire=Questionnaire.objects.get(code=identifier),
            user=self.user_secretariat,
            affected=old_compiler,
            role='compiler'
        )
        mock_member_change.assert_any_call(
            sender='add_member',
            questionnaire=Questionnaire.objects.get(code=identifier),
            user=self.user_secretariat,
            affected=new_compiler_1,
            role='compiler'
        )
        mock_member_change.reset_mock()

        # The new compiler is visible in the details, editor did not change
        assert detail_page.get_compiler() == new_compiler_1.get_display_name()
        assert detail_page.get_editors() == [editor.get_display_name()]

        # In the list, the new compiler is visible
        list_page.open()
        list_results = [
            {
            },
            {
                'title': 'Foo 3',
                'compiler': new_compiler_1
            }
        ]
        list_page.check_list_results(list_results)

        # In the details page, the user changes the compiler and enters the
        # current compiler once again
        detail_page.open()
        detail_page.hide_notifications()
        detail_page.change_compiler(
            new_compiler_1.get_display_name(), submit=False
        )

        # The compiler is listed
        assert detail_page.get_selected_compilers() == [
            new_compiler_1.get_display_name()]

        # User confirms and sees an error message
        detail_page.click_change_compiler()
        assert detail_page.has_notice_message(
            detail_page.TEXT_MESSAGE_USER_ALREADY_COMPILER)

        # No notifications were created
        self.assertEqual(mock_member_change.call_count, 0)

        # User changes the compiler yet again.
        detail_page.hide_notifications()
        detail_page.change_compiler(
            new_compiler_2.get_display_name(), submit=False)
        assert detail_page.get_selected_compilers() == [
            new_compiler_2.get_display_name()]

        # User sees the search box is now disabled
        assert not detail_page.can_enter_new_compiler()

        # User marks the checkbox which keeps the old compiler as editor
        detail_page.select_keep_compiler_as_editor()

        detail_page.click_change_compiler()
        assert detail_page.has_success_message(
            detail_page.TEXT_MESSAGE_COMPILER_CHANGED)

        # Three notifications were created
        self.assertEqual(mock_member_change.call_count, 3)
        mock_member_change.assert_any_call(
            sender='delete_member',
            questionnaire=Questionnaire.objects.get(code=identifier),
            user=self.user_secretariat,
            affected=new_compiler_1,
            role='compiler'
        )
        mock_member_change.assert_any_call(
            sender='add_member',
            questionnaire=Questionnaire.objects.get(code=identifier),
            user=self.user_secretariat,
            affected=new_compiler_2,
            role='compiler'
        )
        mock_member_change.assert_any_call(
            sender='add_member',
            questionnaire=Questionnaire.objects.get(code=identifier),
            user=self.user_secretariat,
            affected=new_compiler_1,
            role='editor'
        )
        mock_member_change.reset_mock()

        # The new compiler is visible in the details
        assert detail_page.get_compiler() == new_compiler_2.get_display_name()

        # The old compiler is now an editor
        assert new_compiler_1.get_display_name() in detail_page.get_editors()

        list_page.open()
        list_results = [
            {
            },
            {
                'title': 'Foo 3',
                'compiler': new_compiler_2
            }
        ]
        list_page.check_list_results(list_results)

    def test_reviewer_can_edit_questionnaire(self):

        cat_1_position = get_position_of_category('cat_1', start0=True)
        identifier = 'sample_2'

        # The moderator logs in
        self.doLogin(user=self.user_reviewer)

        # He goes to a submitted questionnaire and sees that he can edit
        # the questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_details, kwargs={'identifier': identifier}))
        self.findBy('xpath', '//a[contains(text(), "Edit")]').click()

        # He changes the name and submits the step
        self.hide_notifications()
        self.findManyBy(
            'xpath',
            '//main//a[contains(@href, "edit/{}/cat")]'.format(identifier))[
                cat_1_position].click()
        self.findBy('name', 'qg_1-0-original_key_1').send_keys(' (changed)')
        self.findBy('id', 'button-submit').click()
        self.findBy('xpath', '//div[contains(@class, "success")]')

        # He sees the changes in the overview and submits the questionnaire
        self.findBy('xpath', '//*[text()[contains(.," (changed)")]]')

        # He starts editing again
        # self.findBy('xpath', '//a[contains(text(), "Edit")]').click()

        # He sees there is a message of an old version
        # has_old_version_overview(self)

        # He edits the step again and sees there is now a message of changes
        self.findManyBy(
            'xpath',
            '//main//a[contains(@href, "edit/{}/cat")]'.format(identifier))[
                cat_1_position].click()
        # has_old_version_step(self)
        self.findBy('id', 'button-submit').click()
        self.findBy('xpath', '//div[contains(@class, "success")]')

        # He goes back to the overview and reviews the questionnaire
        self.findBy('xpath', '//span[contains(@class, "is-submitted")]')
        self.review_action('review')
        self.findBy('xpath', '//span[contains(@class, "is-reviewed")]')

    def test_reviewer_can_reject_questionnaire(self):

        identifier = 'sample_2'

        # The reviewer logs in
        self.doLogin(user=self.user_reviewer)

        # He goes to a submitted questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_details, kwargs={'identifier': identifier}))
        self.findBy('xpath', '//span[contains(@class, "is-submitted")]')

        # He sees a button to edit the questionnaire
        self.findBy('xpath', '//a[contains(text(), "Edit")]')

        # He sees that he can reject the questionnaire and so he does
        self.review_action('reject')

        # He sees the reject was successful
        self.findBy('xpath', '//div[contains(@class, "success")]')

        # The reviewer has been taken "home" because he has no
        # permission to view or edit the draft questionnaire
        # route_home
        home_url = self.live_server_url + reverse(route_home)
        self.assertEqual(self.browser.current_url, home_url + '#top')

        # User 102 (the compiler of the questionnaire) logs in
        self.doLogin(user=self.user_editor)

        # He sees the questionnaire and sees it is draft.
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_details, kwargs={'identifier': identifier}))
        self.findBy('xpath', '//span[contains(@class, "is-draft")]')

    def test_publishers_can_edit_questionnaire(self):

        cat_1_position = get_position_of_category('cat_1', start0=True)
        identifier = 'sample_7'

        # The moderator logs in
        self.doLogin(user=self.user_publisher)

        # He goes to a submitted questionnaire and sees that he can edit
        # the questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_details, kwargs={'identifier': identifier}))
        self.findBy('xpath', '//a[contains(text(), "Edit")]').click()

        # He changes the name and submits the step
        self.hide_notifications()
        self.findManyBy(
            'xpath',
            '//a[contains(@href, "edit/{}/cat")]'.format(identifier))[
                cat_1_position].click()
        self.findBy('name', 'qg_1-0-original_key_1').send_keys(' (changed)')
        self.findBy('id', 'button-submit').click()
        self.findBy('xpath', '//div[contains(@class, "success")]')

        # He sees the changes in the overview and submits the questionnaire
        self.findBy('xpath', '//*[text()[contains(.," (changed)")]]')

        # He starts editing again
        # self.findBy('xpath', '//a[contains(text(), "Edit")]').click()

        # He sees there is a message of an old version
        # TODO: Basically, the old version should disappear after a compiler
        # saves it.
        # has_old_version_overview(self)

        # He edits the step again and sees there is now a message of changes
        self.findManyBy(
            'xpath',
            '//a[contains(@href, "edit/{}/cat")]'.format(identifier))[
                cat_1_position].click()
        # has_old_version_step(self)
        self.findBy('id', 'button-submit').click()
        self.findBy('xpath', '//div[contains(@class, "success")]')

        # He goes back to the overview and reviews the questionnaire
        self.findBy('xpath', '//span[contains(@class, "is-reviewed")]')
        self.review_action('publish')

    def test_publisher_can_reject_questionnaire(self):

        identifier = 'sample_7'

        # The reviewer logs in
        self.doLogin(user=self.user_publisher)

        # He goes to a reviewed questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_details, kwargs={'identifier': identifier}))
        self.findBy('xpath', '//span[contains(@class, "is-reviewed")]')

        # He sees a button to edit the questionnaire
        self.findBy('xpath', '//a[contains(text(), "Edit")]')

        # He sees that he can reject the questionnaire and so he does
        self.review_action('reject')

        # The reviewer has been taken "home" because he has no
        # permission to view or edit the draft questionnaire
        # route_home
        home_url = self.live_server_url + reverse(route_home)
        self.assertEqual(self.browser.current_url, home_url + '#top')

        # User 102 (the compiler of the questionnaire) logs in
        self.doLogin(user=self.user_compiler)

        # He sees the questionnaire and sees it is draft.
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_details, kwargs={'identifier': identifier}))
        self.findBy('xpath', '//span[contains(@class, "is-draft")]')
