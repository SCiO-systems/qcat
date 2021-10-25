from apps.qcat.tests import TestCase
from apps.questionnaire.templatetags.list_to_columns import (
    columnize,
)
from apps.questionnaire.templatetags.clean_language_url import clean_url


def get_list_of_elements():
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


class ColumnizeTest(TestCase):

    def test_returns_columns_times_list(self):
        cols = columnize(get_list_of_elements(), 2)
        self.assertEqual(len(cols), 2)
        cols = columnize(get_list_of_elements(), 5)
        self.assertEqual(len(cols), 5)
        cols = columnize(get_list_of_elements(), 11)
        self.assertEqual(len(cols), 11)

    def test_uneven_divisions_are_filled_up_front(self):
        cols = columnize(get_list_of_elements(), 3)
        self.assertEqual(len(cols[0]), 4)
        self.assertEqual(len(cols[1]), 3)
        self.assertEqual(len(cols[2]), 3)


class CleanUrlTest(TestCase):

    def test_returns_url_without_language_prefix(self):
        url = '/en/foo'
        self.assertEqual(clean_url(url), '/foo')

    def test_returns_url_unchanged_if_no_language_prefix(self):
        url = '/foo'
        self.assertEqual(clean_url(url), url)

    def test_do_not_remove_prefix_if_elsewehere_in_url(self):
        url = '/foo/en/bar'
        self.assertEqual(clean_url(url), url)

    def test_handle_full_url(self):
        url = 'http://qcat.wocat.net/en/foo'
        self.assertEqual(clean_url(url), 'http://qcat.wocat.net/foo')

    def test_handle_trailing_slash(self):
        url = '/en/foo/'
        self.assertEqual(clean_url(url), '/foo/')

    def test_handle_empty_url(self):
        url = '/'
        self.assertEqual(clean_url(url), url)

    def test_handle_empty_url_2(self):
        url = ''
        self.assertEqual(clean_url(url), url)

    def test_handle_invalid_url(self):
        url = None
        self.assertEqual(clean_url(url), url)
