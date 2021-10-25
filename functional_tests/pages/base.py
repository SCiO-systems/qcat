from urllib.parse import urlparse, parse_qs, urlencode

from apps.accounts.models import User
from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from functional_tests.base import FunctionalTest


class Page:
    route_kwargs = {}

    @property
    def route_name(self):
        raise NotImplementedError

    def __init__(self, test_case: FunctionalTest):
        self.test_case = test_case
        self.browser = test_case.browser

    def format_locator(self, locator, **kwargs):
        return (
            locator[0],
            locator[1].format(**kwargs),
        )

    def get_url(self):
        return self.test_case.live_server_url + reverse(
            self.route_name, kwargs=self.route_kwargs)

    def open(self, query_dict: dict=None, login: bool=False, user: User=None):
        if login is True:
            self.test_case.doLogin(user=user)
        url = self.get_url()
        if query_dict:
            url = f'{url}?{self.get_query_string(query_dict)}'
        self.browser.get(url)

    def get_el(self, locator: tuple, base: WebElement=None) -> WebElement:
        """
        Shortcut to get an element.
        """
        if base is None:
            base = self.browser
        return base.find_element(*locator)

    def get_els(self, locator: tuple) -> list:
        """
        Shortcut to get multiple elements
        """
        return self.browser.find_elements(*locator)

    def exists_el(self, locator: tuple) -> bool:
        """
        Check whether an element exists or not.
        """
        try:
            self.browser.find_element(*locator)
        except NoSuchElementException:
            return False
        return True

    def wait_for(self, locator: tuple, visibility: bool=True):
        if visibility is True:
            condition = expected_conditions.visibility_of_element_located(
                locator)
        else:
            condition = expected_conditions.invisibility_of_element_located(
                locator)
        WebDriverWait(self.browser, 10).until(condition)

    def scroll_to_element(self, element: WebElement):
        self.browser.execute_script(
            'return arguments[0].scrollIntoView();', element)

    @staticmethod
    def get_value(element: WebElement) -> str:
        return element.get_attribute('value')

    def set_value(self, element: WebElement, value: str):
        self.browser.execute_script('''
            var elem = arguments[0];
            var value = arguments[1];
            elem.value = value;
        ''', element, value)

    def hide_element(self, element: WebElement):
        self.browser.execute_script('''
            arguments[0].style.visibility='hidden';
        ''', element)

    def show_element(self, element: WebElement):
        self.browser.execute_script('''
            arguments[0].style.display='block';
        ''', element)

    def has_text(self, text):
        return text in self.browser.page_source

    def get_query_dict(self) -> dict:
        """ Return the query string of the current url as dict. """
        return parse_qs(urlparse(self.browser.current_url).query)

    @staticmethod
    def get_query_string(query_dict: dict) -> str:
        """ Return the query string based on a dict. """
        return urlencode(query_dict, doseq=True)

    def select_chosen(self, locator: tuple, value: str):
        # Locator needs to be an xpath!
        el = self.get_el(locator)
        self.scroll_to_element(el)
        el.click()
        value_locator = (
            By.XPATH,
            f'{locator[1]}//ul[@class="chosen-results"]/li[text()="{value}"]'
        )
        self.get_el(value_locator).click()

    def select_autocomplete(self, value: str):
        # Jquery UI Autocomplete
        self.wait_for((By.CLASS_NAME, 'ui-menu-item'))
        value_locator = (
            By.XPATH,
            f'//li[@class="ui-menu-item"]//*[contains(text(), "{value}")]')
        self.get_el(value_locator).click()


class QcatPage(Page):
    LOC_MENU_LANGUAGE_SWITCHER = (
        By.XPATH, '//li[contains(@class, "top-bar-lang")]/a')
    LOC_MENU_LANGUAGE_ENTRY = (
        By.XPATH, '//li[contains(@class, "top-bar-lang")]//li/'
                  'a[@data-language="{locale}"]')
    LOC_MENU_ADD_SLM_DATA = (
        By.XPATH, '//section[contains(@class, "top-bar-section")]//a[contains('
                  '@href, "/wocat/add")]')
    LOC_MENU_USER = (By.XPATH, '//li[contains(@class, "user-menu")]/a')
    LOC_MENU_USER_LOGOUT = (
        By.XPATH, '//ul[@class="dropdown"]/li/a[contains(@href, '
                  '"/accounts/logout/")]')
    LOC_SUCCESS_MESSAGE = (By.XPATH, '//div[contains(@class, "success")]')
    LOC_MESSAGE_WITH_TEXT = (
        By.XPATH, '//div[contains(@class, "notification-group")]/div[contains('
                  '@class, "{cls}") and text()="{msg}"]')
    LOC_NOTIFICATIONS_CONTAINER = (By.CLASS_NAME, 'notification-group')
    LOC_UNREAD_MESSAGES = (By.CLASS_NAME, 'has-unread-messages')
    LOC_MODAL_OPEN = (
        By.XPATH, '//div[contains(@class, "reveal-modal") and contains(@class, '
                  '"open") and contains(@style, "opacity: 1")]')

    def change_language(self, locale):
        self.get_el(self.LOC_MENU_LANGUAGE_SWITCHER).click()
        locator = self.format_locator(
            self.LOC_MENU_LANGUAGE_ENTRY, locale=locale)
        self.get_el(locator).click()

    def click_add_slm_data(self):
        self.get_el(self.LOC_MENU_ADD_SLM_DATA).click()

    def has_success_message(self, msg: str='') -> bool:
        if msg:
            return self.exists_el(
                self.format_locator(
                    self.LOC_MESSAGE_WITH_TEXT, cls='success', msg=msg))
        return self.exists_el(self.LOC_SUCCESS_MESSAGE)

    def has_error_message(self, msg: str) -> bool:
        return self.exists_el(
            self.format_locator(
                self.LOC_MESSAGE_WITH_TEXT, cls='error', msg=msg))

    def has_warning_message(self, msg: str) -> bool:
        return self.exists_el(
            self.format_locator(
                self.LOC_MESSAGE_WITH_TEXT, cls='warning', msg=msg))

    def has_notice_message(self, msg: str) -> bool:
        return self.exists_el(
            self.format_locator(
                self.LOC_MESSAGE_WITH_TEXT, cls='secondary', msg=msg))

    def hide_notifications(self):
        # Actually, there is only one notification container. But it might not
        # always be there, therefore using get_els which does not fail if it
        # does not exist.
        for el in self.get_els(self.LOC_NOTIFICATIONS_CONTAINER):
            self.hide_element(el)

    def has_unread_messages(self) -> bool:
        return self.exists_el(self.LOC_UNREAD_MESSAGES)

    def logout(self):
        self.get_el(self.LOC_MENU_USER).click()
        self.get_el(self.LOC_MENU_USER_LOGOUT).click()

    def wait_for_modal(self, visibility: bool=True):
        self.wait_for(self.LOC_MODAL_OPEN, visibility=visibility)

    def is_not_found_404(self) -> bool:
        return self.has_text('404') and self.has_text('ot found')


class ApiPage(Page):

    def open(self, output_format: str='json', **kwargs):
        """ Open API page with format 'json' by default. """
        query_dict = kwargs.pop('query_dict', {})
        query_dict['format'] = [output_format]
        kwargs['query_dict'] = query_dict
        super().open(**kwargs)
