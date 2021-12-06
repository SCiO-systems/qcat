from selenium.webdriver.common.by import By

from functional_tests.pages.base import QcatPage
from functional_tests.pages.mixins import EditMixin, DetailMixin
from functional_tests.pages.questionnaire import QuestionnaireStepPage


class Technologies2015Mixin:
    CATEGORIES = [
        ('tech__1', 'General information'),
        ('tech__2', 'Description of the SLM Technology'),
        ('tech__3', 'Classification of the SLM Technology'),
        ('tech__4', 'Technical specifications, implementation activities, '
                    'inputs, and costs'),
        ('tech__5', 'Natural and human environment'),
        ('tech__6', 'Impacts and concluding statements'),
        ('tech__7', 'References and links'),
    ]

    CATEGORIES_TRANSLATED = [
        ('tech__1', 'Información general'),
        # Not all categories needed. Used only to check if translation is shown.
    ]


class Technologies2018Mixin(Technologies2015Mixin):
    # So far, not many differences to edition 2015.
    pass


class TechnologiesNewPage(Technologies2015Mixin, EditMixin, QcatPage):
    route_name = 'technologies:questionnaire_new'


class Technologies2018NewPage(Technologies2018Mixin, EditMixin, QcatPage):
    route_name = 'technologies:questionnaire_new'

    LOC_MODAL_EDITION_2018_WARNING = (
        By.ID, 'modal-technologies-edition-2018-note')
    LOC_BUTTON_CLOSE_MODAL_EDITION_2018_WARNING = (
        By.CLASS_NAME, 'close-modal-technologies-edition-2018-note')

    def has_updated_edition_warning(self):
        return self.exists_el(self.LOC_MODAL_EDITION_2018_WARNING)

    def close_updated_edition_warning(self):
        elm = self.get_el(self.LOC_BUTTON_CLOSE_MODAL_EDITION_2018_WARNING)
        self.browser.execute_script("arguments[0].click();", elm)


class TechnologiesEditPage(Technologies2018Mixin, EditMixin, QcatPage):
    route_name = 'technologies:questionnaire_edit'


class TechnologiesDetailPage(Technologies2015Mixin, DetailMixin, QcatPage):
    route_name = 'technologies:questionnaire_details'


class TechnologiesStepPage(QuestionnaireStepPage):
    route_name = 'technologies:questionnaire_new_step'
