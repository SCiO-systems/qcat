from selenium.webdriver.common.by import By


class ListMixin:
    LOC_LIST_ENTRY = (By.XPATH, '//article[contains(@class, "tech-item")]')
    LOC_LIST_ENTRY_TITLE = (
        By.XPATH, '(//article[contains(@class, "tech-item")])[{i}]'  # 1-based!
                  '//a[contains(text(), "{title}")]')
    LOC_LIST_ENTRY_DESCRIPTION = (
        By.XPATH, '(//article[contains(@class, "tech-item")])[{i}]'  # 1-based!
                  '//p[contains(text(), "{description}")]')
    LOC_LIST_ENTRY_STATUS = (
        By.XPATH, '(//article[contains(@class, "tech-item")])[{i}]'  # 1-based!
                  '//span[contains(@class, "tech-status") and contains('
                  '@class, "is-{status}")]')
    LOC_LIST_ENTRY_LANGUAGE = (
        By.XPATH, '(//article[contains(@class, "tech-item")])[{i}]'  # 1-based!
                  '//a[contains(text(), "{lang}")]')
    LOC_LIST_ENTRY_COMPILER = (
        By.XPATH, '(//article[contains(@class, "tech-item")])[{i}]'  # 1-based!
                  '//li[text()="Compiler: {compiler}"]'
    )
    LOC_FILTER_TYPE_SWITCHER = (By.ID, 'search-type-display')
    LOC_FILTER_TYPE_ENTRY = (
        By.XPATH, '//ul[contains(@class, "search-type-select")]/li/'
                  'a[@data-type="{type}"]')
    LOC_FILTER_TYPE_VALUE = (By.ID, 'search-type')  # The hidden value
    LOC_FILTER_COUNTRY_CHOSEN = (By.XPATH, '//div[@id="filter_country_chosen"]')
    LOC_BUTTON_FILTER_SUBMIT = (By.CLASS_NAME, 'search-submit')
    LOC_LOADING_INDICATOR = (By.CLASS_NAME, 'loading-indicator')
    LOC_ACTIVE_FILTERS = (By.XPATH, '//div[@id="active-filters"]//li')
    LOC_SEARCH_INPUT = (By.XPATH, '//input[@type="search" and @name="q"]')

    def get_type_value(self) -> str:
        return self.get_value(self.get_el(self.LOC_FILTER_TYPE_VALUE))

    def search(self, search_term: str, clear: bool=True):
        el = self.get_el(self.LOC_SEARCH_INPUT)
        if clear is True:
            el.clear()
        el.send_keys(search_term)

    def filter_by_type(self, type_keyword: str):
        elm = self.get_el(self.LOC_FILTER_TYPE_SWITCHER)
        self.browser.execute_script("arguments[0].click();", elm)
        locator = self.format_locator(
            self.LOC_FILTER_TYPE_ENTRY, type=type_keyword)
        elm = self.get_el(locator)
        self.browser.execute_script("arguments[0].click();", elm)

    def filter_by_country(self, country_name: str):
        self.select_chosen(self.LOC_FILTER_COUNTRY_CHOSEN, country_name)

    def apply_filter(self):
        elm = self.get_el(self.LOC_BUTTON_FILTER_SUBMIT)
        self.browser.execute_script("arguments[0].click();", elm)
        self.wait_for(self.LOC_LOADING_INDICATOR, visibility=False)

    def get_active_filters(self) -> list:
        return [f.text for f in self.get_els(self.LOC_ACTIVE_FILTERS)]

    def count_list_results(self) -> int:
        return len(self.get_els(self.LOC_LIST_ENTRY))

    def check_list_results(self, expected: list, count: bool=True):
        """
        Args:
            expected: list of dicts. Can contain
                - title
                - description
                - status: Note that status "public" has no badge
                - translations (list)
            count: bool. Check whether length of expected list matches length of
                actual list results.
        """
        if count is True:
            assert self.count_list_results() == len(expected)
        for i, e in enumerate(expected):
            i_xpath = i + 1
            if e.get('title'):
                locator = self.format_locator(
                    self.LOC_LIST_ENTRY_TITLE, i=i_xpath, title=e['title'])
                self.get_el(locator)
            if e.get('description'):
                locator = self.format_locator(
                    self.LOC_LIST_ENTRY_DESCRIPTION, i=i_xpath,
                    description=e['description'])
                self.get_el(locator)
            if e.get('status'):
                locator = self.format_locator(
                    self.LOC_LIST_ENTRY_STATUS, i=i_xpath, status=e['status'])
                if e['status'] == 'public':
                    assert self.exists_el(locator) is False
                else:
                    self.get_el(locator)
            for lang in e.get('translations', []):
                locator = self.format_locator(
                    self.LOC_LIST_ENTRY_LANGUAGE, i=i_xpath, lang=lang)
                self.get_el(locator)
            if e.get('compiler'):
                locator = self.format_locator(
                    self.LOC_LIST_ENTRY_COMPILER, i=i_xpath,
                    compiler=e['compiler'])
                self.get_el(locator)

    def click_list_entry(self, index: int):
        elm = self.get_el(
            self.format_locator(self.LOC_LIST_ENTRY_TITLE, i=index+1, title='')
        )
        self.browser.execute_script("arguments[0].click();", elm)


