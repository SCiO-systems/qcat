from django.urls import reverse
from django.test.client import RequestFactory
from unittest.mock import patch, Mock

from apps.accounts.tests.test_models import create_new_user
from apps.qcat.tests import TestCase

route_questionnaire_details = 'samplemulti:questionnaire_details'
route_home = 'samplemulti:home'
route_questionnaire_link_search = 'samplemulti:questionnaire_link_search'
route_questionnaire_list = 'samplemulti:questionnaire_list'
route_questionnaire_list_partial = 'samplemulti:questionnaire_list_partial'
route_questionnaire_new = 'samplemulti:questionnaire_new'
route_questionnaire_new_step = 'samplemulti:questionnaire_new_step'


def get_valid_link_form_values():
    args = ('samplemulti', 'samplemulti')
    kwargs = {'page_title': 'SAMPLEMULTI Links', 'identifier': 'foo'}
    return args, kwargs


def get_valid_new_step_values():
    args = (get_categories()[0][0], 'samplemulti', 'samplemulti')
    kwargs = {'page_title': 'SAMPLEMULTI Form', 'identifier': 'new'}
    return args, kwargs


def get_valid_new_values():
    args = (
        'samplemulti', 'questionnaire/details.html', 'samplemulti')
    kwargs = {'identifier': None}
    return args, kwargs


def get_valid_details_values():
    return ('foo', 'samplemulti', 'samplemulti')


def get_valid_list_values():
    return ('samplemulti', 'samplemulti/questionnaire/list.html')


def get_category_count():
    return len(get_categories())


def get_section_count():
    return len(get_sections())


def get_categories():
    return (
        ('mcat_1', 'MCategory 1'),
    )


def get_sections():
    return (
        ('msection_1', 'MSection 1'),
    )


def get_position_of_category(category, start0=False):
    for i, cat in enumerate(get_categories()):
        if cat[0] == category:
            if start0 is True:
                return i
            else:
                return i + 1
    return None


class SampleMultiHomeTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(route_home)

    def test_renders_correct_template(self):
        res = self.client.get(self.url)
        self.assertTemplateUsed(res, 'samplemulti/home.html')
        self.assertEqual(res.status_code, 200)


class QuestionnaireNewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(route_questionnaire_new)
        self.request = self.factory.get(self.url)
        self.request.user = create_new_user()
        self.request.session = {}

    def test_questionnaire_new_login_required(self):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'login.html')


class QuestionnaireNewStepTest(TestCase):

    fixtures = [
        'groups_permissions',
        'global_key_values',
        'samplemulti',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(
            route_questionnaire_new_step, kwargs={
                'identifier': 'new', 'step': get_categories()[0][0]})
        self.request = self.factory.get(self.url)
        self.request.user = create_new_user()
        self.request.session = {}

    def test_questionnaire_new_step_login_required(self):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'login.html')


class QuestionnaireDetailsTest(TestCase):

    fixtures = [
        'groups_permissions',
        'global_key_values',
        'samplemulti',
        'samplemulti_questionnaires',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(
            route_questionnaire_details, kwargs={
                'identifier': 'samplemulti_1'})

    def test_renders_correct_template(self):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'questionnaire/details.html')
        self.assertEqual(res.status_code, 200)
