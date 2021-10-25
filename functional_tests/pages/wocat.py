from selenium.webdriver.common.by import By

from functional_tests.pages.base import QcatPage
from functional_tests.pages.mixins import ListMixin


class ListPage(ListMixin, QcatPage):
    route_name = 'wocat:questionnaire_list'


class AddDataPage(QcatPage):
    route_name = 'wocat:add'

    LOC_BUTTON_ADD_SLM_DATA = (
        By.XPATH, '//div[contains(@class, "card")]//a['
                  'contains(@href, "/technologies/edit/new")]')

    def click_add_technology(self):
        self.get_el(self.LOC_BUTTON_ADD_SLM_DATA).click()
