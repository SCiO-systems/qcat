from django.urls import reverse
from django.test.client import RequestFactory

from apps.accounts.tests.test_models import create_new_user
from apps.qcat.tests import TestCase

route_questionnaire_details = 'sample:questionnaire_details'
route_home = 'sample:home'
route_questionnaire_link_search = 'sample:questionnaire_link_search'
route_questionnaire_list = 'sample:questionnaire_list'
route_questionnaire_filter = 'wocat:questionnaire_filter'
route_questionnaire_list_partial = 'sample:questionnaire_list_partial'
route_questionnaire_new = 'sample:questionnaire_new'
route_questionnaire_new_step = 'sample:questionnaire_new_step'


def get_valid_new_step_values():
    args = (get_categories()[0][0], 'sample', 'sample')
    kwargs = {'page_title': 'SAMPLE Form', 'identifier': 'new'}
    return args, kwargs


def get_valid_new_values():
    args = ('sample', 'sample/questionnaire/details.html', 'sample')
    kwargs = {'identifier': None}
    return args, kwargs


def get_valid_details_values():
    return ('foo', 'sample', 'sample')


def get_valid_list_values():
    return ('sample', 'sample/questionnaire/list.html')


def get_category_count():
    return len(get_categories())


def get_section_count():
    return len(get_sections())


def get_categories():
    return (
        ('cat_0', 'Category 0'),
        ('cat_1', 'Category 1'),
        ('cat_2', 'Category 2'),
        ('cat_3', 'Category 3'),
        ('cat_4', 'Category 4'),
        ('cat_5', 'Category 5'),
    )


def get_sections():
    return (
        ('section_1', 'Section 1'),
        ('section_2', 'Section 2'),
    )


def get_position_of_category(category, start0=False):
    for i, cat in enumerate(get_categories()):
        if cat[0] == category:
            if start0 is True:
                return i
            else:
                return i + 1
    return None


class SampleHomeTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(route_home)

    def test_renders_correct_template(self):
        res = self.client.get(self.url)
        self.assertTemplateUsed(res, 'sample/home.html')
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
        'sample',
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
        'sample_global_key_values',
        'sample',
        'sample_questionnaires',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(
            route_questionnaire_details, kwargs={'identifier': 'sample_1'})

    def test_renders_correct_template(self):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'questionnaire/details.html')
        self.assertEqual(res.status_code, 200)
