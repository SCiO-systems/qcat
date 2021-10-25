from selenium.webdriver.common.by import By

from functional_tests.pages.base import QcatPage
from functional_tests.pages.mixins import EditMixin, DetailMixin, ListMixin
from functional_tests.pages.questionnaire import QuestionnaireStepPage


class Sample2015Mixin:
    CATEGORIES = [
        ('cat_0', 'Category 0'),
        ('cat_1', 'Category 1'),
        ('cat_2', 'Category 2'),
        ('cat_3', 'Category 3'),
        ('cat_4', 'Category 4'),
        ('cat_5', 'Category 5'),
    ]
    TEXT_SAMPLEMULTI_LINKS_SUBCATEGORY = 'Subcategory 5_3 (links)'


class SampleNewPage(Sample2015Mixin, EditMixin, QcatPage):
    route_name = 'sample:questionnaire_new'

    def create_new_questionnaire(self, **kwargs):
        step_page = SampleStepPage(self.test_case)

        def _enter_text_fields(keys: list):
            for text_key in keys:
                if text_key in kwargs:
                    locator = getattr(
                        step_page, f'LOC_FORM_INPUT_{text_key.upper()}')
                    step_page.enter_text(locator, kwargs[text_key])

        if {'key_1', 'key_3'}.intersection(kwargs.keys()):
            self.click_edit_category('cat_1')
            _enter_text_fields(['key_1', 'key_3'])

        step_page.submit_step()


class SampleStepPage(QuestionnaireStepPage):
    LOC_FORM_INPUT_KEY_1 = (By.NAME, 'qg_1-0-original_key_1')
    LOC_FORM_INPUT_KEY_3 = (By.NAME, 'qg_1-0-original_key_3')
    LOC_FORM_INPUT_KEY_5 = (By.NAME, 'qg_19-0-original_key_5')  # cat_2
    LOC_FORM_INPUT_KEY_68 = (By.NAME, 'qg_12-0-original_key_68')
    LOC_FORM_INPUT_SAMPLEMULTI_LINK_ID = (
        By.NAME, 'qg_33__samplemulti-0-link_id')  # cat_5
    LOC_FORM_INPUT_USER_ID = (By.NAME, 'qg_31-0-key_39')  # cat_0

    def get_selected_user_id(self):
        return self.get_value(self.get_el(self.LOC_FORM_INPUT_USER_ID))


class SampleEditPage(Sample2015Mixin, EditMixin, QcatPage):
    route_name = 'sample:questionnaire_edit'


class SampleDetailPage(Sample2015Mixin, DetailMixin, QcatPage):
    route_name = 'sample:questionnaire_details'


class SampleListPage(ListMixin, QcatPage):
    route_name = 'sample:questionnaire_list'
