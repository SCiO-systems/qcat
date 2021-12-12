import pytest
from apps.configuration.models import Configuration
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.test_views import accounts_route_questionnaires
from model_mommy import mommy

from functional_tests.base import FunctionalTest
from apps.questionnaire.models import Questionnaire, QuestionnaireMembership, Lock
from apps.sample.tests.test_views import (
    route_questionnaire_details,
    route_questionnaire_new,
    get_categories)

from django.contrib.auth.models import Group
from apps.accounts.tests.test_models import create_new_user

from functional_tests.pages.qcat import MyDataPage
from functional_tests.pages.sample import SampleDetailPage, SampleEditPage, \
    SampleStepPage, SampleNewPage
from selenium.webdriver.support.ui import Select


def has_old_version_step(browser):
    browser.findBy(
        'xpath', '//p[contains(text(), "There is an old version with changes '
        'in this section.")]')


def has_no_old_version_step(browser):
    browser.findByNot(
        'xpath', '//p[contains(text(), "There is an old version with changes '
        'in this section.")]')


def has_old_version_overview(browser):
    browser.findBy(
        'xpath', '//p[contains(text(), "There is an old version which is '
        'different than the current one.")]')


def has_no_old_version_overview(browser):
    browser.findByNot(
        'xpath', '//p[contains(text(), "There is an old version which is '
        'different than the current one.")]')


def get_sample_4_5_options(testcase, index=0):
    return testcase.findManyBy(
        'xpath',
        '//select[@id="id_qg_43-{}-key_58"]/option[not(@value="")]'.format(
            index))


def get_sample_4_6_options(testcase, index=0):
    return testcase.findManyBy(
        'xpath',
        '//select[@id="id_qg_46-{}-key_63"]/option[not(@value="")]'.format(
            index))


def get_sample_5_4_options(testcase, index=0):
    return testcase.findManyBy(
        'xpath',
        '//select[@id="id_qg_44-{}-key_60"]/option[not(@value="")]'.format(
            index))


def get_sample_5_5_options(testcase, index=0):
    return testcase.findManyBy(
        'xpath',
        '//select[@id="id_qg_45-{}-key_62"]/option[not(@value="")]'.format(
            index))


