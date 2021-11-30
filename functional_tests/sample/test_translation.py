import pytest
import requests

from django.contrib.auth.models import Group
from django.urls import reverse

from apps.accounts.tests.test_models import create_new_user
from functional_tests.base import FunctionalTest
from apps.sample.tests.test_views import (
    route_questionnaire_new,
)

from functional_tests.pages.sample import SampleNewPage, SampleStepPage


class TranslationTest(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'sample_global_key_values',
        'sample',
    ]

    def test_enter_questionnaire_in_spanish_freetext(self):

        # Alice logs in
        self.doLogin()

        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_new))

        # She changes the language to Spanish
        self.changeLanguage('es')

        # She starts editing and enters some freetext
        self.click_edit_section('cat_1')
        self.findBy('name', 'qg_1-0-original_key_1').send_keys(
            'Foo content in Spanish')

        # She submits the step and sees the values were transmitted correctly.
        self.submit_form_step()
        self.findBy(
            'xpath', '//*[text()[contains(.,"Foo content in Spanish")]]')

        # She changes the language to English and sees that she can see the
        # freetext values, even though they are in Spanish
        self.changeLanguage('en')
        self.findBy(
            'xpath', '//*[text()[contains(.,"Foo content in Spanish")]]')

        self.click_edit_section('cat_1')

        # She sees a warning that she is about to create a new translation
        step_page = SampleStepPage(self)
        assert step_page.has_translation_warning()
        step_page.translation_warning_click_continue(self.browser)

        # She sees that the field already contains the original value
        text_field = self.findBy('name', 'qg_1-0-translation_key_1')
        self.assertEqual(
            text_field.get_attribute('value'), 'Foo content in Spanish')

        # She changes the value to its English translation
        text_field.clear()
        text_field.send_keys('Foo content in English')

        # She submits the step
        step_page.submit_step(self.browser, confirm_add_translation=True)
        self.findBy(
            'xpath', '//*[text()[contains(.,"Foo content in English")]]')

        # She submits the Questionnaire
        self.review_action('submit')
        self.findBy(
            'xpath', '//*[text()[contains(.,"Foo content in English")]]')

        # She sees that the Spanish original is still there
        self.changeLanguage('es')
        self.findBy(
            'xpath', '//*[text()[contains(.,"Foo content in Spanish")]]')

        # She sees that both languages are available in the tech info metadata
        translations = self.findManyBy(
            'xpath', '//ul[contains(@class, "tech-lang-list")]/li')
        self.assertEqual(len(translations), 2)

    def test_enter_translation_in_review_process(self):
        # Alice logs in
        user_alice = create_new_user()
        user_alice.groups.set([Group.objects.get(pk=3), Group.objects.get(pk=4)])
        self.doLogin(user=user_alice)

        # She goes to the form to enter a new Questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_new))

        # She enters a questionnaire in English
        self.click_edit_section('cat_1')
        self.findBy('name', 'qg_1-0-original_key_1').send_keys(
            'Foo content in English')

        # She submits the step and sees the values were transmitted correctly.
        self.submit_form_step()
        self.findBy(
            'xpath', '//*[text()[contains(.,"Foo content in English")]]')

        # She submits the questionnaire
        self.review_action('submit')
        self.findBy(
            'xpath', '//*[text()[contains(.,"Foo content in English")]]')

        # She is also moderator and edits the questionnaire again
        elm = self.findBy('xpath', '//a[text()="Edit" and @type="submit"]')
        self.browser.execute_script("arguments[0].click();", elm)

        # She changes the language to Spanish
        self.changeLanguage('es')

        # She edits the first section
        self.click_edit_section('cat_1')

        # She sees a warning that she is about to create a new translation
        step_page = SampleStepPage(self)
        assert step_page.has_translation_warning()
        step_page.translation_warning_click_continue(self.browser)

        # She sees that the field already contains the original value
        text_field = self.findBy('name', 'qg_1-0-translation_key_1')
        self.assertEqual(
            text_field.get_attribute('value'), 'Foo content in English')

        # She changes the value to its Spanish translation
        text_field.clear()
        text_field.send_keys('Foo content in Spanish')

        # She submits the step and sees the values were transmitted correctly.
        step_page.submit_step(self.browser, confirm_add_translation=True)
        self.findBy(
            'xpath', '//*[text()[contains(.,"Foo content in Spanish")]]')

        # She sees that both languages are available in the tech info metadata
        translations = self.findManyBy(
            'xpath', '//ul[contains(@class, "tech-lang-list")]/li')
        self.assertEqual(len(translations), 2)

    def test_show_warning_when_adding_new_translation(self):

        user = self.create_new_user(email='user@foo.com')

        new_page = SampleNewPage(self)
        new_page.open(login=True, user=user)

        # User sets the language to English and starts editing.
        new_page.change_language('en', self.browser)
        new_page.click_edit_category(self.browser, 'cat_1')

        # User does not see a translation warning (no object yet)
        step_page = SampleStepPage(self)
        assert not step_page.has_translation_warning()

        # User fills out a key and submits the step.
        step_page.get_el(step_page.LOC_FORM_INPUT_KEY_1).send_keys('Foo')
        step_page.submit_step(self.browser)

        # User opens another step and does not see a translation warning
        new_page.click_edit_category(self.browser, 'cat_1')
        assert not step_page.has_translation_warning()
        step_page.back_without_saving(self.browser)

        # User now changes the language to French and wants to edit again.
        new_page.change_language('fr', self.browser)
        new_page.click_edit_category(self.browser, 'cat_1')

        # User sees a warning, telling him that he is about to add a new
        # translation.
        assert step_page.has_translation_warning()

        # User decides to go back to the overview.
        step_page.translation_warning_click_go_back(self.browser)

        # User again wants to edit in French
        new_page.click_edit_category(self.browser, 'cat_1')
        assert step_page.has_translation_warning()

        # This time, user continues and submits the step.
        step_page.translation_warning_click_continue(self.browser)
        step_page.submit_step(self.browser, confirm_add_translation=True)

        # When he opens the step again (in French), no warning is displayed
        # anymore.
        new_page.click_edit_category(self.browser, 'cat_1')
        assert not step_page.has_translation_warning()
