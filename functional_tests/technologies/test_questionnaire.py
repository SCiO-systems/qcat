from django.contrib.auth import get_user_model
from apps.questionnaire.models import Questionnaire

from functional_tests.base import FunctionalTest
from functional_tests.pages.qcat import HomePage
from functional_tests.pages.questionnaire import QuestionnaireStepPage
from functional_tests.pages.technologies import TechnologiesNewPage, \
    Technologies2018NewPage, TechnologiesDetailPage, TechnologiesEditPage, \
    TechnologiesStepPage
from functional_tests.pages.wocat import AddDataPage


class QuestionnaireTest(FunctionalTest):

    fixtures = [
        'global_key_values',
        'technologies',
    ]

    def test_questionnaire_is_available(self):

        # User logs in and goes to the home page.
        home_page = HomePage(self)
        home_page.open(login=True)

        # User clicks a link to add data in the top menu.
        home_page.click_add_slm_data(self.browser)

        # User clicks a link to add a new Technology.
        add_page = AddDataPage(self)
        add_page.click_add_technology()

        # User sees an empty edit page and the categories of the Technology.
        edit_page = Technologies2018NewPage(self)
        edit_page.close_updated_edition_warning()
        progress_indicators = edit_page.get_progress_indicators()
        categories = edit_page.CATEGORIES
        assert len(progress_indicators) == len(categories)

        # All the categories are listed.
        for __, category in categories:
            edit_page.get_category_by_name(category)

        # User edits the first category.
        edit_page.click_edit_category(self.browser, categories[0][0])

        # The focal point is available
        step_page = QuestionnaireStepPage(self)
        step_page.is_focal_point_available()

        # User saves the first category.
        step_page.submit_step(self.browser)

        # All the categories are still there.
        progress_indicators = edit_page.get_progress_indicators()
        categories = edit_page.CATEGORIES
        assert len(progress_indicators) == len(categories)
        for __, category in categories:
            edit_page.get_category_by_name(category)

    def test_translation(self):

        # User logs in and goes to the Edit page.
        page = Technologies2018NewPage(self)
        page.open(login=True)
        page.close_updated_edition_warning()

        # User sees the category names in English.
        for __, category in page.CATEGORIES:
            page.get_category_by_name(category)

        # User changes the language.
        page.change_language('es', self.browser)
        page.close_updated_edition_warning()

        # User sees the category names in Spanish.
        for __, category in page.CATEGORIES_TRANSLATED:
            page.get_category_by_name(category)


class QuestionnaireFixturesTest(FunctionalTest):

    fixtures = [
        'global_key_values',
        'technologies',
        'technologies_questionnaires',
    ]

    def test_show_edition_update_warning(self):
        # User logs in and goes to the page to create a new Technology
        page = Technologies2018NewPage(self)
        page.open(login=True)

        # There is a warning about updated editions.
        assert page.has_updated_edition_warning()
        page.close_updated_edition_warning()

        # After creating a draft version, the warning is not there anymore.
        page.click_edit_category(self.browser, 'tech__1')
        step_page = QuestionnaireStepPage(self)
        step_page.submit_step(self.browser)
        assert not page.has_updated_edition_warning()

    def test_redirect_edit_public_version(self):

        # User is the compiler of technology "tech_1"
        user = get_user_model().objects.get(pk=101)
        identifier = 'tech_1'
        title = 'WOCAT Technology 1'

        # User logs in and goes to the details of a questionnaire
        detail_page = TechnologiesDetailPage(self)
        detail_page.route_kwargs = {'identifier': identifier}
        detail_page.open(login=True, user=user)
        assert detail_page.has_text(title)

        # User goes to the edit page of the questionnaire and sees he has been
        # redirected to the detail page.
        edit_page = TechnologiesEditPage(self)
        edit_page.route_kwargs = {'identifier': identifier}
        edit_page.open()
        assert self.browser.current_url == detail_page.get_url()

        # User tries to open the URL of a step of this public questionnaire and
        # sees he has been redirected as well.
        step_page = TechnologiesStepPage(self)
        step_page.route_kwargs = {
            'identifier': identifier,
            'step': 'tech__1'
        }
        step_page.open()
        assert self.browser.current_url == detail_page.get_url()

        # User starts a new questionnaire
        new_page = Technologies2018NewPage(self)
        new_page.open()
        new_page.close_updated_edition_warning()
        new_page.click_edit_category(self.browser, 'tech__1')
        step_page = TechnologiesStepPage(self)
        step_page.submit_step(self.browser)

        # For draft versions, the edit URLs can be accessed
        draft_identifier = Questionnaire.objects.get(status=1)
        edit_page.route_kwargs = {'identifier': draft_identifier}
        edit_page.open()
        assert self.browser.current_url == edit_page.get_url()

        step_page.route_kwargs = {
            'identifier': draft_identifier,
            'step': 'tech__1'
        }
        step_page.open()
        assert self.browser.current_url == step_page.get_url()
