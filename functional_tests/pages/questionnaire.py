from apps.accounts.models import User
from selenium.webdriver.common.by import By

from functional_tests.pages.base import QcatPage


class QuestionnaireStepPage(QcatPage):
    route_name = ''

    LOC_BUTTON_SUBMIT = (By.ID, 'button-submit')
    LOC_IMAGE_FOCAL_POINT_TARGET = (By.ID, 'id_qg_image-0-image_target')
    LOC_LINK_ENTRIES = (By.XPATH, '//div[@class="link-preview"]/div')
    LOC_LINK_ENTRY = (
        By.XPATH,
        '//div[@class="link-preview"]/div[text()="{link_text}"]')
    LOC_LINK_ENTRY_REMOVE = (
        By.XPATH, '(//div[@class="link-preview"])[{index}]//'
                  'a[@class="close"]')  # 1-based!
    LOC_LINK_ADD_MORE = (
        By.XPATH, '//a[@data-questiongroup-keyword="{questiongroup}" and '
                  '@data-add-item]')
    LOC_INPUT_SEARCH_LINK = (
        By.XPATH, '(//div[contains(@class, "link-search") and not(contains('
                  '@style, "display: none;"))])[1]/input[contains(@class, '
                  '"link-search-field")]')
    LOC_INPUT_SEARCH_USER = (
        By.XPATH,
        '(//input[contains(@class, "user-search-field")])[{index}]')  # 1-based!
    LOC_RADIO_SEARCH_USER = (
        By.XPATH, '//input[@name="form-user-radio" and @value="search"]')
    LOC_LOADING_SEARCH_USER = (By.CLASS_NAME, 'form-user-search-loading')
    LOC_DISPLAY_SEARCH_USER = (
        By.XPATH,
        '//div[contains(@class, "alert-box") and contains(text(), "{name}")]')
    LOC_REMOVE_SEARCH_USER = (
        By.XPATH,
        '//div[contains(@class, "alert-box") and contains(text(), "{name}")]/a')
    LOC_BUTTON_BACK_WITHOUT_SAVING = (
        By.XPATH, '//a[@class="wizard-header-back"]')
    LOC_MODAL_TRANSLATION_WARNING = (By.ID, 'modal-translation-warning')
    LOC_MODAL_TRANSLATION_CONFIRM_CREATE = (
        By.CLASS_NAME, 'close-modal-translation-confirm-create')
    LOC_BUTTON_TRANSLATION_WARNING_BACK = (
        By.ID, 'modal-translation-warning-back')
    LOC_BUTTON_TRANSLATION_WARNING_CONTINUE = (
        By.CLASS_NAME, 'close-modal-translation-warning')

    def is_focal_point_available(self):
        # The script to set the focus point for the image is loaded, and the
        # hidden field is in the DOM.
        self.browser.execute_script("return $.addFocusPoint();")
        self.exists_el(self.LOC_IMAGE_FOCAL_POINT_TARGET)

    def enter_text(self, locator: tuple, text: str, clear: bool=False):
        el = self.get_el(locator)
        if clear is True:
            el.clear()
        el.send_keys(text)

    def submit_step(self, driver, confirm_add_translation: bool=False):
        elm = self.get_el(self.LOC_BUTTON_SUBMIT)
        driver.execute_script("arguments[0].click();", elm)
        if confirm_add_translation:
            self.wait_for_modal()
            elm = self.get_el(self.LOC_MODAL_TRANSLATION_CONFIRM_CREATE)
            driver.execute_script("arguments[0].click();", elm)
        assert self.has_success_message()

    def back_without_saving(self, driver):
        elm = self.get_el(self.LOC_BUTTON_BACK_WITHOUT_SAVING)
        driver.execute_script("arguments[0].click();", elm)

    def check_links(self, link_list: list, count: bool=True) -> bool:
        found_links = []
        for link in link_list:
            link_el = self.get_el(
                self.format_locator(self.LOC_LINK_ENTRY, link_text=link))
            found_links.append(link_el)
        if count is True:
            return len(self.get_els(self.LOC_LINK_ENTRIES)) == len(found_links)
        return True

    def delete_link(self, index: int):
        elm = self.get_el(
            self.format_locator(self.LOC_LINK_ENTRY_REMOVE, index=index+1)
        )
        self.browser.execute_script("arguments[0].click();", elm)

    def add_link(self, qg_keyword: str, link_name: str, add_more: bool=False):
        if add_more is True:
            elm = self.get_el(
                self.format_locator(
                    self.LOC_LINK_ADD_MORE, questiongroup=qg_keyword)
            )
            self.browser.execute_script("arguments[0].click();", elm)
        self.get_el(self.LOC_INPUT_SEARCH_LINK).send_keys(link_name)
        self.select_autocomplete(self.browser, link_name)

    def get_user_search_field(self, index: int=1):
        return self.get_el(
            self.format_locator(self.LOC_INPUT_SEARCH_USER, index=index))

    def has_selected_user(self, user: User):
        return self.exists_el(
            self.format_locator(
                self.LOC_DISPLAY_SEARCH_USER, name=user.get_display_name()))

    def select_user(self, user: User, index: int=1):
        search_field = self.get_user_search_field(index=index)
        search_field.send_keys(user.firstname)
        self.select_autocomplete(user.get_display_name())
        self.wait_for(self.LOC_LOADING_SEARCH_USER, visibility=False)

    def remove_selected_user(self, user: User):
        self.get_el(
            self.format_locator(
                self.LOC_REMOVE_SEARCH_USER, name=user.get_display_name())
        ).click()

    def has_translation_warning(self):
        return self.exists_el(self.LOC_MODAL_TRANSLATION_WARNING)

    def translation_warning_click_go_back(self, driver):
        elm = self.get_el(self.LOC_BUTTON_TRANSLATION_WARNING_BACK)
        driver.execute_script("arguments[0].click();", elm)

    def translation_warning_click_continue(self, driver):
        elm = self.get_el(self.LOC_BUTTON_TRANSLATION_WARNING_CONTINUE)
        driver.execute_script("arguments[0].click();", elm)
        #self.wait_for_modal(visibility=False)
