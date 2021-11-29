from functional_tests.base import FunctionalTest
from selenium.common.exceptions import NoSuchElementException
from django.contrib.auth.models import Group
from webdriver_manager.chrome import ChromeDriverManager

from apps.accounts.tests.test_models import create_new_user


class AdminTest(FunctionalTest):

    fixtures = [
        'groups_permissions',
    ]

    def setUp(self):
        super(AdminTest, self).setUp()
        user = create_new_user()
        user.is_superuser = True
        user.save()
        self.user = user

    def test_admin_page_superuser(self):
        return
        # Alice logs in
        self.doLogin(user=self.user)

        # She sees the admin button in the top navigation bar and clicks on it
        self.clickUserMenu(self.user)
        navbar = self.findBy('class_name', 'top-bar')
        elm = navbar.find_element_by_link_text('Search Index Administration')
        self.browser.execute_script("arguments[0].click();", elm)
        print(self.browser.page_source)

        column_1 = self.findBy('id', 'column_1')

        user_module = self.findBy('id', 'module_1', base=column_1)
        user_module.find_element_by_link_text('Users')
        configurations_module = self.findBy('id', 'module_3', base=column_1)
        configurations_module.find_element_by_link_text('Projects')
        with self.assertRaises(NoSuchElementException):
            column_1.find_element_by_id('module_6')
            column_1.find_element_by_id('module_7')

    def test_admin_page_translators(self):
        return

        user = create_new_user(id=2, email='foo@bar.com')
        user.groups.add(Group.objects.filter(name='Translators').first())
        user.save()

        # Alice logs in
        self.doLogin(user=user)

        # She sees the admin button in the top navigation bar and clicks on it
        self.clickUserMenu(user)
        navbar = self.findBy('class_name', 'top-bar')
        navbar.find_element_by_link_text('Administration').click()

        column_1 = self.findBy('id', 'column_1')
        with self.assertRaises(NoSuchElementException):
            column_1.find_element_by_id('module_2')
            column_1.find_element_by_id('module_6')

    def test_admin_page_wocat_secretariat(self):
        return
        user = create_new_user(id=2, email='foo@bar.com')
        user.groups.add(Group.objects.filter(name='WOCAT Secretariat').first())
        user.save()

        # Alice logs in
        self.doLogin(user=user)

        # She sees the admin button in the top navigation bar and clicks on it
        self.clickUserMenu(user)
        navbar = self.findBy('class_name', 'top-bar')
        navbar.find_element_by_link_text('Administration').click()

        # She sees that she can edit projects in the admin section
        self.findBy('xpath', '//h2[contains(text(), "Configuration")]')
        self.findBy('xpath', '//strong[contains(text(), "Projects")]')

        # She clicks to add a new project and sees that she can edit the ID as
        # well
        self.findBy('xpath', '//a[contains(@href, "/admin/configuration/project'
                             '/add/")]').click()

        textfields = self.findManyBy('xpath', '//input[@type="text"]')
        self.assertEqual(len(textfields), 2)

        # She goes back to the admin page
        self.browser.execute_script("window.history.go(-1)")

        # She can no longer edit institutions (they are managed in the CMS)
        self.findByNot('xpath', '//strong[contains(text(), "Institutions")]')