class EditTest(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'global_key_values',
        'sample',
        'sample_questionnaire_status',
    ]

    def test_creation_date_does_not_change(self):
        return
        # Alice logs in
        user = User.objects.get(pk=102)

        # She goes to the details of an existing questionnaire and takes
        # note of the creation and update dates
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': 'sample_3'}
        detail_page.open(login=True, user=user)

        creation_date = detail_page.get_el(detail_page.LOC_CREATION_DATE).text
        update_date = detail_page.get_el(detail_page.LOC_UPDATE_DATE).text

        # She creates a new version
        detail_page.create_new_version()

        # She notices that the creation date did not change while the
        # update date changed.
        creation_date_1 = detail_page.get_el(detail_page.LOC_CREATION_DATE).text
        update_date_1 = detail_page.get_el(detail_page.LOC_UPDATE_DATE).text
        assert creation_date == creation_date_1
        assert update_date != update_date_1

        # Alice logs in as a different user
        # She also opens a draft version of a questionnaire and takes
        # note of the creation and update dates
        user = User.objects.get(pk=101)
        detail_page.route_kwargs = {'identifier': 'sample_1'}
        detail_page.open(login=True, user=user)
        creation_date = detail_page.get_el(detail_page.LOC_CREATION_DATE).text
        update_date = detail_page.get_el(detail_page.LOC_UPDATE_DATE).text

        # She makes an edit
        detail_page.edit_questionnaire()
        edit_page = SampleEditPage(self)
        edit_page.click_edit_category(self.browser, 'cat_1')
        step_page = SampleStepPage(self)
        step_page.enter_text(step_page.LOC_FORM_INPUT_KEY_1, ' (changed)')

        # She submits the questionnaire
        step_page.submit_step(self.browser)

        # She sees the changes were submitted
        assert edit_page.has_text(' (changed)')

        # She notices that the creation date did not change while the
        # update date changed.
        creation_date_1 = edit_page.get_el(edit_page.LOC_CREATION_DATE).text
        update_date_1 = edit_page.get_el(edit_page.LOC_UPDATE_DATE).text
        assert creation_date == creation_date_1
        assert update_date != update_date_1

    def test_edit_draft(self):

        code = 'sample_1'

        # Alice logs in
        user = User.objects.get(pk=101)
        self.doLogin(user=user)

        # She goes to the detail page of a "draft" Questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_details, kwargs={'identifier': code}))
        self.assertIn(code, self.browser.current_url)

        self.findBy('xpath', '//*[text()[contains(.,"Foo 1")]]')
        self.findByNot('xpath', '//*[text()[contains(.,"asdf")]]')

        # She edits the Questionnaire and sees that the URL contains the
        # code of the questionnaire
        elm = self.findBy('xpath', '//a[contains(text(), "Edit")]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertIn(code, self.browser.current_url)

        # She edits a category and sees that the URL still contains the
        # code of the Questionnaire
        self.hide_notifications()
        self.click_edit_section('cat_1')
        self.assertIn(code, self.browser.current_url)

        # She makes some changes and submits the category
        key_1 = self.findBy('name', 'qg_1-0-original_key_1')
        key_1.clear()
        self.findBy('name', 'qg_1-0-original_key_1').send_keys('asdf')
        elm = self.findBy('id', 'button-submit')
        self.browser.execute_script("arguments[0].click();", elm)

        # She is back on the overview page and sees that the URL still
        # contains the code of the Questionnaire
        self.assertIn(code, self.browser.current_url)

        # She sees that no new code was created.
        self.assertIn(code, self.browser.current_url)

        # She sees that the value of Key 1 was updated
        self.findByNot('xpath', '//*[text()[contains(.,"Foo 1")]]')
        self.findBy('xpath', '//*[text()[contains(.,"asdf")]]')

        # Also there was no additional version created in the database
        self.assertEqual(Questionnaire.objects.count(), 10)

    def test_edit_public(self):
        return
        code = 'sample_3'
        user = User.objects.get(pk=101)
        old_text = 'Faz 3'
        new_text = 'asdf'

        # User logs in and goes to the detail page of a "public" Questionnaire
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': code}
        detail_page.open(login=True, user=user)
        assert code in self.browser.current_url

        assert detail_page.has_text(old_text)
        assert not detail_page.has_text(new_text)

        # There is only one version of this questionnaire in the db
        assert Questionnaire.objects.filter(code=code).count() == 1

        # User uses the direct link to go to the edit page of the questionnaire
        # and sees no new version of the questionnaire is created in the DB.
        # This prevents the issue when new versions were created upon GET of the
        # edit page, which should be fixed now.
        edit_page = SampleEditPage(self)
        edit_page.route_kwargs = {'identifier': code}
        edit_page.open()
        assert Questionnaire.objects.filter(code=code).count() == 1

        # User edits the Questionnaire (creates a new version) and sees that
        # the URL contains the code of the Questionnaire
        detail_page.open()
        detail_page.create_new_version()
        assert code in self.browser.current_url

        # User edits a category and sees that the URL still contains the
        # code of the Questionnaire
        edit_page.click_edit_category(self.browser, 'cat_2')
        assert code in self.browser.current_url

        # User makes some changes and submits the category
        step_page = SampleStepPage(self)
        step_page.enter_text(
            step_page.LOC_FORM_INPUT_KEY_5, new_text, clear=True)
        step_page.submit_step(self.browser)

        # User is back on the overview page and sees that the URL still
        # contains the code of the Questionnaire
        assert code in self.browser.current_url
        assert edit_page.has_text(code)

        # She sees that the value of Key 1 was updated
        assert not edit_page.has_text(old_text)
        assert edit_page.has_text(new_text)

        # Also there was an additional version created in the database
        assert Questionnaire.objects.count() == 11

        # The newly created version has the same code
        assert Questionnaire.objects.filter(code=code).count() == 2

        # She goes to see her own questionnaire and sees sample_3 appears only
        # once
        my_page = MyDataPage(self)
        my_page.open()

        my_page.wait_for_lists()
        expected_list = [
            {
                'description': new_text,
            },
            {
                # Just to check that description is there ...
                'description': 'Faz 1'
            },
            # ... the rest does not really matter
        ]
        assert my_page.count_list_results() == 6
        my_page.check_list_results(expected_list, count=False)

        # She clicks the first entry and sees that she is taken to the
        # details page of the latest (pending) version.
        my_page.click_list_entry(index=0)
        assert detail_page.has_text(new_text)

    def test_edit_questionnaire(self):
        return
        user = self.create_new_user(
            email='mod@bar.com', groups=['Reviewers', 'Publishers'])

        # Alice logs in
        # She enters a Questionnaire
        new_page = SampleNewPage(self)
        new_page.open(login=True, user=user)

        new_page.click_edit_category(self.browser, 'cat_1')

        step_page = SampleStepPage(self)
        step_page.enter_text(step_page.LOC_FORM_INPUT_KEY_1, 'Foo')
        step_page.enter_text(step_page.LOC_FORM_INPUT_KEY_3, 'Bar')
        step_page.submit_step(self.browser)

        # The questionnaire is already saved as draft
        # She submits it for review
        edit_page = SampleEditPage(self)
        edit_page.submit_questionnaire()

        # She reviews it
        detail_page = SampleDetailPage(self)
        detail_page.review_questionnaire()

        # She publishes it
        detail_page.publish_questionnaire()

        # She sees it is public and visible
        assert detail_page.has_text('Foo')
        assert detail_page.has_text('Bar')

        url = self.browser.current_url

        # She creates a new version
        detail_page.create_new_version()

        # She edits it
        edit_page.click_edit_category(self.browser, 'cat_1')

        # She changes some values
        step_page.enter_text(step_page.LOC_FORM_INPUT_KEY_1, 'asdf', clear=True)
        step_page.submit_step(self.browser)

        # The questionnaire is already saved as draft
        # She is taken to the overview page where she sees the latest
        # (pending) changes of the draft
        edit_page.check_status('draft')
        assert not edit_page.has_text('Foo')
        assert edit_page.has_text('asdf')
        assert edit_page.has_text('Bar')

        # She sees the edit buttons
        assert edit_page.exists_el(edit_page.format_locator(
            edit_page.LOC_BUTTON_EDIT_CATEGORY, keyword='cat_1'))

        # She sees the possibility to view the questionnaire
        edit_page.view_questionnaire(self.browser)
        self.assertIn(url, self.browser.current_url + '#top')

        # All the changes are there
        assert not detail_page.has_text('Foo')
        assert detail_page.has_text('asdf')
        assert detail_page.has_text('Bar')

        # There are no buttons to edit the sections anymore
        assert not detail_page.exists_el(detail_page.format_locator(
            edit_page.LOC_BUTTON_EDIT_CATEGORY, keyword='cat_1'))


class CustomToOptionsTest(FunctionalTest):

    fixtures = [
        'sample_global_key_values',
        'sample',
    ]

    def test_custom_to_options(self):
        return
        # Alice logs in
        self.doLogin()

        # She goes to step 5 of the SAMPLE form
        self.browser.get(
            self.live_server_url + reverse(route_questionnaire_new))
        self.click_edit_section('cat_5')

        # She sees that no labels are selected in key_65 and key_67
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen"]/a/span[text()="-"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen"]/a/span[text()="-"]')

        # She sees that the label fields are disabled
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen" and contains(@class, '
                    '"disabled")]/a/span[text()="-"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen" and contains(@class, '
                    '"disabled")]/a/span[text()="-"]')

        # She selects Value 1 of key 64
        elm = self.findBy('id', 'id_qg_47-0-key_64')
        self.browser.execute_script("document.getElementById('id_qg_47-0-key_64').style.display = '';")
        self.browser.execute_script(
            "arguments[0].style.visibility = 'visible'; arguments[0].style.height = '1px'; arguments[0].style.width = "
            "'1px'; arguments[0].style.opacity = 1",
            elm)

        select = Select(elm)
        select.select_by_value('value_64_1')

        # She sees the labels were updated in key_65 and key_67
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen"]/a/span[text()="'
                    'Value 66 1 Left"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen"]/a/span[text()="'
                    'Value 66 1 Right"]')

        # She deselects the value in key 64
        elm = self.findBy('id', 'id_qg_47-0-key_64')
        self.browser.execute_script("document.getElementById('id_qg_47-0-key_64').style.display = '';")
        self.browser.execute_script(
            "arguments[0].style.visibility = 'visible'; arguments[0].style.height = '1px'; arguments[0].style.width = "
            "'1px'; arguments[0].style.opacity = 1",
            elm)

        select = Select(elm)
        select.select_by_value('')

        # She sees the labels were reset
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen"]/a/span[text()="-"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen"]/a/span[text()="-"]')

        # She selects Value 1 of key 64 again
        elm = self.findBy('id', 'id_qg_47-0-key_64')
        self.browser.execute_script("document.getElementById('id_qg_47-0-key_64').style.display = '';")
        self.browser.execute_script(
            "arguments[0].style.visibility = 'visible'; arguments[0].style.height = '1px'; arguments[0].style.width = "
            "'1px'; arguments[0].style.opacity = 1",
            elm)

        select = Select(elm)
        select.select_by_value('value_64_1')

        # She submits the step and sees the values were submitted correctly
        self.submit_form_step()
        self.findBy('xpath',
                    '//span[contains(@class, "chart-measure-label-left") and '
                    'contains(text(), "Value 66 1 Left")]')
        self.findBy('xpath',
                    '//span[contains(@class, "chart-measure-label-right") and '
                    'contains(text(), "Value 66 1 Right")]')

        # She goes back to the form
        self.click_edit_section('cat_5')

        # She sees the fields were populated correctly
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen" and contains(@class, '
                    '"disabled")]/a/span[text()="Value 66 1 Left"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen" and contains(@class, '
                    '"disabled")]/a/span[text()="Value 66 1 Right"]')

        # She sees the labels were updated in key_65 and key_67
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen"]/a/span[text()="'
                    'Value 66 1 Left"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen"]/a/span[text()="'
                    'Value 66 1 Right"]')

        # She selects Value 2 of key 64
        elm = self.findBy('id', 'id_qg_47-0-key_64')
        self.browser.execute_script("document.getElementById('id_qg_47-0-key_64').style.display = '';")
        self.browser.execute_script(
            "arguments[0].style.visibility = 'visible'; arguments[0].style.height = '1px'; arguments[0].style.width = "
            "'1px'; arguments[0].style.opacity = 1",
            elm)

        select = Select(elm)
        select.select_by_value('value_64_2')

        # She sees the labels were updated in key_65 and key_67
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen"]/a/span[text()="'
                    'Value 66 2 Left"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen"]/a/span[text()="'
                    'Value 66 2 Right"]')

        # She sees that the label fields are disabled
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen" and contains(@class, '
                    '"disabled")]/a/span[text()="Value 66 2 Left"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen" and contains(@class, '
                    '"disabled")]/a/span[text()="Value 66 2 Right"]')

        # She selects Value 3 of key 64
        elm = self.findBy('id', 'id_qg_47-0-key_64')
        self.browser.execute_script("document.getElementById('id_qg_47-0-key_64').style.display = '';")
        self.browser.execute_script(
            "arguments[0].style.visibility = 'visible'; arguments[0].style.height = '1px'; arguments[0].style.width = "
            "'1px'; arguments[0].style.opacity = 1",
            elm)

        select = Select(elm)
        select.select_by_value('value_64_3')

        # She sees the labels were updated and show the first value possible
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen"]/a/span[text()="'
                    'Value 66 3A Left"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen"]/a/span[text()="'
                    'Value 66 3A Right"]')

        # She sees the field is not disabled anymore
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen" and not(contains('
                    '@class, "disabled"))]/a/span[text()="Value 66 3A Left"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen" and not(contains('
                    '@class, "disabled"))]/a/span[text()="Value 66 3A Right"]')

        # She sees she cannot select "Value 66 1 Left"
        elm = self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen"]')
        self.browser.execute_script("arguments[0].click();", elm)

        elm = self.findBy('id', 'id_qg_47-0-key_65')
        self.browser.execute_script("document.getElementById('id_qg_47-0-key_65').style.display = '';")
        self.browser.execute_script(
            "arguments[0].style.visibility = 'visible'; arguments[0].style.height = '1px'; arguments[0].style.width = "
            "'1px'; arguments[0].style.opacity = 1",
            elm)
        select = Select(elm)
        select.select_by_value('value_66_2_left')

        self.browser.execute_script("arguments[0].click();", elm)
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen"]/a/span[text()="'
                    'Value 66 3A Left"]')

        # However, she can select "Value 66 3B Left"
        elm = self.findBy('id', 'id_qg_47-0-key_65')
        self.browser.execute_script("document.getElementById('id_qg_47-0-key_65').style.display = '';")
        self.browser.execute_script(
            "arguments[0].style.visibility = 'visible'; arguments[0].style.height = '1px'; arguments[0].style.width = "
            "'1px'; arguments[0].style.opacity = 1",
            elm)
        select = Select(elm)
        select.select_by_value('value_66_3b_left')
        #print(self.browser.page_source)
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen"]/a/span[text()="'
                    'Value 66 3B Left"]')

        # She submits the step and sees the values were submitted correctly
        self.submit_form_step()
        self.findBy('xpath',
                    '//span[contains(@class, "chart-measure-label-left") and '
                    'contains(text(), "Value 66 3B Left")]')
        self.findBy('xpath',
                    '//span[contains(@class, "chart-measure-label-right") and '
                    'contains(text(), "Value 66 3A Right")]')

        # She goes back to step 5 of the form and sees the values were
        # initialized correctly, the label fields are not disabled
        self.click_edit_section('cat_5')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_65_chosen" and not(contains('
                    '@class, "disabled"))]/a/span[text()="Value 66 3B Left"]')
        self.findBy('xpath',
                    '//div[@id="id_qg_47_0_key_67_chosen" and not(contains('
                    '@class, "disabled"))]/a/span[text()="Value 66 3A Right"]')


