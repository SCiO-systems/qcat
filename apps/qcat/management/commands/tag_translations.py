"""
Automated browser script to tag translations in Transifex.

If translation strings are tagged in Transifex, translators can selectively
translate only parts of the application (e.g. only questionnaire on
Technologies), which was often requested. This script was initially used to tag
all 3000+ strings and can be used to update tags for new translation strings.

This script is not used regularly and therefore not thoroughly tested. It works
best when it can process a shrinking list so it is able to continue after
restarting the script.

Suggested procedure to tag new translations:
In Transifex, filter strings by "Source updated after" to get a list of new
translations. Select and tag them all (e.g. tag "Untagged"). The script below
uses a Transifex link filtered by this tag and will process this list until no
more "Untagged" strings left.

Usage:
    python manage.py tag_translations [-v 2]
"""

from getpass import getpass

from django.conf import settings
from django.core.management import BaseCommand
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

driver = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver")


class Command(BaseCommand):
    help = 'Automated browser script to tag translations in Transifex.'

    # Transifex URL filtered by tag "Untagged"
    transifex_url = 'https://www.transifex.com/university-of-bern-cde/qcat/translate/#fr/website/82107202?q=tags%3ATechnologies'

    # Transifex URL for the entire list (unfiltered)
    # transifex_url = 'https://www.transifex.com/university-of-bern-cde/qcat/translate/#fr/website/82107202'

    # Map contexts to tags
    map_context_to_tags = {
        # Notice the space at the end of the key! Checks are done with
        # str.startswith(key)
        'approaches ': ['Approaches', '2015'],
        'cca ': ['CCA', '2015'],
        'cbp ': ['CBP', '2015'],
        'technologies ': ['Technologies', '2015'],
        'technologies_2018': ['Technologies', '2018'],
        'unccd ': ['UNCCD', '2015'],
        'watershed ': ['Watershed', '2015'],
        'wocat ': ['WOCAT', '2015', 'Technologies', 'Approaches'],
        'None': ['Application'],
        # Special contexts ...
        'Jay wrote you a message': ['Application'],
        "New status of the questionnaire, e.g. 'published'": ['Application'],
        'A questionnaire was rejected by...': ['Application'],
        'A questionnaire was approved by...': ['Application'],
    }

    # Element locators
    loc_input_username = (By.ID, 'id_identification')
    loc_input_password = (By.ID, 'id_password')
    loc_button_login = (By.XPATH, '//input[@type="submit"]')
    loc_translation_entries = (
        By.XPATH, '//div[contains(@class, "string-trans")]')
    loc_context = (By.XPATH, '//div[text()="Context"]/../div[2]')
    loc_entries_container = (By.XPATH, '//div[@id="string-list"]/..')
    loc_selected_entry = (
        By.XPATH,
        '//div[contains(@class, "js-stringlist-item") and '
        'contains(@class, "string-selected")]')
    loc_selected_entry_string = (
        By.XPATH,
        '//div[contains(@class, "js-stringlist-item") and contains(@class, '
        '"string-selected")]//div[contains(@class, "default-source-text")]')
    loc_entry_tags = (By.XPATH, '//span[contains(@class, "tagitem")]')
    loc_button_edit_context = (
        By.XPATH, '//a[contains(@class, "js-edit-context")]')
    loc_button_save_context = (
        By.XPATH,
        '//div[@class="facebox-content"]//a[contains(@class, "js-save")]')
    loc_input_tag = (
        By.XPATH,
        '//div[@class="facebox-content"]//input[contains(@class, '
        '"c-taglist__input")]')
    loc_button_delete_tags = (
        By.XPATH, '//span[contains(@class, "js-remove-tag")]')
    loc_context_key = (
        By.XPATH,
        '//div[@id="details-area"]//div[text()="Key"]/../span[contains(text(), '
        '"{key}")]')
    loc_overlay = (By.ID, 'facebox_overlay')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entry_id_list = []

    def handle(self, *args, **options):

        # User input
        username = input('Transifex username: ')
        password = getpass(prompt='Transifex password: ')

        # Set up a browser
        self.browser = webdriver.Chrome(
            executable_path=settings.TESTING_CHROMEDRIVER_PATH)
        self.browser.implicitly_wait(3)
        self.verbosity = options['verbosity']

        # Log in to Transifex
        self.open_transifex(username, password)

        # Wait for the first selected translation
        try:
            self.wait_for(self.loc_selected_entry)
        except TimeoutException:
            # Sometimes, no initial element is selected. In this case, use the
            # key shortcut to select the first and try to wait again.
            ActionChains(self.browser).send_keys(
                Keys.CONTROL, Keys.DOWN).perform()
            self.wait_for(self.loc_selected_entry)

        while self.process_current_entry() is not False:
            # Select next (for some reason this has to be executed twice)
            ActionChains(self.browser).send_keys(
                Keys.CONTROL, Keys.DOWN).perform()
            ActionChains(self.browser).send_keys(
                Keys.CONTROL, Keys.DOWN).perform()

        self.output(f'Looked through {len(self.entry_id_list)} translations.')

        self.browser.quit()

    def process_current_entry(self) -> False or None:
        """
        Process a single translation entry. Returns False if the entry was
        already processed (e.g. when starting again from the top of the list)
        """
        entry = self.browser.find_element(*self.loc_selected_entry)

        # Keep track of all visited IDs as looping through the list with the
        # keyboard shortcut will start again from the top after the last
        # element.
        entry_id = entry.get_attribute('source-entity-id')
        if entry_id in self.entry_id_list:
            return False
        else:
            self.entry_id_list.append(entry_id)

        # It is necessary to wait for the info panel to load. Check if the
        # string is listed there (as Key). However, the string has HTML tags
        # displayed differently while the Key in the info panel has them as raw
        # HTML. Therefore use only text outside of the HTML tags to check if the
        # string is available in the info panel.
        string_element = self.browser.find_element(
            *self.loc_selected_entry_string)
        string = string_element.text
        string_texts = self.get_text_parts_without_children(string_element)
        key_locator = self.loc_context_key
        try:
            self.wait_for((key_locator[0], key_locator[1].format(
                key=string_texts[0].split('"')[0])))
        except TimeoutException:
            # For some reason, this works better when pressing the shortcut 2x
            ActionChains(self.browser).send_keys(
                Keys.CONTROL, Keys.UP).perform()
            ActionChains(self.browser).send_keys(
                Keys.CONTROL, Keys.DOWN).perform()
            return self.process_current_entry()

        # Get the context and the mapped tags for it.
        context = self.browser.find_element(*self.loc_context).text
        matching_tags_key = next(
            (t for t in self.map_context_to_tags.keys()
             if context.startswith(t)),
            None)
        try:
            matching_tags = self.map_context_to_tags[matching_tags_key]
        except KeyError:
            raise Exception(
                f'No tag found in mapping for for context "{context}"')

        # Some output if desired.
        if self.verbosity > 1:
            string_short = (string[:75] + '...') if len(string) > 75 else string
            self.output(f'Current string: [{entry_id} / '
                        f'{len(self.entry_id_list)}] {string_short}')
            self.output(f'... Context: {context}')
            self.output(f'... Matching tags: {matching_tags}')

        # Check for existing tags.
        existing_tags = [
            el.text for el in self.browser.find_elements(*self.loc_entry_tags)]
        if self.verbosity > 1:
            if existing_tags:
                self.output(f'... Found existing tags: {existing_tags}')

        # If the item is already tagged correctly, return early.
        if sorted(matching_tags) == sorted(existing_tags):
            if self.verbosity > 1:
                self.output(f'... Already tagged correctly, do nothing')
            return

        # If there are incorrect existing tags, remove them all.
        elif existing_tags:
            self.browser.find_element(*self.loc_button_edit_context).click()
            self.wait_for(self.loc_input_tag)

            # Remove every single tag until there are none left.
            tag_btn_delete_list = self.browser.find_elements(
                *self.loc_button_delete_tags)
            while tag_btn_delete_list:
                tag_btn_delete_list[0].click()
                tag_btn_delete_list = self.browser.find_elements(
                    *self.loc_button_delete_tags)

            if self.verbosity > 1:
                self.output(f'... Matching tags did not match existing tags. '
                            f'Removed all old tags.')

            # Close the popup only if there are no matching tags.
            if not matching_tags:
                self.save_close_context()

        # Add new tags.
        if matching_tags:
            # If there were existing tags, the popup is already open.
            if not existing_tags:
                self.browser.find_element(*self.loc_button_edit_context).click()
                self.wait_for(self.loc_input_tag)

            # Add each tag.
            input_field = self.browser.find_element(*self.loc_input_tag)
            for tag in matching_tags:
                input_field.send_keys(tag)
                input_field.send_keys(Keys.ENTER)

            # Save and close popup.
            self.save_close_context()

        if self.verbosity > 1:
            self.output(f'... Added tags {matching_tags}')

    def open_transifex(self, username: str, password: str):
        """Open Transifex and log in."""
        self.browser.get(self.transifex_url)
        # Login
        self.browser.find_element(*self.loc_input_username).send_keys(username)
        self.browser.find_element(*self.loc_input_password).send_keys(password)
        self.browser.find_element(*self.loc_button_login).click()

    def save_close_context(self):
        """Save and close the popup where the context is edited."""
        self.browser.find_element(*self.loc_button_save_context).click()
        self.wait_for(self.loc_overlay, visibility=False)

    def wait_for(self, locator: tuple, visibility: bool=True):
        """Wait for the (in)visibility of an element."""
        if visibility is True:
            condition = expected_conditions.visibility_of_element_located(
                locator)
        else:
            condition = expected_conditions.invisibility_of_element_located(
                locator)
        WebDriverWait(self.browser, 10).until(condition)

    def get_text_parts_without_children(self, element: WebElement) -> list:
        """
        Return a list of all texts of the current element, exclude child tags.
        Adapted from: https://stackoverflow.com/a/19040341
        """
        return self.browser.execute_script("""
            var parent = arguments[0];
            var child = parent.firstChild;
            var ret = [];
            while (child) {
                if (child.nodeType === Node.TEXT_NODE)
                    ret.push(child.textContent);
                child = child.nextSibling;
            }
            return ret;
        """, element)

    def output(self, msg):
        """Shortcut to write output."""
        self.stdout.write(msg)
