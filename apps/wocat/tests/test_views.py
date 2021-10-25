from django.urls import reverse
from django.test.client import RequestFactory

from apps.qcat.tests import TestCase


route_home = 'wocat:home'
route_questionnaire_list = 'wocat:questionnaire_list'
route_questionnaire_list_partial = 'wocat:questionnaire_list_partial'


def get_valid_details_values():
    return (1, 'wocat', 'wocat', 'wocat/questionnaire/details.html')


def get_valid_list_values():
    return ('wocat', 'wocat/questionnaire/list.html')


class WocatHomeTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(route_home)

    def test_renders_correct_template(self):
        res = self.client.get(self.url)
        self.assertTemplateUsed(res, 'wocat/home.html')
        self.assertEqual(res.status_code, 200)
