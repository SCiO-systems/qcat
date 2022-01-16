from functional_tests.base import FunctionalTest
from functional_tests.pages.qcat import HomePage


class TranslationTest(FunctionalTest):

    def test_change_languages(self):
        # A user can change the language in the top menu. The same page is
        # reloaded, language is switched.

        # User loads the page
        page = HomePage(self)
        page.open()

        # The page is in English
        assert page.has_text('Home')

        en_url = self.browser.current_url

        # User changes the language
        page.change_language('es', self.browser)

        # The language has changed.
        assert page.has_text('Inicio')

        # The URL is basically still the same, save for the language prefix
        es_url = self.browser.current_url
        assert en_url.replace('/en/', '/es/') == es_url
