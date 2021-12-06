from django.urls import reverse
from django.test.client import RequestFactory

from apps.accounts.tests.test_models import create_new_user
from apps.qcat.tests import TestCase


route_home = 'unccd:home'
route_questionnaire_details = 'unccd:questionnaire_details'
route_questionnaire_list = 'unccd:questionnaire_list'
route_questionnaire_list_partial = 'unccd:questionnaire_list_partial'
route_questionnaire_new = 'unccd:questionnaire_new'
route_questionnaire_new_step = 'unccd:questionnaire_new_step'


def get_valid_new_step_values():
    args = (get_categories()[0][0], 'unccd', 'unccd')
    kwargs = {'page_title': 'UNCCD Form', 'identifier': 'new'}
    return args, kwargs


def get_valid_new_values():
    args = ('unccd', 'questionnaire/details.html', 'unccd')
    kwargs = {'identifier': None}
    return args, kwargs


def get_valid_details_values():
    return ('foo', 'unccd', 'unccd')


def get_valid_list_values():
    return ('unccd', 'unccd/questionnaire/list.html')


def get_category_count():
    return len(get_categories())


def get_categories():
    return (
        ('unccd_0_general_information', 'General Information'),
        ('unccd_0_classification', 'Classification'),
        ('unccd_1_context', 'Section 1: ...'),
        ('unccd_2_problems_addressed', 'Section 2: ...'),
        ('unccd_3_activities', 'Section 3: ...'),
        ('unccd_4_actors_involved', 'Section 4: ...'),
        ('unccd_5_impact', 'Section 5: ...'),
        ('unccd_6_adoption_replicability', 'Section 6: ...'),
        ('unccd_7_lessons_learned', 'Section 7: ...'),
        ('unccd_8_questions_leg1', 'Section 8: ...'),
    )


class UnccdHomeTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(route_home)

    def test_redirect(self):
        res = self.client.get(self.url)
        self.assertRedirects(res, '/en/wocat/')


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
        'unccd',
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
        'unccd',
        'unccd_questionnaires',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(
            route_questionnaire_details, kwargs={'identifier': 'unccd_1'})

    def test_renders_correct_template(self):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'questionnaire/details.html')
        self.assertEqual(res.status_code, 200)
