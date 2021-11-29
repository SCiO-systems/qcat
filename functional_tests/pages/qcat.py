from collections import namedtuple

from selenium.webdriver.common.by import By

from functional_tests.pages.base import QcatPage
from functional_tests.pages.mixins import PaginationMixin, ListMixin


class HomePage(QcatPage):
    route_name = 'home'


class MyDataPage(PaginationMixin, ListMixin, QcatPage):
    route_name = 'accounts:account_questionnaires'

    LOC_LOGS = (By.XPATH, '//div[(contains(@class, "notification-list") and '
                          'not(contains(@class, "header")))]')
    LOC_LOGS_CONTAINER = (By.ID, 'latest-notification-updates')
    LOC_LOG_ENTRY_CHECKBOX_READ = (
        By.XPATH, '//div[contains(@class, "notification-list") and not('
                  'contains(@class, "header"))][{index}]//input['
                  '@class="mark-done"]')
    LOC_LOG_ENTRY_IS_READ = (
        By.XPATH, '//div[contains(@class, "notification-list") and not(contains'
                  '(@class, "header"))][{index}][contains(@class, "is-read")]')
    LOC_LOG_ENTRY_IS_UNREAD = (
        By.XPATH, '//div[contains(@class, "notification-list") and not(contains'
                  '(@class, "header"))][{index}][not('
                  'contains(@class, "is-read"))]')
    LOC_LOG_ENTRY_TODO = (
        By.XPATH, '//div[contains(@class, "log-todo")]')  # Relative to LOC_LOGS
    TEXT_NO_NOTIFICATIONS = 'No notifications.'
    CLASS_LOG_ENTRY_IS_READ = 'is-read'
    STYLE_LOG_ENTRY_IS_TODO = 'visibility: visible;'

    def get_logs(self) -> list:
        LogEntry = namedtuple('LogEntry', 'text, is_read, is_todo')
        logs = []
        for el in self.get_els(self.LOC_LOGS):
            is_read = self.CLASS_LOG_ENTRY_IS_READ in el.get_attribute('class')
            is_todo = self.STYLE_LOG_ENTRY_IS_TODO in self.get_el(
                self.LOC_LOG_ENTRY_TODO, base=el).get_attribute('style')
            logs.append(LogEntry(
                text=el.text,
                is_read=is_read,
                is_todo=is_todo
            ))
        return logs

    def mark_read(self, index: int):
        elm = self.get_el(
            self.format_locator(self.LOC_LOG_ENTRY_CHECKBOX_READ, index=index+1)
        )
        self.browser.execute_script("arguments[0].click();", elm)

    def wait_marked_read(self, index: int, is_read: bool):
        if is_read is True:
            loc = self.LOC_LOG_ENTRY_IS_READ
        else:
            loc = self.LOC_LOG_ENTRY_IS_UNREAD
        self.wait_for(self.format_locator(loc, index=index+1))

    def has_no_notifications(self) -> bool:
        return self.TEXT_NO_NOTIFICATIONS in self.get_el(
            self.LOC_LOGS_CONTAINER).text

    def wait_for_lists(self):
        self.wait_for(self.LOC_LOADING_INDICATOR, visibility=False)
