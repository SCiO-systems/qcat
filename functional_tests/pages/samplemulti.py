from selenium.webdriver.common.by import By

from functional_tests.pages.base import QcatPage
from functional_tests.pages.mixins import EditMixin, DetailMixin
from functional_tests.pages.questionnaire import QuestionnaireStepPage


class Samplemulti2015Mixin:
    CATEGORIES = [
        ('mcat_1', 'MCategory 1'),
    ]
    TEXT_SAMPLE_LINKS_SUBCATEGORY = 'MSubcategory 1_2 (links)'


class SamplemultiNewPage(Samplemulti2015Mixin, EditMixin, QcatPage):
    route_name = 'samplemulti:questionnaire_new'


class SampleMultiStepPage(QuestionnaireStepPage):
    LOC_QUESTION_MQG01_MKEY01 = (By.NAME, 'mqg_01-0-original_mkey_01')
    LOC_FORM_INPUT_SAMPLE_LINK_ID = (By.NAME, 'mqg_02__sample-0-link_id')  # mcat_1


class SampleMultiDetailPage(Samplemulti2015Mixin, DetailMixin, QcatPage):
    route_name = 'samplemulti:questionnaire_details'


class SampleMultiEditPage(Samplemulti2015Mixin, EditMixin, QcatPage):
    route_name = 'samplemulti:questionnaire_edit'