class ReviewMixin:
    LOC_BUTTON_REVIEW_ACTION = (
        By.XPATH, '//a[@data-reveal-id="confirm-{action}"]')
    LOC_BUTTON_REVIEW_CONFIRM = (By.XPATH, '//button[@name="{action}"]')
    LOC_BUTTONS_REVIEW_ACTIONS = (
        By.XPATH, '//div[contains(@class, "review-panel")]//a[contains(@class, '
                  '"button") and contains(@class, "expand")]')
    LOC_BUTTON_CHANGE_COMPILER_PANEL = (
        By.XPATH, '//a[@data-toggle="review-change-compiler-panel" and '
                  'contains(@class, "expand")]')
    LOC_BUTTON_ASSIGN_USER_PANEL = (
        By.XPATH, '//a[contains(@class, "js-toggle-edit-assigned-users") and '
                  'contains(@class, "expand")]')
    LOC_BUTTON_CHANGE_COMPILER = (By.ID, 'button-change-compiler')
    LOC_BUTTON_CHANGE_USER = (By.ID, 'button-assign')
    LOC_BUTTON_REMOVE_USER = (
        By.XPATH, '//div[@id="review-new-user"]/div[contains(text(), '
                  '"{user}")]/a')
    LOC_BUTTON_FINISH_EDITING = (By.XPATH, '//a[@data-reveal-id="finish-editing"]')
    LOC_BUTTON_FINISH_EDITING_CONFIRM = (By.ID, 'inform-compiler')
    LOC_BUTTON_CLOSE_EDITION_MODAL = (
        By.XPATH, '//a[contains(@class, "close-modal-new-edition")]')
    LOC_BUTTONS_EDIT_CATEGORIES = (
        By.XPATH, '//div[contains(@class, "tech-section-action")]/a')
    LOC_INPUT_NEW_COMPILER = (By.ID, 'review-change-compiler')
    LOC_INPUT_NEW_USER = (By.ID, 'review-search-user')
    LOC_INPUT_KEEP_COMPILER_AS_EDITOR = (By.NAME, 'change-compiler-keep-editor')
    LOC_INPUT_REVIEW_COMMENT = (By.NAME, 'message')
    LOC_INPUT_REJECT_COMMENT = (By.NAME, 'reject-message')
    LOC_INPUT_COMPILER_MESSAGE = (By.NAME, 'compiler_info_message')
    LOC_CHANGE_COMPILER_SELECTED = (
        By.XPATH,
        '//div[@id="review-new-compiler"]/div[contains(@class, "alert-box")]')
    LOC_COMPILER = (
        By.XPATH, '//ul[@class="tech-infos"]/li/span[text()="Compiler:"]/../a')
    LOC_EDITORS = (
        By.XPATH,
        # Can be "Editor/s:" ...
        '//ul[@class="tech-infos"]/li/span[contains(text(), "Editor")]/../a')
    LOC_CONTENT_DETAILS = (
        By.XPATH, '//div[contains(@class, "tech-section-content")]')
    LOC_LINK_DETAILS = (
        By.XPATH, '//div[contains(@class, "tech-links-content")]')
    LOC_LINKED_QUESTIONNAIRE_ENTRY = (
        By.XPATH, '//section[@id="links"]//article')
    LOC_LINKED_QUESTIONNAIRE_ENTRY_TITLE = (
        By.XPATH, '(//section[@id="links"]//article)[{i}]'
                  '//h2/a[contains(text(), "{title}")]')  # 1-based!
    LOC_LINKED_QUESTIONNAIRE_ENTRY_CONFIGURATION = (
        By.XPATH, '(//section[@id="links"]//article)[{i}]'
                  '//figcaption[contains(@class, "is-{configuration}")]')
    LOC_LINKED_QUESTIONNAIRE_LINK = (
        By.XPATH, '(//section[@id="links"]//article)[{index}]//h2/a')  # 1-based!
    LOC_STATUS_LABEL = (By.XPATH, '//span[contains(@class, "is-{status}")]')
    LOC_CREATION_DATE = (By.XPATH, '(//ul[contains(@class, "tech-infos")]/li/time)[1]')
    LOC_UPDATE_DATE = (By.XPATH, '(//ul[contains(@class, "tech-infos")]/li/time)[2]')
    TEXT_REVIEW_ACTION_CREATE_NEW_VERSION = 'Create new version'
    TEXT_REVIEW_ACTION_EDIT_QUESTIONNAIRE = 'Edit'
    TEXT_REVIEW_ACTION_SUBMIT_QUESTIONNAIRE = 'Submit'
    TEXT_REVIEW_ACTION_REVIEW_QUESTIONNAIRE = 'Approve'
    TEXT_REVIEW_ACTION_PUBLISH_QUESTIONNAIRE = 'Publish'
    TEXT_REVIEW_ACTION_CHANGE_COMPILER = 'Change compiler'
    TEXT_REVIEW_ACTION_DELETE_QUESTIONNAIRE = 'Delete'
    TEXT_MESSAGE_NO_VALID_NEW_COMPILER = 'No valid new compiler provided!'
    TEXT_MESSAGE_COMPILER_CHANGED = 'Compiler was changed successfully'
    TEXT_MESSAGE_USER_ALREADY_COMPILER = 'This user is already the compiler.'
    TEXT_NEW_EDITION_AVAILABLE = 'New edition of the questionnaire is available'

    def do_review_action(
            self, action: str, check_success: bool=True, message: str='',
            message_locator: tuple=None):
        btn_locator = self.format_locator(
            self.LOC_BUTTON_REVIEW_ACTION, action=action)
        elm = self.get_el(btn_locator)
        self.browser.execute_script("arguments[0].click();", elm)
        self.wait_for_modal()
        confirm_locator = self.format_locator(
            self.LOC_BUTTON_REVIEW_CONFIRM, action=action)
        self.wait_for(confirm_locator)
        if message:
            if not message_locator:
                message_locator = self.LOC_INPUT_REVIEW_COMMENT
            self.get_el(message_locator).send_keys(message)
        elm = self.get_el(confirm_locator)
        self.browser.execute_script("arguments[0].click();", elm)
        if check_success is True:
            assert self.has_success_message()

    def delete_questionnaire(self, check_success: bool=True):
        self.do_review_action('delete', check_success=check_success)

    def submit_questionnaire(self, check_success: bool=True, message: str=''):
        self.do_review_action(
            'submit', check_success=check_success, message=message)

    def review_questionnaire(self, check_success: bool=True, message: str=''):
        self.do_review_action(
            'review', check_success=check_success, message=message)

    def publish_questionnaire(self, check_success: bool=True, message: str=''):
        self.do_review_action(
            'publish', check_success=check_success, message=message)

    def reject_questionnaire(self, message: str, check_success: bool=True):
        self.do_review_action(
            'reject', check_success=check_success, message=message,
            message_locator=self.LOC_INPUT_REJECT_COMMENT)

    def finish_editing(self, check_success: bool=True, message: str=''):
        elm = self.get_el(self.LOC_BUTTON_FINISH_EDITING)
        self.browser.execute_script("arguments[0].click();", elm)
        self.wait_for_modal()
        self.wait_for(self.LOC_BUTTON_FINISH_EDITING_CONFIRM)
        if message:
            self.get_el(self.LOC_INPUT_COMPILER_MESSAGE).send_keys(message)
        elm = self.get_el(self.LOC_BUTTON_FINISH_EDITING_CONFIRM)
        self.browser.execute_script("arguments[0].click();", elm)
        if check_success is True:
            assert self.has_success_message()
            # Important: Wait for the modal to be hidden again, otherwise async
            # POST might not be finished yet.
            self.wait_for_modal(visibility=False)

    def get_review_actions(self) -> list:
        return [el.text for el in self.get_els(self.LOC_BUTTONS_REVIEW_ACTIONS)]

    def open_change_compiler_panel(self):
        elm = self.get_el(self.LOC_BUTTON_CHANGE_COMPILER_PANEL)
        self.browser.execute_script("arguments[0].click();", elm)

    def open_assign_user_panel(self):
        elm = self.get_el(self.LOC_BUTTON_ASSIGN_USER_PANEL)
        self.browser.execute_script("arguments[0].click();", elm)

    def click_change_compiler(self):
        self.wait_for(self.LOC_BUTTON_CHANGE_COMPILER)
        elm = self.get_el(self.LOC_BUTTON_CHANGE_COMPILER)
        self.browser.execute_script("arguments[0].click();", elm)

    def click_update_users(self):
        self.wait_for(self.LOC_BUTTON_CHANGE_USER)
        elm = self.get_el(self.LOC_BUTTON_CHANGE_USER)
        self.browser.execute_script("arguments[0].click();", elm)

    def assign_user(self, user: str):
        self.open_assign_user_panel()
        self.get_el(self.LOC_INPUT_NEW_USER).send_keys(
            user.split(' ')[0])
        self.select_autocomplete(self.browser, user)
        self.click_update_users()

    def remove_user(self, editor: str):
        self.hide_notifications()
        self.open_assign_user_panel()
        elm = self.get_el(self.format_locator(
            self.LOC_BUTTON_REMOVE_USER, user=editor))
        self.browser.execute_script("arguments[0].click();", elm)
        self.click_update_users()

    def change_compiler(
            self, compiler: str, keep_as_editor: bool=False, submit: bool=True):
        self.hide_notifications()
        self.open_change_compiler_panel()
        self.get_el(self.LOC_INPUT_NEW_COMPILER).send_keys(
            compiler.split(' ')[0])
        self.select_autocomplete(self.browser, compiler)
        if keep_as_editor is True:
            self.select_keep_compiler_as_editor()
        if submit is True:
            self.click_change_compiler()

    def select_keep_compiler_as_editor(self):
        elm = self.get_el(self.LOC_INPUT_KEEP_COMPILER_AS_EDITOR)
        self.browser.execute_script("arguments[0].click();", elm)

    def can_enter_new_compiler(self) -> bool:
        return not self.get_el(
            self.LOC_INPUT_NEW_COMPILER).get_attribute('disabled')

    def get_selected_compilers(self) -> list:
        return [
            el.text.replace('\n×', '') for el in
            self.get_els(self.LOC_CHANGE_COMPILER_SELECTED)]

    def can_submit_questionnaire(self) -> bool:
        return self.TEXT_REVIEW_ACTION_SUBMIT_QUESTIONNAIRE in \
               self.get_review_actions()

    def can_review_questionnaire(self) -> bool:
        return self.TEXT_REVIEW_ACTION_REVIEW_QUESTIONNAIRE in \
               self.get_review_actions()

    def can_publish_questionnaire(self) -> bool:
        return self.TEXT_REVIEW_ACTION_PUBLISH_QUESTIONNAIRE in \
               self.get_review_actions()

    def can_change_compiler(self) -> bool:
        return self.TEXT_REVIEW_ACTION_CHANGE_COMPILER in \
               self.get_review_actions()

    def can_delete_questionnaire(self) -> bool:
        return self.TEXT_REVIEW_ACTION_DELETE_QUESTIONNAIRE in \
               self.get_review_actions()

    def get_compiler(self) -> str:
        """From the details view, return the name of the compiler"""
        return self.get_el(self.LOC_COMPILER).text

    def get_editors(self) -> list:
        """From the details view, return the names of the editors"""
        return [el.text for el in self.get_els(self.LOC_EDITORS)]

    def check_status(self, status: str):
        self.get_el(self.format_locator(self.LOC_STATUS_LABEL, status=status))

    def check_review_actions(
            self, create_new: bool, edit: bool, submit: bool, review: bool,
            publish: bool, delete: bool, change_compiler: bool):
        review_actions = self.get_review_actions()
        assert (self.TEXT_REVIEW_ACTION_CREATE_NEW_VERSION in review_actions) \
                is create_new
        assert (self.TEXT_REVIEW_ACTION_EDIT_QUESTIONNAIRE in review_actions) \
                is edit
        assert (self.TEXT_REVIEW_ACTION_SUBMIT_QUESTIONNAIRE in review_actions)\
                is submit
        assert (self.TEXT_REVIEW_ACTION_REVIEW_QUESTIONNAIRE in review_actions)\
                is review
        assert (self.TEXT_REVIEW_ACTION_PUBLISH_QUESTIONNAIRE in review_actions)\
                is publish
        assert (self.TEXT_REVIEW_ACTION_DELETE_QUESTIONNAIRE in review_actions)\
                is delete
        assert (self.TEXT_REVIEW_ACTION_CHANGE_COMPILER in review_actions) \
                is change_compiler

    def can_edit_category(self, keyword: str) -> bool:
        category_buttons = self.get_els(self.LOC_BUTTONS_EDIT_CATEGORIES)
        for cat in category_buttons:
            if keyword in cat.get_attribute('href'):
                return True
        return False

    def expand_details(self):
        for el in self.get_els(self.LOC_LINK_DETAILS):
            self.show_element(el)
        for el in self.get_els(self.LOC_CONTENT_DETAILS):
            self.show_element(el)

    def close_edition_modal(self):
        elm = self.get_el(self.LOC_BUTTON_CLOSE_EDITION_MODAL)
        self.browser.execute_script("arguments[0].click();", elm)
        self.wait_for_modal(visibility=False)

    def has_new_edition(self) -> bool:
        return self.has_text(self.TEXT_NEW_EDITION_AVAILABLE)

    def count_linked_questionnaires(self) -> int:
        return len(self.get_els(self.LOC_LINKED_QUESTIONNAIRE_ENTRY))

    def check_linked_questionnaires(self, expected: list, count: bool=True):
        """
        Args:
            expected: list of dicts. Can contain
                - title
            count: bool. Check whether length of expected list matches length of
                actual list results.
        """
        if count is True:
            assert self.count_linked_questionnaires() == len(expected)
        for i, e in enumerate(expected):
            i_xpath = i + 1
            if e.get('title'):
                locator = self.format_locator(
                    self.LOC_LINKED_QUESTIONNAIRE_ENTRY_TITLE, i=i_xpath,
                    title=e['title'])
                self.get_el(locator)
            if e.get('configuration'):
                locator = self.format_locator(
                    self.LOC_LINKED_QUESTIONNAIRE_ENTRY_CONFIGURATION,
                    i=i_xpath, configuration=e['configuration'])
                self.get_el(locator)

    def click_linked_questionnaire(self, index: int):
        self.get_el(
            self.format_locator(
                self.LOC_LINKED_QUESTIONNAIRE_LINK, index=index + 1)
        ).click()


