import os
import sys

from apps.accounts.models import User
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.db.models import Q
from django.test.utils import override_settings
from pyvirtualdisplay import Display
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, \
    WebDriverException
from unittest import skipUnless

import pytest
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from apps.accounts.authentication import WocatCMSAuthenticationBackend
from apps.accounts.client import WocatWebsiteUserClient
from apps.qcat.tests import TEST_CACHES
from unittest.mock import patch
from apps.accounts.tests.test_models import create_new_user

from apps.sample.tests.test_views import route_questionnaire_details as \
    route_questionnaire_details_sample

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth import BACKEND_SESSION_KEY, SESSION_KEY, HASH_SESSION_KEY, get_user_model
from selenium.webdriver.support.ui import Select

loginRouteName = 'accounts:login'


def check_firefox_path():
    """
    Check if a path for Firefox to be used by Selenium is specified in
    the (local) settings.

    Returns:
        ``bool``. Returns ``True`` if the setting
        ``TESTING_FIREFOX_PATH`` is set. Returns ``False`` if the
        setting is not present or empty.
    """
    try:
        if settings.TESTING_FIREFOX_PATH != '':
            return True
    except:
        pass
    return False

# @skipUnless(check_firefox_path(), "Firefox path not specified")
@override_settings(
    CACHES=TEST_CACHES,
    DEBUG=True,
    LANGUAGES=(('en', 'English'), ('es', 'Spanish'), ('fr', 'French')),
)
@pytest.mark.functional
class FunctionalTest(StaticLiveServerTestCase):

    def setUp(self):
        """
        Use FF as browser for functional tests.
        Create a virtual display, so the browser doesn't keep popping up.
        """
        # if '-pop' not in sys.argv[1:] and settings.TESTING_POP_BROWSER is False:
        #     self.display = Display(visible=0, size=(1600, 900))
        #     self.display.start()
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')

        driver = webdriver.Chrome(chrome_options=chrome_options)
        self.browser = driver
        self.browser.implicitly_wait(3)

    def tearDown(self):
        # self.save_failed_screenshots()
        self.browser.quit()
        # if '-pop' not in sys.argv[1:] and settings.TESTING_POP_BROWSER is False:
        #     self.display.stop()

    def save_failed_screenshots(self):
        if self._outcome.errors:
            path = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'failed_screenshots')
            if not os.path.exists(path):
                os.makedirs(path)
            file = os.path.join(path, f'failed_{self.id()}.png')
            self.browser.save_screenshot(file)

    def create_new_user(
            self, email: str='a@b.com', last_name: str='foo',
            first_name: str='bar', groups: list=None) -> User:
        defaults = {
            'firstname': first_name,
            'lastname': last_name
        }
        user, __ = User.objects.get_or_create(email=email, defaults=defaults)

        for group in groups or []:
            # 1. Translators
            # 2. Administrators
            # 3. Reviewers
            # 4. Publishers
            # 5. WOCAT Secretariat
            user.groups.add(Group.objects.get(name=group))

        return user

    def findByNot(self, by, el):
        try:
            self.browser.implicitly_wait(0)
            if by == 'class_name':
                self.browser.find_element_by_class_name(el)
            elif by == 'link_text':
                self.browser.find_element_by_link_text(el)
            elif by == 'name':
                self.browser.find_element_by_name(el)
            elif by == 'xpath':
                self.browser.find_element_by_xpath(el)
            elif by == 'id':
                self.browser.find_element_by_id(el)
            else:
                self.fail('Argument "by" = "%s" is not valid.' % by)
            self.fail('Element %s was found when it should not be' % el)
        except NoSuchElementException:
            pass

    def findBy(self, by, el, base=None, wait=False):
        if base is None:
            base = self.browser
        if wait is True:
            self.wait_for(by, el)
        f = None
        try:
            if by == 'class_name':
                f = base.find_element_by_class_name(el)
            elif by == 'link_text':
                f = base.find_element_by_link_text(el)
            elif by == 'name':
                f = base.find_element_by_name(el)
            elif by == 'xpath':
                f = base.find_element_by_xpath(el)
            elif by == 'id':
                f = base.find_element_by_id(el)
            else:
                self.fail('Argument "by" = "%s" is not valid.' % by)
        except NoSuchElementException:
            self.fail('Element %s was not found by %s' % (el, by))
        return f

    def findManyBy(self, by, el, base=None):
        if base is None:
            base = self.browser
        f = None
        try:
            if by == 'class_name':
                f = base.find_elements_by_class_name(el)
            elif by == 'link_text':
                f = base.find_elements_by_link_text(el)
            elif by == 'name':
                f = base.find_elements_by_name(el)
            elif by == 'xpath':
                f = base.find_elements_by_xpath(el)
            elif by == 'id':
                f = base.find_elements_by_id(el)
            else:
                self.fail('Argument "by" = "%s" is not valid.' % by)
        except NoSuchElementException:
            self.fail('Elements %s were not found by %s' % (el, by))
        return f

    def wait_for(self, by, el, visibility=True):
        if by == 'class_name':
            locator = By.CLASS_NAME
        elif by == 'xpath':
            locator = By.XPATH
        elif by == 'id':
            locator = By.ID
        elif by == 'name':
            locator = By.NAME
        else:
            self.fail('Argument "by" = "%s" is not valid.' % by)

        if visibility is True:
            condition = EC.visibility_of_element_located((locator, el))
        else:
            condition = EC.invisibility_of_element_located((locator, el))

        WebDriverWait(self.browser, 10).until(condition)

    def changeHiddenInput(self, el, val):
        self.browser.execute_script('''
            var elem = arguments[0];
            var value = arguments[1];
            elem.value = value;
        ''', el, val)

    def rearrangeFormHeader(self):
        """
        Use this function to rearrange the fixed header of the form if it is
        blocking certain elements, namely when using headless browser for
        testing. Sets the header to "position: relative".
        """
        try:
            form_header = self.findBy(
                'xpath', '//header[contains(@class, "wizard-header")]')
            self.browser.execute_script(
                'arguments[0].style.position = "relative";', form_header)
        except:
            pass

    def rearrangeStickyMenu(self):
        """
        Use this function to rearrange the fixed sticky menu if it is blocking
        certain elements, namely when using headless browser for testing. Sets
        it to "position: relative".
        """
        pass
        # sticky = self.findBy('class_name', 'sticky-menu-outer')
        # self.browser.execute_script(
        #     'arguments[0].style.position = "absolute";', sticky)

    def rearrange_notifications(self):
        notifications = self.findBy('class_name', 'notification-group')
        self.browser.execute_script(
            'arguments[0].style.position = "relative";', notifications)

    def screenshot(self, filename='screenshot.png'):
        self.browser.save_screenshot(filename)

    def form_click_add_more(self, questiongroup_keyword):
        elm = self.findBy(
            'xpath',
            '//a[@data-add-item and @data-questiongroup-keyword="{}"]'.format(
                questiongroup_keyword))
        self.browser.execute_script("arguments[0].click();", elm)

    def review_action(
            self, action, exists_only=False, exists_not=False,
            expected_msg_class='success'):
        """
        Handle review actions which trigger a modal.

        Args:
            action: One of
                - 'edit'
                - 'view'
                - 'submit'
                ⁻ 'review'
                - 'publish'
                - 'reject'
                - 'flag-unccd'
                - 'unflag-unccd'
            exists_only: Only check that the modal is opened without triggering
              the action.
            expected_msg_class: str.

        Returns:

        """
        if action == 'view':
            btn = self.findBy(
                'xpath', '//form[@id="review_form"]//a[text()="View"]')
            if exists_only is True:
                return btn
            btn.click()
            return
        if exists_not is True:
            self.findByNot(
                'xpath', '//a[@data-reveal-id="confirm-{}"]'.format(action))
            return
        elm = self.findBy(
            'xpath', '//a[@data-reveal-id="confirm-{}"]'.format(action))
        self.browser.execute_script("arguments[0].click();", elm)
        btn_xpath = '//button[@name="{}"]'.format(action)
        if action == 'edit':
            # No button for "edit"
            btn_xpath = '//a[@type="submit"]'
        WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, btn_xpath)))
        if action == 'reject':
            self.findBy('name', 'reject-message').send_keys("spam")

        if exists_only is True:
            self.findBy(
                'xpath', '//div[contains(@class, "reveal-modal") and contains('
                         '@class, "open")]//a[contains(@class, '
                         '"close-reveal-modal")]', wait=True).click()
            import time; time.sleep(1)
            return
        self.wait_for('xpath', btn_xpath)
        # Sometimes, the click on the button in the modal happens too fast
        # (modal not yet correctly displayed), which results in an error saying
        # another (underlying) element would receive the click. In this case,
        # simply try again (hopefully modal showing by now)
        try:
            self.findBy('xpath', btn_xpath).click()
        except WebDriverException:
            self.findBy('xpath', btn_xpath).click()
        self.findBy(
            'xpath', '//div[contains(@class, "{}")]'.format(expected_msg_class))
        if action not in ['reject', 'delete']:
            self.toggle_all_sections()

    def submit_form_step(self):
        elm = self.findBy('id', 'button-submit')
        self.browser.execute_script("arguments[0].click();", elm)

        self.findBy('xpath', '//div[contains(@class, "success")]')
        self.toggle_all_sections()

    def click_edit_section(
            self, section_identifier, return_button=False, exists_not=False):
        btn_xpath = '//a[contains(@href, "/edit/") and contains(@href, "{}")]'.\
            format(section_identifier)
        if exists_not is True:
            self.findByNot('xpath', btn_xpath)
            return

        self.wait_for('xpath', btn_xpath)
        btn = self.findBy('xpath', btn_xpath)
        if return_button is True:
            return btn
        # Clicking does work reliably. Instead opening the URL manually.
        self.browser.get(btn.get_attribute('href'))
        self.rearrangeFormHeader()

    def toggle_all_sections(self):
        self.wait_for('class_name', 'js-expand-all-sections')
        # Remove all notifications so the buttons to expand the sections are
        # clickable
        self.hide_notifications()
        links = self.findManyBy('class_name', 'js-expand-all-sections')
        for link in reversed(links):
            self.browser.execute_script("arguments[0].click();", link)

    def open_questionnaire_details(self, configuration, identifier=None):
        route = route_questionnaire_details_sample
        self.browser.get(self.live_server_url + reverse(
            route, kwargs={'identifier': identifier}))
        self.toggle_all_sections()

    def toggle_selected_advanced_filters(self, display: bool=True) -> None:
        """Toggle the panel with selected advanced filters"""
        filter_panel_xpath = '//div[contains(@class, "selected-advanced-filters")]'
        filter_panel = self.findBy('xpath', filter_panel_xpath)
        if filter_panel.is_displayed() != display:
            self.findBy('xpath',
                        '//a[@data-toggle="js-selected-advanced-filters"]').click()
            self.wait_for('xpath', filter_panel_xpath)

    def open_advanced_filter(self, configuration: str) -> None:
        """
        Assuming that you are on search page, click the link to open the
        advanced filter of a given configuration
        """
        self.findBy('xpath',
                    f'//a[contains(@class, "js-filter-advanced-type") and '
                    f'@data-type="{configuration}"]').click()

    def add_advanced_filter(self, key: str, value: str) -> None:
        """Add a new advanced filter"""

        # Toggle the filter panel if it is not open yet
        self.toggle_selected_advanced_filters(display=True)

        # Select the last <select> available
        filter_row_xpath = '(//div[contains(@class, "selected-advanced-filters")]/div[contains(@class, "js-filter-item")])[last()]'
        filter_row = self.findBy('xpath', filter_row_xpath)
        filter_select_xpath = f'//select[contains(@class, "filter-key-select")]'
        select = Select(self.findBy('xpath', filter_select_xpath, base=filter_row))

        # If it already has a key selected, click "add filter" to add a new row
        # and select the <select> again
        if select.first_selected_option.text != '---':
            self.findBy('id', 'filter-add-new').click()
            filter_row = self.findBy('xpath', filter_row_xpath)
            select = Select(
                self.findBy('xpath', filter_select_xpath, base=filter_row))

        # Select the key, wait for the values to be loaded and select one
        select.select_by_value(key)
        self.wait_for('xpath', filter_row_xpath + '//div[contains(@class, "loading-indicator-filter-key")]', visibility=False)
        self.findBy('xpath', f'//div[contains(@class, "filter-value-column")]//input[@value="{value}"]', base=filter_row).click()
        self.apply_filter()

    def remove_filter(self, index):
        """
        Remove the filter at a given (0-based) index. If index is None, all
        filters are removed!
        """
        curr_index = index
        if curr_index is None:
            curr_index = 0
        self.findBy(
            'xpath',
            f'(//ul[@class="filter-list"]/li/span/a)[{curr_index + 1}]/'
            f'*[contains(@class, "icon")]').click()
        self.wait_for('class_name', 'loading-indicator', visibility=False)
        if index is None:
            try:
                self.remove_filter(index=None)
            except AssertionError:
                pass

    def get_active_filters(self, has_any=None) -> list:
        """
        Return a list of all active filters. If has_any is a boolean, it is
        checked whether there are any active filters or not.
        """
        active_filters = self.findManyBy(
            'xpath', '//div[@id="active-filters"]//li')
        if has_any is not None:
            active_filter_panel = self.findBy(
                'xpath', '//div[@id="active-filters"]/div')
            self.assertEqual(has_any, active_filter_panel.is_displayed())
            if has_any is False:
                self.assertEqual(len(active_filters), 0)
            else:
                self.assertNotEqual(len(active_filters), 0)
        return active_filters

    def apply_filter(self):
        self.findBy(
            'xpath', '//input[contains(@class, "search-submit")]').click()
        self.wait_for('class_name', 'loading-indicator', visibility=False)

    def check_list_results(self, expected: list, count: bool=True):
        """
        Args:
            expected: list of dicts. Can contain
                - title
                - description
                - translations (list)
        """
        if count is True:
            list_entries = self.findManyBy(
                'xpath', '//article[contains(@class, "tech-item")]')
            self.assertEqual(len(list_entries), len(expected))
        for i, e in enumerate(expected):
            i_xpath = i + 1
            if e.get('title') is not None:
                title = e['title']
                self.findBy(
                    'xpath',
                    f'(//article[contains(@class, "tech-item")])[{i_xpath}]//'
                    f'a[contains(text(), "{title}")]')
            if e.get('description'):
                description = e['description']
                self.findBy(
                    'xpath',
                    f'(//article[contains(@class, "tech-item")])[{i_xpath}]//'
                    f'p[contains(text(), "{description}")]')
            if e.get('status'):
                status = e['status']
                xpath = f'(//article[contains(@class, "tech-item")])[{i_xpath}]' \
                        f'//span[contains(@class, "tech-status") and ' \
                        f'contains(@class, "is-{status}")]'
                if status == 'public':
                    self.findByNot('xpath', xpath)
                else:
                    self.findBy('xpath', xpath)
            for lang in e.get('translations', []):
                self.findBy(
                    'xpath',
                    f'(//article[contains(@class, "tech-item")])[{i_xpath}]//'
                    f'a[contains(text(), "{lang}")]')

    def get_compiler(self) -> str:
        """From the details view, return the name of the compiler"""
        return self.findBy(
            'xpath',
            '//ul[@class="tech-infos"]/li/span[text()="Compiler:"]/../a'
        ).text

    def get_editors(self) -> list:
        """From the details view, return the names of the editors"""
        editors = []
        for el in self.findManyBy(
                'xpath',
                '//ul[@class="tech-infos"]/li/span[text()="Editors:"]/../a'):
            editors.append(el.text)
        return editors

    def checkOnPage(self, text):
        xpath = '//*[text()[contains(.,"{}")]]'.format(text)
        WebDriverWait(self.browser, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, xpath)))

    def scroll_to_element(self, el):
        self.browser.execute_script("return arguments[0].scrollIntoView();", el)

    def set_input_value(self, element, value):
        if not isinstance(element, WebElement):
            element = self.findBy('id', element)
        self.browser.execute_script("""
            var element = arguments[0];
                element.setAttribute('value', '{}')
        """.format(value), element)

    def get_text_excluding_children(self, element):
        return self.browser.execute_script("""
        return jQuery(arguments[0]).contents().filter(function() {
            return this.nodeType == Node.TEXT_NODE;
        }).text();
        """, element)

    def hide_notifications(self):
        for el in self.findManyBy(
                'xpath', '//div[contains(@class, "notification alert-box")]'):
            self.browser.execute_script("""
                var element = arguments[0];
                element.parentNode.removeChild(element);
                """, el)

    def select_chosen_element(self, chosen_id: str, chosen_value: str):
        chosen_el = self.findBy('xpath', '//div[@id="{}"]'.format(chosen_id))
        self.browser.execute_script("arguments[0].click();", chosen_el)
        chosen_el = self.findBy('xpath', '//div[@id="{}"]'.format(chosen_id), wait=True)
        print(chosen_el.get_attribute('innerHTML'))
        elm = self.findBy(
            'xpath', '//div[@id="{}"]//ul[@class="chosen-results"]/li[text()='
                     '"{}"]'.format(chosen_id, chosen_value))
        self.browser.execute_script("arguments[0].click();", elm)

    def clickUserMenu(self, user):
        elm = self.findBy(
            'xpath', '//li[contains(@class, "has-dropdown")]/a[contains(text(),'
                     ' "{}")]'.format(user))
        self.browser.execute_script("arguments[0].click();", elm)

    def changeLanguage(self, locale):

        elm = self.findBy(
            'xpath', '//li[contains(@class, "has-dropdown") and contains('
                     '@class, "top-bar-lang")]/a')

        self.browser.execute_script("arguments[0].click();", elm)
        lang_elm = self.findBy('xpath', '//a[@data-language="{}"]'.format(locale))
        self.browser.execute_script("arguments[0].click();", lang_elm)

    def doLogin(self, user=None):
        """
        A user is required for the login, this is a convenience wrapper to
        login a non-specified user.
        """
        self.doLogout()
        self._doLogin(user or create_new_user())

    @patch.object(WocatCMSAuthenticationBackend, 'authenticate')
    @patch.object(WocatWebsiteUserClient, 'get_and_update_django_user')
    @patch('django.contrib.auth.authenticate')
    def _doLogin(self, user, mock_authenticate,
                 mock_cms_get_and_update_django_user, mock_cms_authenticate):
        """
        Mock the authentication to return the given user and put it to the
        session - django.contrib.auth.login handles this.
        Set the cookie so the custom middleware doesn't force-validate the login
        against the login API.
        """

        session = SessionStore()
        session[SESSION_KEY] = user.pk
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()

        self.browser.get(self.live_server_url + "/404_no_such_url/")
        self.browser.add_cookie(dict(
            name=settings.SESSION_COOKIE_NAME,
            value=session.session_key,
            path='/',
            secure=False,
            httpOnly=True
        ))

        self.browser.get(self.live_server_url + reverse(loginRouteName))

    def doLogout(self):
        try:
            elm = self.browser.find_element_by_xpath(
                '//li[contains(@class, "user-menu")]/a')
            self.browser.execute_script("arguments[0].click();", elm)
            elm = self.browser.find_element_by_xpath(
                '//ul[@class="dropdown"]/li/a[contains(@href, "/accounts/logout/")]')
            self.browser.execute_script("arguments[0].click();", elm)
        except NoSuchElementException:
            pass
        self.browser.delete_cookie('fe_typo_user')
        self.browser.get(self.live_server_url + '/404_no_such_url/')

    def get_mock_remote_user_client_search(self, name):
        """
        Simulate a response from the remote auth provider when searching for a
        user. Searches in the local database instead and returns all users
        matching the query (case insensitve search by first or last name).

        Usually, you will want to use this in combination with
        get_mock_remote_user_client_user_information (see below) to also
        correctly update the user in the database (e.g. when changing compiler
        or adding reviewer)

        Usage in tests:
        Patch the remote client's search_users function in the view and set this
        function as side_effect. Similar with remote client's
        get_user_information.

        Example:
            @patch('questionnaire.utils.remote_user_client.get_user_information')
            @patch('accounts.views.remote_user_client.search_users')
            def test_something(self, mock_search_users, mock_user_information):
                mock_search_users.side_effect = self.get_mock_remote_user_client_search
                mock_user_information.side_effect = self.get_mock_remote_user_client_user_information
                # ...
        """
        users = User.objects.filter(
            Q(firstname__icontains=name) | Q(lastname__icontains=name))
        return {
            'success': True,
            'users': [
                self._mock_remote_client_user_details(user)
                for user in users
            ]
        }

    def get_mock_remote_user_client_user_information(self, user_id):
        """
        Simulate a response from the remote auth provider when retrieving the
        user details needed to update the user. Searches in the local database
        instead (lookup by ID).

        Usually, you will want to use this in combination with
        get_mock_remote_user_client_search (see above).

        Usage in tests:
        Patch the remote client's get_user_information function where it is used
        (e.g. in questionnaire.utils when changing users of a questionnaire) and
        set this function as side_effect. Similar with remote client's
        search_users.

        Example:
            @patch('questionnaire.utils.remote_user_client.get_user_information')
            @patch('accounts.views.remote_user_client.search_users')
            def test_something(self, mock_search_users, mock_user_information):
                mock_search_users.side_effect = self.get_mock_remote_user_client_search
                mock_user_information.side_effect = self.get_mock_remote_user_client_user_information
                # ...
        """
        user = User.objects.get(pk=user_id)
        return self._mock_remote_client_user_details(user)

    def _mock_remote_client_user_details(self, user):
        # Helper to format the user details similar to the remote client's
        # reponse.
        return {
            'uid': user.pk,
            'username': user.email,
            'email': user.email,
            'first_name': user.firstname,
            'last_name': user.lastname,
        }

    def dropImage(self, dropzone_id):
        self.browser.execute_script(
            "function base64toBlob(b64Data, contentType, sliceSize) "
            "{contentType = contentType || '';sliceSize = sliceSize || 512;"
            "var byteCharacters = atob(b64Data);var byteArrays = [];for (var "
            "offset = 0; offset < byteCharacters.length; offset += sliceSize) "
            "{var slice = byteCharacters.slice(offset, offset + sliceSize);"
            "var byteNumbers = new Array(slice.length);for (var i = 0; i < "
            "slice.length; i++) {byteNumbers[i] = slice.charCodeAt(i);}var "
            "byteArray = new Uint8Array(byteNumbers);byteArrays.push("
            "byteArray);}var blob = new Blob(byteArrays, {type: "
            "contentType});return blob;}var base64Image = "
            "'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"
            "pCZbEhAAOw==';var dz = Dropzone.forElement('#%s'); dz.addFile("
            "base64toBlob(base64Image, 'image/gif'));" % dropzone_id)
        # Wait for preview image
        self.wait_for(
            'xpath',
            f'//div[@id="preview-{dropzone_id}"]/div[@class="image-preview"]/img')