class LinkedChoicesTest(FunctionalTest):

    fixtures = [
        'sample_global_key_values',
        'sample',
    ]

    def test_linked_across_step(self):
        return
        # Alice logs in
        self.doLogin()

        # She goes to step 5 of the SAMPLE form
        self.browser.get(
            self.live_server_url + reverse(route_questionnaire_new))
        self.click_edit_section('cat_5')

        # She sees that there are no choices available for 5.4
        self.assertEqual(len(get_sample_5_4_options(self)), 0)

        # She goes to section 4 of the SAMPLE form
        self.submit_form_step()
        self.click_edit_section('cat_4')

        # She selects some options in 4.4
        elm = self.findBy('xpath', '//input[@id="subcat_4_4"]')
        self.browser.execute_script("arguments[0].click();", elm)
        elm = self.findBy(
            'xpath', '//input[@data-container="qg_40"]', wait=True)
        self.browser.execute_script("arguments[0].click();", elm)
        xpath = '//select[@id="id_qg_40-0-key_57"]/option[@value="value_57_1"]'
        elm = self.findBy('xpath', xpath, wait=True)
        self.browser.execute_script("arguments[0].click();", elm)

        elm = self.findBy(
            'xpath', '//input[@data-container="qg_41"]', wait=True)
        self.browser.execute_script("arguments[0].click();", elm)
        xpath = '//select[@id="id_qg_41-0-key_57"]/option[@value="value_57_2"]'
        elm = self.findBy('xpath', xpath, wait=True)
        self.browser.execute_script("arguments[0].click();", elm)

        elm = self.findBy(
            'xpath', '//input[@data-container="qg_42"]', wait=True)
        self.browser.execute_script("arguments[0].click();", elm)
        xpath = '//select[@id="id_qg_42-0-key_57"]/option[@value="value_57_3"]'
        elm = self.findBy('xpath', xpath, wait=True)
        self.browser.execute_script("arguments[0].click();", elm)

        # She submits the step and goes to step 5 again
        self.submit_form_step()
        self.click_edit_section('cat_5')

        # She sees that in 5.4, there are now 3 choices available.
        self.assertEqual(len(get_sample_5_4_options(self)), 3)

        # She fills out a first questiongroup
        self.select_chosen_element('id_qg_44_0_key_60_chosen', 'QG 40')
        self.findBy('id', 'id_qg_44-0-original_key_61').send_keys('Foo')

        # She also fills out a second questiongroup
        self.form_click_add_more('qg_44')
        self.assertEqual(len(get_sample_5_4_options(self, index=1)), 3)
        elm = self.findBy('xpath',
                    '//div[@id="id_qg_44_1_key_60_chosen"]')
        self.browser.execute_script("arguments[0].click();", elm)
        elm = self.findBy('xpath',
                    '//div[@id="id_qg_44_1_key_60_chosen"]//ul[@class="chosen-'
                    'results"]/li[contains(text(), "QG 42")]')
        self.findBy('id', 'id_qg_44-1-original_key_61').send_keys('Bar')

        # She sees that in 5.5, there are only 2 choices available (no qg_42)
        self.assertEqual(len(get_sample_5_5_options(self)), 2)

        # She submits the form step and sees that the values are there.
        self.submit_form_step()
        self.findBy('xpath',
                    '//h3[contains(text(), "Subcategory 5_4")]/following::p['
                    'contains(text(), "QG 40")]')

        # She goes back to step 4
        self.click_edit_section('cat_4')

        # She deselects a value
        xpath = '//select[@id="id_qg_40-0-key_57"]/option[@value=""]'
        elm = self.findBy('xpath', xpath, wait=True)
        self.browser.execute_script("arguments[0].click();", elm)

        # She submits the step and goes back to step 5
        self.submit_form_step()
        self.findByNot('xpath',
                    '//h3[contains(text(), "Subcategory 5_4")]/following::p['
                    'contains(text(), "QG 40")]')

        self.click_edit_section('cat_5')

        # She sees that the option is not selected anymore, all the other
        # values are there
        self.assertEqual(len(get_sample_5_4_options(self)), 2)
        self.assertEqual(len(get_sample_5_4_options(self, index=1)), 2)
        self.findBy('xpath',
                    '//div[@id="id_qg_44_0_key_60_chosen"]/a/span[text()="-"]')
        self.assertEqual(
            self.findBy('id', 'id_qg_44-0-original_key_61').get_attribute(
                'value'), 'Foo')
        self.findBy('xpath',
                    '//div[@id="id_qg_44_1_key_60_chosen"]/a/span['
                    'text()="QG 42"]')
        self.assertEqual(
            self.findBy('id', 'id_qg_44-1-original_key_61').get_attribute(
                'value'), 'Bar')

        # She sees that in 5.5, there is only one option left
        self.assertEqual(len(get_sample_5_5_options(self)), 1)

    def test_linked_choices_within_step(self):
        return
        # Alice logs in
        self.doLogin()

        # She goes to step 4 of the SAMPLE form
        self.browser.get(
            self.live_server_url + reverse(route_questionnaire_new))
        self.click_edit_section('cat_4')

        # She sees that no extremes can be selected in 4.5
        self.assertEqual(len(get_sample_4_5_options(self)), 0)

        # She selects some questiongroups in 4.4 and sees that they are now
        # available for selection in 4.5
        elm = self.findBy('xpath', '//input[@id="subcat_4_4"]')
        self.browser.execute_script("arguments[0].click();", elm)
        elm = self.findBy(
            'xpath', '//input[@data-container="qg_40"]', wait=True)
        self.browser.execute_script("arguments[0].click();", elm)
        # It is not sufficient to click the checkbox of the questiongroup, an
        # actual value of the questiongroup must be selected.
        self.assertEqual(len(get_sample_4_5_options(self)), 0)
        elm = self.findBy('xpath',
                    '//select[@id="id_qg_40-0-key_57"]/option['
                    '@value="value_57_1"]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertEqual(len(get_sample_4_5_options(self)), 1)

        # The same option is also available in 4.6
        self.assertEqual(len(get_sample_4_6_options(self)), 1)

        # She deselects the value again and sees the option disappears in 4.5
        elm = self.findBy('xpath',
                    '//select[@id="id_qg_40-0-key_57"]/option['
                    '@value=""]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertEqual(len(get_sample_4_5_options(self)), 0)
        self.assertEqual(len(get_sample_4_6_options(self)), 0)

        # She selects a value again, the option appears in 4.5
        elm = self.findBy('xpath',
                    '//select[@id="id_qg_40-0-key_57"]/option['
                    '@value="value_57_2"]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertEqual(len(get_sample_4_5_options(self)), 1)

        # The same option is also available in 4.6
        self.assertEqual(len(get_sample_4_6_options(self)), 1)

        # She changes the value of 4.5, still the option appears only once
        self.findBy('xpath',
                    '//select[@id="id_qg_40-0-key_57"]/option['
                    '@value="value_57_1"]').click()
        self.assertEqual(len(get_sample_4_5_options(self)), 1)
        self.assertEqual(len(get_sample_4_6_options(self)), 1)

        # She also selects another value in 4.4
        elm = self.findBy('xpath', '//input[@data-container="qg_41"]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertEqual(len(get_sample_4_5_options(self)), 1)
        xpath = '//select[@id="id_qg_41-0-key_57"]/option[@value="value_57_1"]'
        elm = self.findBy('xpath', xpath, wait=True)
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertEqual(len(get_sample_4_5_options(self)), 2)

        # The same option is also available in 4.6
        self.assertEqual(len(get_sample_4_6_options(self)), 2)

        # She selects an option in 4.6
        self.select_chosen_element('id_qg_46_0_key_63_chosen', 'QG 41')

        # She also selects value 3 of 4.4, but sees that this one is not in the
        # list of options for 4.5
        elm = self.findBy('xpath', '//input[@data-container="qg_42"]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertEqual(len(get_sample_4_5_options(self)), 2)
        xpath = '//select[@id="id_qg_42-0-key_57"]/option[@value="value_57_1"]'
        elm = self.findBy('xpath', xpath, wait=True)
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertEqual(len(get_sample_4_5_options(self)), 2)

        # However, the same option appears in 4.6
        self.assertEqual(len(get_sample_4_6_options(self)), 3)

        # In 4.6, the selected option is still qg_41
        self.findBy('xpath', '//div[@id="id_qg_46_0_key_63_chosen"]/a/span['
                             'text()="QG 41"]')

        # She selects an option in 4.5 and fills out the additional key.
        elm = self.findBy('xpath',
                    '//div[@id="id_qg_43_0_key_58_chosen"]')
        self.browser.execute_script("arguments[0].click();", elm)
        elm = self.findBy('xpath',
                    '//div[@id="id_qg_43_0_key_58_chosen"]//ul[@class="chosen-'
                    'results"]/li[contains(text(), "QG 41")]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.findBy('id', 'id_qg_43-0-original_key_59').send_keys('Foo')

        # She also adds another option in 4.5 by clicking "Add more".
        self.form_click_add_more('qg_43')
        self.assertEqual(len(get_sample_4_5_options(self, index=1)), 2)
        elm = self.findBy('xpath',
                    '//div[@id="id_qg_43_1_key_58_chosen"]')
        self.browser.execute_script("arguments[0].click();", elm)
        elm = self.findBy('xpath',
                    '//div[@id="id_qg_43_1_key_58_chosen"]//ul[@class="chosen-'
                    'results"]/li[contains(text(), "QG 40")]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.findBy('id', 'id_qg_43-1-original_key_59').send_keys('Bar')

        # She deselects a value in 4.4
        elm = self.findBy('xpath',
                    '//select[@id="id_qg_41-0-key_57"]/option['
                    '@value=""]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertEqual(len(get_sample_4_5_options(self)), 1)
        self.assertEqual(len(get_sample_4_5_options(self, index=1)), 1)

        # She sees that the first questiongroup of 4.5 now has no value selected
        # but the additional text field is still there.
        self.findBy('xpath', '//div[@id="id_qg_43_0_key_58_chosen"]/a/span['
                             'text()="-"]')
        self.assertEqual(
            self.findBy('id', 'id_qg_43-0-original_key_59').get_attribute(
                'value'), 'Foo')

        # The second questiongroup of 4.5 is untouched
        self.findBy('xpath', '//div[@id="id_qg_43_1_key_58_chosen"]/a/span['
                             'text()="QG 40"]')
        self.assertEqual(
            self.findBy('id', 'id_qg_43-1-original_key_59').get_attribute(
                'value'), 'Bar')

        # She submits the step and sees the values are submitted correctly
        self.submit_form_step()

        # She opens section 4 again and sees that she can still only select
        # certain options in 4.5
        self.click_edit_section('cat_4')
        self.assertEqual(len(get_sample_4_5_options(self)), 1)
        self.assertEqual(len(get_sample_4_5_options(self, index=1)), 1)

        # The same option is also available in 4.6 (plus qg_42)
        self.assertEqual(len(get_sample_4_6_options(self)), 2)

        self.findBy('xpath',
                    '//div[@id="id_qg_43_0_key_58_chosen"]/a/span[text()="-"]')
        self.assertEqual(
            self.findBy('id', 'id_qg_43-0-original_key_59').get_attribute(
                'value'), 'Foo')
        self.findBy('xpath',
                    '//div[@id="id_qg_43_1_key_58_chosen"]/a/span['
                    'text()="QG 40"]')
        self.assertEqual(
            self.findBy('id', 'id_qg_43-1-original_key_59').get_attribute(
                'value'), 'Bar')

    def test_linked_choices_order(self):
        return
        # Alice logs in
        self.doLogin()

        # She goes to step 4 of the SAMPLE form
        self.browser.get(
            self.live_server_url + reverse(route_questionnaire_new))
        self.click_edit_section('cat_4')

        # She sees that no extremes can be selected in 4.5
        self.assertEqual(len(get_sample_4_5_options(self)), 0)

        # She selects some questiongroups in 4.4 and sees that they are now
        # available for selection in 4.5
        elm = self.findBy('xpath', '//input[@id="subcat_4_4"]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.findBy(
            'xpath', '//input[@data-container="qg_41"]', wait=True)
        self.browser.execute_script("arguments[0].click();", elm)


        elm = self.findBy('id', 'id_qg_41-0-key_67')
        self.browser.execute_script("document.getElementById('id_qg_41-0-key_67').style.display = '';")
        self.browser.execute_script(
            "arguments[0].style.visibility = 'visible'; arguments[0].style.height = '1px'; arguments[0].style.width = "
            "'1px'; arguments[0].style.opacity = 1",
            elm)
        select = Select(elm)
        select.select_by_value('value_57_1')
        elm = self.findBy('xpath',
                    '//select[@id="id_qg_41-0-key_57"]/option['
                    '@value="value_57_1"]', wait=True)
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertEqual(len(get_sample_4_5_options(self)), 1)

        # She selects another option
        elm = self.findBy('xpath', '//input[@data-container="qg_40"]')
        self.browser.execute_script("arguments[0].click();", elm)
        elm = self.findBy('xpath',
                    '//select[@id="id_qg_40-0-key_57"]/option['
                    '@value="value_57_2"]', wait=True)
        self.browser.execute_script("arguments[0].click();", elm)
        self.assertEqual(len(get_sample_4_5_options(self)), 2)

        elm = self.findBy('xpath',
                    '//div[@id="id_qg_43_0_key_58_chosen"]')
        self.browser.execute_script("arguments[0].click();", elm)

        self.findBy('xpath',
                    '//div[@id="id_qg_43_0_key_58_chosen"]//ul[@class="chosen-'
                    'results"]/li[2][contains(text(), "QG 40")]')
        self.findBy('xpath',
                    '//div[@id="id_qg_43_0_key_58_chosen"]//ul[@class="chosen-'
                    'results"]/li[3][contains(text(), "QG 41")]')


class LockTest(FunctionalTest):
    """
    Tests for questionnaire locking.
    """
    fixtures = [
        'sample_global_key_values',
        'sample',
    ]

    def setUp(self):
        super().setUp()
        self.jay = mommy.make(
            _model=get_user_model(),
            firstname='jay',
            email = 'jay@spam.com'
        )
        self.robin = mommy.make(
            _model=get_user_model(),
            firstname='robin',
            email='robin@spam.com'
        )
        self.questionnaire = mommy.make(
            _model=Questionnaire,
            data={},
            code='sample_1',
            status=settings.QUESTIONNAIRE_DRAFT,
            configuration=Configuration.objects.filter(code='sample').first()
        )
        # Create a valid questionnaire with the least required data.
        mommy.make(
            _model=QuestionnaireMembership,
            user=self.jay,
            questionnaire=self.questionnaire,
            role='compiler'
        )
        mommy.make(
            _model=QuestionnaireMembership,
            user=self.robin,
            questionnaire=self.questionnaire,
            role='editor'
        )
        self.questionnaire_edit_url = '{}{}'.format(
            self.live_server_url,
            reverse('sample:questionnaire_edit', args=['sample_1'])
        )
        self.questionnaire_view_url = '{}{}'.format(
            self.live_server_url,
            self.questionnaire.get_absolute_url()
        )

    def test_edit_adds_lock(self):
        # Jay loggs in and starts editing a section.
        self.doLogin(user=self.jay)
        self.browser.get(self.questionnaire_edit_url)
        self.hide_notifications()
        elm = self.findManyBy('link_text', 'Edit this section')[0]
        self.browser.execute_script("arguments[0].click();", elm)

        # Robin logs in and views the questionnaire
        self.doLogin(user=self.robin)
        self.browser.get(self.questionnaire_view_url)
        # but the questionnaire is locked
        self.assertTrue(
            Lock.with_status.is_blocked('sample_1').exists()
        )
        # and the edit button has no url, but a message about the locked status
        edit_button = self.findBy('link_text', 'Edit')
        self.assertTrue(edit_button.get_attribute('disabled'))
        self.findBy('xpath', '//*[text()[contains(.,"This questionnaire is '
                             'locked for editing by jay None.")]]')

        # if the url is accessed directly, a notification is shown
        self.browser.get(self.questionnaire_edit_url)
        self.findBy('xpath', '//div[contains(@class, "notification") '
                             'and contains(@class, "warning")]')
        # maybe: should the edit buttons be disabled?

    def test_edit_locked(self):
        # The questionnaire is locked for Jay
        Lock.objects.create(
            questionnaire_code='sample_1', user=self.jay
        )
        self.doLogin(user=self.robin)
        # Viewing the questionnaire is fine
        self.browser.get(self.questionnaire_view_url)
        # When Robin tries to edit a section, the browser gets redirected
        self.browser.get('{}cat_1'.format(self.questionnaire_edit_url))
        self.browser.implicitly_wait(3)
        self.assertEqual(self.browser.current_url, self.questionnaire_view_url)

    def test_refresh_lock(self):
        self.doLogin(user=self.jay)
        self.browser.get(self.questionnaire_edit_url)
        self.hide_notifications()
        elm = self.findManyBy('link_text', 'Edit this section')[0]
        self.browser.execute_script("arguments[0].click();", elm)
        interval = (settings.QUESTIONNAIRE_LOCK_TIME - 1) * 60 * 1000
        self.findBy('xpath', '//*[text()[contains(.,"{}")]]'.format(interval))

    def test_delete_with_lock(self):
        return
        # The editor logs in and starts editing, this creates a lock.
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': self.questionnaire.code}
        detail_page.open(login=True, user=self.robin)
        detail_page.edit_questionnaire()
        edit_page = SampleEditPage(self)
        edit_page.click_edit_category(self.browser, 'cat_1')

        # The compiler logs in and wants to delete the questionnaire
        detail_page.open(login=True, user=self.jay)
        assert Questionnaire.objects.get(
            code=self.questionnaire.code).is_deleted is False
        assert detail_page.has_text(self.questionnaire.code)
        detail_page.delete_questionnaire(check_success=False)

        # He receives an error message, the questionnaire was not deleted.
        assert detail_page.has_warning_message(
            f'This questionnaire is locked for editing by '
            f'{self.robin.get_display_name()}.')
        assert detail_page.has_text(self.questionnaire.code)
        assert Questionnaire.objects.get(
            code=self.questionnaire.code).is_deleted is False

        # After a while, the lock expires
        Lock.objects.filter(
            questionnaire_code=self.questionnaire.code
        ).update(is_finished=True)

        # Now the questionnaire can be deleted.
        detail_page.delete_questionnaire(check_success=True)
        assert Questionnaire.objects.get(
            code=self.questionnaire.code).is_deleted is True

    def test_delete_with_lock_by_own_user(self):

        # The compiler (!) logs in and starts editing, this creates a lock.
        detail_page = SampleDetailPage(self)
        detail_page.route_kwargs = {'identifier': self.questionnaire.code}
        detail_page.open(login=True, user=self.jay)
        detail_page.edit_questionnaire()
        edit_page = SampleEditPage(self)
        edit_page.click_edit_category(self.browser, 'cat_1')

        # The compiler opens the detail page (= back without saving) and wants
        # to delete the questionnaire while his own lock is still active. This
        # works because his own lock is released when deleting the
        # questionnaire.
        detail_page.open()
        detail_page.delete_questionnaire(check_success=True)
        assert Questionnaire.objects.get(
            code=self.questionnaire.code).is_deleted is True