class EditMixin(ReviewMixin):

    LOC_CATEGORIES_PROGRESS_INDICATORS = (
        By.XPATH, '//div[@class="tech-section-progress"]')
    LOC_CATEGORY_TITLE = (By.XPATH, '//h2[contains(text(), "{category}")]')
    LOC_BUTTON_EDIT_CATEGORY = (
        By.XPATH, '//div[contains(@class, "tech-section-action")]/a['
                  'contains(@href, "/edit/") and contains(@href, "{keyword}")]')
    LOC_BUTTON_VIEW_QUESTIONNAIRE = (
        By.XPATH, '//div[contains(@class, "review-panel")]//a[contains(@class, '
                  '"success") and contains(@href, "/view/")]')

    def get_progress_indicators(self):
        return self.get_els(self.LOC_CATEGORIES_PROGRESS_INDICATORS)

    def get_category_by_name(self, name: str):
        locator = self.format_locator(self.LOC_CATEGORY_TITLE, category=name)
        return self.get_el(locator)

    def click_edit_category(self, driver, keyword: str):
        self.hide_notifications()
        locator = self.format_locator(
            self.LOC_BUTTON_EDIT_CATEGORY, keyword=keyword)
        elm = self.get_el(locator)
        driver.execute_script("arguments[0].click();", elm)

    def view_questionnaire(self, driver):
        elm = self.get_el(self.LOC_BUTTON_VIEW_QUESTIONNAIRE)
        driver.execute_script("arguments[0].click();", elm)
        assert self.has_success_message()


