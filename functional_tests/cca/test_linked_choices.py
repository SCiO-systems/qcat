from django.urls import reverse
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from apps.cca.tests.test_views import route_questionnaire_new
from functional_tests.base import FunctionalTest

driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver")

def get_cca_2_3_options(testcase):
    return testcase.findManyBy(
        'xpath', '//select[@id="id_cca_qg_39-0-climate_related_extreme"]/'
                 'option[not(@value="")]')


def get_cca_3_1_options(testcase):
    return testcase.findManyBy(
        'xpath', '//select[@id="id_cca_qg_40-0-climate_related_extreme_conditional"]/'
                 'option[not(@value="")]')


class LinkedChoicesTest(FunctionalTest):

    fixtures = [
        'global_key_values',
        'technologies',
        'cca',
    ]

    def test_linked_across_step(self):

        # Alice logs in
        self.doLogin()

        # She goes to step 3 of the CCA form.
        self.browser.get(
            self.live_server_url + reverse(route_questionnaire_new))
        self.click_edit_section('cca__3')

        # She sees that there are no choices available for 3.1
        self.assertEqual(len(get_cca_3_1_options(self)), 0)

        # She goes to step 2 and selects some disasters
        self.submit_form_step()
        self.click_edit_section('cca__2')

        self.findBy('xpath', '//input[@id="cca__2__2__meteorological"]', wait=True).click()
        self.findBy('xpath', '//input[@data-container="cca_qg_9"]', wait=True).click()
        self.findBy('xpath',
                    '//select[@id="id_cca_qg_9-0-cca_exposure_decrstabincr"]/option[@value="stable"]', wait=True).click()

        self.findBy('xpath', '//input[@id="cca__2__2__biological"]', wait=True).click()
        self.findBy('xpath', '//input[@data-container="cca_qg_29"]', wait=True).click()
        self.findBy('xpath',
                    '//select[@id="id_cca_qg_29-0-cca_exposure_decrstabincr_other"]/option[@value="cca_decrease"]', wait=True).click()

        # She also selects a gradual climate change
        self.findBy('xpath', '//input[@id="cca__2__2__gradual"]', wait=True).click()
        self.findBy('xpath', '//input[@data-container="cca_qg_2"]', wait=True).click()
        self.findBy('xpath',
                    '//select[@id="id_cca_qg_2-0-cca_exposure_decrstabincr"]/option[@value="cca_decrease"]', wait=True).click()

        # She saves and goes to step 3 again and sees she can now select them.
        self.submit_form_step()
        self.click_edit_section('cca__3')
        self.assertEqual(len(get_cca_3_1_options(self)), 3)

        self.select_chosen_element(
            'id_cca_qg_40_0_climate_related_extreme_conditional_chosen',
            'annual temperature')
        self.select_chosen_element(
            'id_cca_qg_40_0_climate_related_extreme_conditional_chosen',
            'local rainstorm')
        self.select_chosen_element(
            'id_cca_qg_40_0_climate_related_extreme_conditional_chosen',
            'insect/ worm infestation')

    def test_linked_choices_within_step(self):

        # Alice logs in
        self.doLogin()

        # She goes to step 2 of the CCA form
        self.browser.get(
            self.live_server_url + reverse(route_questionnaire_new))
        self.click_edit_section('cca__2')

        # She sees that no extremes can be selected in 2.3
        self.assertEqual(len(get_cca_2_3_options(self)), 0)

        # She selects some disasters in 2.2 and sees that they are now available
        # for selection in 2.3
        self.findBy('xpath', '//input[@id="cca__2__2__meteorological"]', wait=True).click()
        self.findBy('xpath', '//input[@data-container="cca_qg_9"]', wait=True).click()
        # It is not sufficient to click the checkbox of the questiongroup, an
        # actual value of the questiongroup must be selected.
        self.assertEqual(len(get_cca_2_3_options(self)), 0)
        self.findBy('xpath', '//select[@id="id_cca_qg_9-0-cca_exposure_decrstabincr"]/option[@value="stable"]', wait=True).click()
        self.assertEqual(len(get_cca_2_3_options(self)), 1)

        self.findBy('xpath', '//input[@id="cca__2__2__biological"]', wait=True).click()
        self.findBy('xpath', '//input[@data-container="cca_qg_29"]', wait=True).click()
        self.assertEqual(len(get_cca_2_3_options(self)), 1)
        self.findBy('xpath',
                    '//select[@id="id_cca_qg_29-0-cca_exposure_decrstabincr_other"]/option[@value="cca_decrease"]', wait=True).click()
        self.assertEqual(len(get_cca_2_3_options(self)), 2)

        # She also selects a gradual climate change and sees it is not an option
        # in 2.3
        self.findBy('xpath', '//input[@id="cca__2__2__gradual"]', wait=True).click()
        self.findBy('xpath', '//input[@data-container="cca_qg_2"]', wait=True).click()
        self.findBy('xpath',
                    '//select[@id="id_cca_qg_2-0-cca_exposure_decrstabincr"]/option[@value="cca_decrease"]', wait=True).click()
        self.assertEqual(len(get_cca_2_3_options(self)), 2)

        # She selects an extreme in 2.3
        cca_2_3_radio = self.findBy(
            'id', 'id_cca_qg_38-0-technology_exposed_to_disasters_1')
        cca_2_3_radio.click()
        self.findBy('xpath', '//div[@id="id_cca_qg_39_0_climate_related_extreme_chosen"]', wait=True).click()
        self.findBy('xpath', '//div[@id="id_cca_qg_39_0_climate_related_extreme_chosen"]//ul[@class="chosen-results"]/li[contains(text(), "local rainstorm")]')
        self.findBy('xpath', '//div[@id="id_cca_qg_39_0_climate_related_extreme_chosen"]//ul[@class="chosen-results"]/li[contains(text(), "insect/ worm infestation")]', wait=True).click()

        # She adds another row and can again select the same extremes
        self.findBy('xpath', '//a[@data-questiongroup-keyword="cca_qg_39"]', wait=True).click()
        self.findBy('xpath', '//div[@id="id_cca_qg_39_1_climate_related_extreme_chosen"]', wait=True).click()
        self.findBy('xpath', '//div[@id="id_cca_qg_39_1_climate_related_extreme_chosen"]//ul[@class="chosen-results"]/li[contains(text(), "insect/ worm infestation")]')
        self.findBy('xpath', '//div[@id="id_cca_qg_39_1_climate_related_extreme_chosen"]//ul[@class="chosen-results"]/li[contains(text(), "local rainstorm")]', wait=True).click()

        # She submits the step and sees the values are submitted correctly
        self.submit_form_step()

        self.findBy('xpath', '//h3[contains(text(), "Gradual climate change")]/following::table/tbody/tr/td[contains(text(), "annual temperature")]')
        self.findBy('xpath', '//h3[contains(text(), "Climate-related extremes (disasters)")]/following::h5[contains(text(), "Meteorological disasters")]/following::table/tbody/tr/td[contains(text(), "local rainstorm")]')
        self.findBy('xpath', '//h3[contains(text(), "Climate-related extremes (disasters)")]/following::h5[contains(text(), "Biological disasters")]/following::table/tbody/tr/td[contains(text(), "insect/ worm infestation")]')

        self.findBy('xpath', '//h3[contains(text(), "Experienced climate-related extremes (disasters)")]/following::table/tbody/tr/td[contains(text(), "insect/ worm infestation")]')
        self.findBy('xpath', '//h3[contains(text(), "Experienced climate-related extremes (disasters)")]/following::table/tbody/tr/td[contains(text(), "local rainstorm")]')

        # She opens section 2 again and sees that she can still only select
        # certain options in 2.3
        self.click_edit_section('cca__2')
        self.assertEqual(len(get_cca_2_3_options(self)), 2)
