from django.urls import reverse
from django.contrib.auth.models import Group

from functional_tests.base import FunctionalTest
from apps.accounts.models import User
from apps.accounts.tests.test_models import create_new_user
from apps.accounts.tests.test_views import accounts_route_questionnaires


# @patch('wocat.views.generic_questionnaire_list')
# @patch.object(WocatAuthenticationBackend, 'authenticate')
# class LoginTest(FunctionalTest):
#
#     def test_login(
#             self, mock_authenticate, mock_get_user_id, mock_get_and_update,
#             mock_questionnaire_list
#     ):
#
#         user = create_new_user()
#
#         mock_get_and_update.return_value = user
#         mock_authenticate.return_value = None
#         mock_authenticate.__name__ = ''
#         mock_get_user_id.return_value = user.id
#         mock_questionnaire_list.return_value = {}
#
#         # Alice opens her web browser and goes to the home page
#         self.browser.get(self.live_server_url)
#
#         # She sees the top navigation bar with the login button, on which she
#         # clicks.
#         navbar = self.findBy('class_name', 'top-bar')
#         navbar.find_element_by_link_text('Login').click()
#
#         # She tries to submit the form empty and sees that the form was
#         # not submitted.
#         self.findBy('id', 'button_login').click()
#         self.findBy('name', 'username')
#
#         # She enters some (wrong) user credentials
#         self.findBy('name', 'username').send_keys('wrong@user.com')
#         self.findBy('name', 'password').send_keys('wrong')
#
#         # She tries to submit the form and sees an error message
#         self.findBy('id', 'button_login').click()
#         self.checkOnPage('Please enter a correct email address and password.')
#
#         mock_authenticate.return_value = user
#         self.browser.add_cookie({'name': 'fe_typo_user', 'value': 'session_id'})
#
#         # She enters some (correct) user credentials
#         self.findBy('name', 'password').send_keys('correct')
#         self.findBy('id', 'button_login').click()
#
#         # She sees that she was redirected to the landing page
#         self.assertEqual(self.browser.current_url,
#                          self.live_server_url + reverse('wocat:home'))
#         self.checkOnPage(user.get_display_name())
#         self.checkOnPage('Logout')


class UserTest(FunctionalTest):

    fixtures = [
        'groups_permissions',
    ]

    def test_superusers(self):

        user = create_new_user()
        user.is_superuser = True
        user.save()

        self.doLogin(user)

        # Superusers see the link to the administration
        self.findBy(
            'xpath', '//ul[@class="dropdown"]/li/a[@href="/admin/"]')

        # Superusers see the link to the Dashboard
        self.findBy(
            'xpath', '//ul[@class="dropdown"]/li/a[contains(@href, "search/'
            'admin")]')

    def test_administrators(self):

        user = create_new_user()
        user.groups.set([Group.objects.get(pk=1)])

        self.doLogin(user)

        # Administrators see the link to the administration
        self.findBy(
            'xpath', '//ul[@class="dropdown"]/li/a[@href="/admin/"]')

        # Administrators do not see the link to the Dashboard
        self.findByNot(
            'xpath', '//ul[@class="dropdown"]/li/a[contains(@href, "search/'
            'admin")]')

    def test_moderators(self):

        user = create_new_user()
        user.groups = [Group.objects.get(pk=3)]

        self.doLogin(user)

        # Moderators do not see the link to the administration
        self.findByNot(
            'xpath', '//ul[@class="dropdown"]/li/a[@href="/admin/"]')

        # Moderators do not see the link to the Dashboard
        self.findByNot(
            'xpath', '//ul[@class="dropdown"]/li/a[contains(@href, "search/'
            'admin")]')

    def test_translators(self):

        user = create_new_user()
        user.groups.set([Group.objects.get(pk=2)])

        self.doLogin(user)

        # Translators see the link to the administration
        self.findBy(
            'xpath', '//ul[@class="dropdown"]/li/a[@href="/admin/"]')

        # Translators do not see the link to the Dashboard
        self.findByNot(
            'xpath', '//ul[@class="dropdown"]/li/a[contains(@href, "search/'
            'admin")]')

# @patch('accounts.authentication.WocatAuthenticationBackend._do_auth')
# class LogoutTest(FunctionalTest):

#     def test_logout(self, mock_do_auth):

#         mock_do_auth.return_value = ('tempsessionid')

#         # Alice logs in
#         self.doLogin('a@b.com', 'foo')

#         # She sees a logout button in the top navigation bar and clicks on it
#         navbar = self.findBy('class_name', 'top-bar')
#         navbar.find_element_by_link_text('Logout').click()

#         # She notices she was redirected to the home page and is now logged
#         # out (the top bar showing a login button)
#         self.assertEqual(self.browser.current_url, self.live_server_url + '/')
#         navbar = self.findBy('class_name', 'top-bar')
#         navbar.find_element_by_link_text('Login')


class ModerationTest(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'global_key_values',
        'sample',
        'sample_questionnaire_status',
        'sample_user',
    ]

    def test_user_questionnaires(self):

        user_alice = User.objects.get(pk=101)
        user_moderator = User.objects.get(pk=103)
        user_secretariat = User.objects.get(pk=107)

        # Alice logs in
        self.doLogin(user=user_alice)

        # She logs in as moderator and sees that she can access the view
        self.doLogin(user=user_moderator)
        self.browser.get(self.live_server_url + reverse(
            accounts_route_questionnaires))
        self.wait_for(
            'xpath', '//img[@src="/static/assets/img/ajax-loader.gif"]',
            visibility=False)

        # She sees all the Questionnaires which are submitted plus the one where
        # he is compiler
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
                     'contains(text(), "Foo 6")]',
            wait=True)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[2]//a['
            'contains(text(), "Foo 2")]',
            wait=True)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[3]//a['
            'contains(text(), "Foo 8")]',
            wait=True)
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 3)

        # He logs in as WOCAT secretariat
        self.doLogin(user=user_secretariat)
        self.browser.get(self.live_server_url + reverse(
            accounts_route_questionnaires))
        self.wait_for(
            'xpath', '//img[@src="/static/assets/img/ajax-loader.gif"]',
            visibility=False)

        # She sees all the Questionnaires (2 drafts, 2 submitted, 2 reviewed and
        # 1 rejected)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[1]//a['
                     'contains(text(), "Foo 1")]',
            wait=True)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[2]//a['
                     'contains(text(), "Foo 6")]',
            wait=True)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[3]//a['
                     'contains(text(), "Foo 2")]',
            wait=True)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[4]//a['
                     'contains(text(), "Foo 8")]',
            wait=True)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[5]//a['
                     'contains(text(), "Foo 7")]',
            wait=True)
        self.findBy(
            'xpath', '(//article[contains(@class, "tech-item")])[6]//a['
                     'contains(text(), "Foo 9")]',
            wait=True)
        list_entries = self.findManyBy(
            'xpath', '//article[contains(@class, "tech-item")]')
        self.assertEqual(len(list_entries), 6)
