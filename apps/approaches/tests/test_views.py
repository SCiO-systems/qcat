from django.urls import reverse
from django.test.client import RequestFactory

from apps.accounts.tests.test_models import create_new_user
from apps.qcat.tests import TestCase


route_home = 'approaches:home'
route_questionnaire_details = 'approaches:questionnaire_details'
route_questionnaire_new = 'approaches:questionnaire_new'
route_questionnaire_new_step = 'approaches:questionnaire_new_step'


def get_valid_details_values():
    return ('foo', 'approaches', 'approaches')


def get_valid_link_form_values():
    args = ('approaches', 'approaches')
    kwargs = {'page_title': 'Approach Links', 'identifier': 'foo'}
    return args, kwargs


def get_valid_new_values():
    args = (
        'approaches', 'approaches/questionnaire/details.html',
        'approaches')
    kwargs = {'identifier': None}
    return args, kwargs


def get_valid_new_step_values():
    args = (get_categories()[0][0], 'approaches', 'approaches')
    kwargs = {'page_title': 'Approaches Form', 'identifier': 'new'}
    return args, kwargs


def get_category_count():
    return len(get_categories())


def get_categories():
    return (
        ('app__1', 'General information'),
        ('app__2', 'Description of the SLM Approach'),
        ('app__3', 'Participation and roles of stakeholders involved'),
        ('app__4', 'Technical support, capacity building, and knowledge '
                   'management'),
        ('app__5', 'Financing and external material support'),
        ('app__6', 'Impact analysis and concluding statements'),
        ('app__7', 'References and links'),
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
        'approaches',
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
        'approaches',
        'approaches_questionnaires',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(
            route_questionnaire_details, kwargs={'identifier': 'app_1'})

    def test_renders_correct_template(self):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'questionnaire/details.html')
        self.assertEqual(res.status_code, 200)
