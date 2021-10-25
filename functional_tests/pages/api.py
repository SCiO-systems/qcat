import json

from functional_tests.pages.base import ApiPage


class ApiV2ListPage(ApiPage):
    route_name = 'v2:questionnaires-api-list'

    def _get_json(self):
        return json.loads(self.browser.find_element_by_tag_name('body').text)

    def _get_list_results(self) -> list:
        return self._get_json()['results']

    def count_list_results(self) -> int:
        """ Returns the paginated (!) count of the current list. """
        return len(self._get_list_results())

    def check_list_results(self, expected: list, count: bool=True):
        # Must be in JSON format.
        if count is True:
            assert self.count_list_results() == len(expected)
        list_results = self._get_list_results()
        for i, e in enumerate(expected):
            if e.get('title'):
                assert list_results[i]['name'] == e['title']

            # Description is not part of the API list view.
            # Status: API only shows public questionnaires.

            for lang in e.get('translations', []):
                assert lang in [t[0] for t in list_results[i]['translations']]
