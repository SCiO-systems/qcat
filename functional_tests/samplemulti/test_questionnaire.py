import pytest
from elasticmock import elasticmock

from functional_tests.base import FunctionalTest
from functional_tests.pages.questionnaire import QuestionnaireStepPage
from functional_tests.pages.samplemulti import SamplemultiNewPage, \
    SampleMultiStepPage


@elasticmock
class QuestionnaireTest(FunctionalTest):

    fixtures = [
        'global_key_values',
        'samplemulti',
    ]

    def test_questionnaire_is_available(self):

        # User logs in and goes to the SAMPLEMULTI edit page.
        edit_page = SamplemultiNewPage(self)
        edit_page.open(login=True)

        # User sees an empty edit page and the categories of the SAMPLEMULTI.
        progress_indicators = edit_page.get_progress_indicators()
        categories = edit_page.CATEGORIES
        assert len(progress_indicators) == len(categories)

        # All the categories are listed.
        for __, category in categories:
            edit_page.get_category_by_name(category)

        # User edits the first category.
        edit_page.click_edit_category(categories[0][0])

        # User saves the first category.
        step_page = QuestionnaireStepPage(self)
        step_page.submit_step()

        # All the categories are still there.
        progress_indicators = edit_page.get_progress_indicators()
        categories = edit_page.CATEGORIES
        assert len(progress_indicators) == len(categories)
        for __, category in categories:
            edit_page.get_category_by_name(category)

    def test_questionnaire_can_be_entered(self):

        # User logs in and goes to the SAMPLEMULTI edit page.
        edit_page = SamplemultiNewPage(self)
        edit_page.open(login=True)

        # User edits first category and enters some data.
        edit_page.click_edit_category('mcat_1')
        step_page = SampleMultiStepPage(self)
        step_page.enter_text(step_page.LOC_QUESTION_MQG01_MKEY01, 'Foo')

        # User saves step.
        step_page.submit_step()

        # User sees the entered data is there.
        edit_page.has_text('MKey 1')
        edit_page.has_text('Foo')

        # User submits the questionnaire and sees the data is still there.
        edit_page.submit_questionnaire()
        edit_page.has_text('MKey 1')
        edit_page.has_text('Foo')