class DetailMixin(ReviewMixin):

    LOC_BUTTON_CREATE_NEW_VERSION = (
        By.XPATH, '//input[@type="submit" and @value="Create new version"]')
    LOC_BUTTON_EDIT_QUESTIONNAIRE = (
        By.XPATH, '//div[contains(@class, "review-panel")]//a[contains(@class, '
                  '"button") and contains(@href, "/edit/")]')
    TEXT_IS_LOCKED_BY = 'This questionnaire is locked for editing by {user}.'

    def create_new_version(self):
        btn_locator = self.format_locator(
            EditMixin.LOC_BUTTON_REVIEW_ACTION, action='edit')
        elm = self.get_el(btn_locator)
        self.browser.execute_script("arguments[0].click();", elm)
        self.wait_for_modal()
        confirm_locator = self.LOC_BUTTON_CREATE_NEW_VERSION
        self.wait_for(confirm_locator)
        elm = self.get_el(confirm_locator)
        self.browser.execute_script("arguments[0].click();", elm)
        assert self.has_success_message()

    def edit_questionnaire(self):
        elm = self.get_el(self.LOC_BUTTON_EDIT_QUESTIONNAIRE)
        self.browser.execute_script("arguments[0].click();", elm)
        assert self.has_success_message()

    def can_create_new_version(self):
        return self.TEXT_REVIEW_ACTION_CREATE_NEW_VERSION in \
               self.get_review_actions()

    def can_edit_questionnaire(self):
        return self.TEXT_REVIEW_ACTION_EDIT_QUESTIONNAIRE in \
               self.get_review_actions()

    def is_locked_by(self, user) -> bool:
        return self.has_warning_message(
            self.TEXT_IS_LOCKED_BY.format(user=user))


