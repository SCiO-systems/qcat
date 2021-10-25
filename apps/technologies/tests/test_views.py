from django.urls import reverse
from django.test.client import RequestFactory
from unittest.mock import patch, Mock

from apps.accounts.tests.test_models import create_new_user
from apps.qcat.tests import TestCase


route_home = 'technologies:home'
route_questionnaire_details = 'technologies:questionnaire_details'
route_questionnaire_list = 'technologies:questionnaire_list'
route_questionnaire_list_partial = 'technologies:questionnaire_list_partial'
route_questionnaire_new = 'technologies:questionnaire_new'
route_questionnaire_new_step = 'technologies:questionnaire_new_step'


def get_valid_details_values():
    return ('foo', 'technologies', 'technologies')


def get_valid_link_form_values():
    args = ('technologies', 'technologies')
    kwargs = {'page_title': 'Technology Links', 'identifier': 'foo'}
    return args, kwargs


def get_valid_new_values():
    args = (
        'technologies', 'questionnaire/details.html',
        'technologies')
    kwargs = {'identifier': None}
    return args, kwargs


def get_valid_new_step_values():
    args = (get_categories()[0][0], 'technologies', 'technologies')
    kwargs = {'page_title': 'Technologies Form', 'identifier': 'new'}
    return args, kwargs


def get_category_count():
    return len(get_categories())


def get_categories():
    return (
        ('tech__1', 'General information'),
        ('tech__2', 'Description of the SLM Technology'),
        ('tech__3', 'Classification of the SLM Technology'),
        ('tech__4', 'Technical specifications, implementation activities, '
                    'inputs, and costs'),
        ('tech__5', 'Natural and human environment'),
        ('tech__6', 'Impacts and concluding statements'),
        ('tech__7', 'References and links'),
    )


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
        'technologies',
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
        'technologies',
        'technologies_questionnaires',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(
            route_questionnaire_details, kwargs={'identifier': 'tech_1'})

    def test_renders_correct_template(self):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'questionnaire/details.html')
        self.assertEqual(res.status_code, 200)
