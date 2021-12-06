from apps.accounts.models import User
from django.urls import reverse
from django.test.utils import override_settings

from functional_tests.base import FunctionalTest
from apps.sample.tests.test_views import route_questionnaire_new

route_add_module = 'sample:add_module'


@override_settings(IS_ACTIVE_FEATURE_MODULE=True)
class EditModuleTest(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'global_key_values',
        'sample',
        'samplemodule',
    ]

    def test_edit_module(self):
        return
        # Alice logs in
        self.doLogin()

        # She creates a sample questionnaire
        self.browser.get(self.live_server_url + reverse(
            route_questionnaire_new))
        self.click_edit_section('cat_1')
        self.findBy('name', 'qg_1-0-original_key_1').send_keys('Foo')
        self.findBy('name', 'qg_1-0-original_key_3').send_keys('Bar')
        self.select_chosen_element('id_qg_3_0_key_4_chosen', 'Germany')
        elm = self.findBy('id', 'button-submit')
        self.browser.execute_script("arguments[0].click();", elm)
        self.findBy('xpath', '//div[contains(@class, "success")]')

        sample_url = self.browser.current_url

        # She adds a module for this questionnaire (toggle section manually)
        elm = self.findBy('xpath', '(//a[contains(@class, "js-expand-all-sections")])[2]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.wait_for('xpath', '//a[contains(@class, "js-show-embedded-modules-form")]')
        elm = self.findBy('xpath', '//a[contains(@class, "js-show-embedded-modules-form")]')
        self.browser.execute_script("arguments[0].click();", elm)
        samplemodule_radio = self.findBy(
            'xpath',
            '//input[@value="samplemodule" and @name="module"]')
        self.browser.execute_script("arguments[0].click();", samplemodule_radio)
        elm = self.findBy('xpath', '//input[@type="submit" and @value="Create"]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.findBy('xpath', '//div[contains(@class, "success")]')

        module_url = self.browser.current_url

        # She sees the inherited values
        self.toggle_all_sections()
        self.findBy('xpath', '//*[text()[contains(.,"Key 1 (Samplemodule)")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Foo")]]')
        self.findByNot('xpath', '//*[text()[contains(.,"Bar")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Key 4 (Samplemodule)")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Germany")]]')

        # She edits the first step of the module
        self.click_edit_section('modcat_1')

        # She sees the inherited values as disabled fields
        key_1 = self.findBy('name', 'modqg_sample_01-0-original_key_1')
        self.assertEqual(key_1.get_attribute('value'), 'Foo')
        self.assertEqual(key_1.get_attribute('disabled'), 'true')

        key_4 = self.findBy('name', 'modqg_sample_02-0-key_4')
        self.assertEqual(key_4.get_attribute('disabled'), 'true')
        key_4_selected = self.findBy(
            'xpath', '//select[@name="modqg_sample_02-0-key_4"]/option[@selected]')
        self.assertEqual(key_4_selected.get_attribute('value'), 'country_2')

        # She sees she can edit the first question
        modkey_1 = self.findBy('name', 'modqg_01-0-original_modkey_01')
        self.assertIsNone(modkey_1.get_attribute('disabled'))

        # She goes to the sample questionnaire
        self.browser.get(sample_url)
        self.toggle_all_sections()

        # She edits some values
        self.click_edit_section('cat_1')
        self.findBy('name', 'qg_1-0-original_key_1').send_keys(' (changed)')
        self.select_chosen_element('id_qg_3_0_key_4_chosen', 'Switzerland')
        elm = self.findBy('id', 'button-submit')
        self.browser.execute_script("arguments[0].click();", elm)
        self.findBy('xpath', '//div[contains(@class, "success")]')

        # She goes back to the module and sees the updated values
        self.browser.get(module_url)
        self.toggle_all_sections()
        self.findBy('xpath', '//*[text()[contains(.,"Key 1 (Samplemodule)")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Foo (changed)")]]')
        self.findByNot('xpath', '//*[text()[contains(.,"Bar")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Key 4 (Samplemodule)")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Switzerland")]]')

        # She enters the first question and saves the step
        self.click_edit_section('modcat_1')
        self.findBy('name', 'modqg_01-0-original_modkey_01').send_keys('asdf')
        self.submit_form_step()

        # She sees the inherited values and the first question
        self.findBy('xpath', '//*[text()[contains(.,"Key 1 (Samplemodule)")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Foo (changed)")]]')
        self.findByNot('xpath', '//*[text()[contains(.,"Bar")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Key 4 (Samplemodule)")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Switzerland")]]')
        self.findBy('xpath', '//*[text()[contains(.,"ModKey 1")]]')
        self.findBy('xpath', '//*[text()[contains(.,"asdf")]]')

        # She goes back to the form and sees all values
        self.click_edit_section('modcat_1')
        key_1 = self.findBy('name', 'modqg_sample_01-0-original_key_1')
        self.assertEqual(key_1.get_attribute('value'), 'Foo (changed)')
        self.assertEqual(key_1.get_attribute('disabled'), 'true')
        key_4 = self.findBy('name', 'modqg_sample_02-0-key_4')
        self.assertEqual(key_4.get_attribute('disabled'), 'true')
        key_4_selected = self.findBy(
            'xpath',
            '//select[@name="modqg_sample_02-0-key_4"]/option[@selected]')
        self.assertEqual(key_4_selected.get_attribute('value'), 'country_4')

        # By some hack, she makes the inherited value editable and submits the
        # step
        self.set_input_value(key_1, 'spam')
        self.submit_form_step()

        # She sees the unchanged inherited values
        self.findBy('xpath', '//*[text()[contains(.,"Key 1 (Samplemodule)")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Foo (changed)")]]')
        self.findByNot('xpath', '//*[text()[contains(.,"Bar")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Key 4 (Samplemodule)")]]')
        self.findBy('xpath', '//*[text()[contains(.,"Switzerland")]]')
        self.findBy('xpath', '//*[text()[contains(.,"ModKey 1")]]')
        self.findBy('xpath', '//*[text()[contains(.,"asdf")]]')
        self.findByNot('xpath', '//*[text()[contains(.,"spam")]]')


@override_settings(IS_ACTIVE_FEATURE_MODULE=True)
class EditModuleWithLink(FunctionalTest):

    fixtures = [
        'groups_permissions',
        'global_key_values',
        'sample',
        'samplemodule',
        'samplemulti',
        'sample_samplemulti_questionnaires',
    ]

    def test_edit_module_with_link(self):
        """
        This tests a bugfix where there was an error when trying to add a module
        to a questionnaire which has a link.
        """
        # Alice logs in
        user = User.objects.get(pk=101)
        self.doLogin(user=user)

        # She goes to a SAMPLE questionnaire which has a link
        self.open_questionnaire_details('sample', identifier='sample_1')

        # She opens the panel to add a module and sees there is no error.
        self.wait_for('xpath', '//a[contains(@class, "js-show-embedded-modules-form")]')
        elm = self.findBy('xpath', '//a[contains(@class, "js-show-embedded-modules-form")]')
        self.browser.execute_script("arguments[0].click();", elm)
        self.findBy('xpath', '//input[@value="samplemodule" and @name="module"]')