class PaginationMixin:
    LOC_PAGINATION_PREVIOUS = (
        By.XPATH, '//ul[@class="pagination"]/li[contains(@class, "arrow")]/a['
                  'text()="«"]/..')
    LOC_PAGINATION_CURRENT = (
        By.XPATH, '//ul[@class="pagination"]/li[contains(@class, "current")]')
    LOC_PAGINATION_CURRENT_PAGE = (
        By.XPATH, '//ul[@class="pagination"]/li[contains(@class, "current")]/'
                  'a[text()="{page}"]')
    LOC_PAGINATION_PAGE_LINK = (
        By.XPATH, '//ul[@class="pagination"]/li/a[text()="{page}"]')
    CLASS_IS_UNAVAILABLE = 'unavailable'

    def is_prev_page_disabled(self) -> bool:
        return self.CLASS_IS_UNAVAILABLE in self.get_el(
            self.LOC_PAGINATION_PREVIOUS).get_attribute('class')

    def get_current_page(self) -> int:
        return int(self.get_el(self.LOC_PAGINATION_CURRENT).text)

    def click_page(self, page: int):
        elm = self.get_el(
            self.format_locator(self.LOC_PAGINATION_PAGE_LINK, page=page)
        )
        self.browser.execute_script("arguments[0].click();", elm)
        self.wait_for(
            self.format_locator(self.LOC_PAGINATION_CURRENT_PAGE, page=page))
