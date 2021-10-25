import json

from apps.configuration.cache import get_cached_configuration
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.http import Http404
from django.test.client import RequestFactory
from unittest.mock import patch, Mock, MagicMock

from apps.accounts.tests.test_models import create_new_user
from apps.configuration.configuration import (
    QuestionnaireConfiguration,
)
from apps.qcat.tests import TestCase
from apps.questionnaire.models import File, Questionnaire
from apps.questionnaire.views import (
    generic_file_upload,
    QuestionnaireEditView,
    QuestionnaireStepView,
    QuestionnaireView, QuestionnaireLinkSearchView)

file_upload_route = 'file_upload'
file_display_route = 'file_serve'
valid_file = 'static/assets/img/img01.jpg'
invalid_file = 'bower.json'  # Needs to exist but not valid file type


class GenericFileUploadTest(TestCase):

    fixtures = [
        'groups_permissions',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(file_upload_route)
        self.request = self.factory.post(self.url)
        self.request.user = create_new_user()
        self.request.session = {}
        self.mock_request = Mock()
        self.mock_request.method = 'POST'
        self.mock_request.session = {}
        self.mock_request.user = self.request.user
        self.mock_request.FILES.getlist.return_value = [Mock()]

    def test_upload_login_required(self):
        self.client.logout()
        res = self.client.post(self.url, follow=True)
        self.assertTemplateUsed(res, 'login.html')

    def test_upload_only_post_allowed(self):
        res = generic_file_upload(self.request)
        self.assertEqual(res.status_code, 400)

    def test_handles_post_without_files(self):
        res = generic_file_upload(self.request)
        self.assertEqual(res.status_code, 400)
        content = json.loads(res.content.decode('utf-8'))
        self.assertFalse(content.get('success'))

    @patch.object(File, 'get_data')
    @patch.object(File, 'handle_upload')
    def test_calls_handle_upload(self, mock_handle_upload, mock_get_data):
        mock_get_data.return_value = {}
        generic_file_upload(self.mock_request)
        self.assertTrue(mock_handle_upload.called)

    def test_handles_exception_by_handle_upload(self):
        res = generic_file_upload(self.request)
        self.assertEqual(res.status_code, 400)
        content = json.loads(res.content.decode('utf-8'))
        self.assertFalse(content.get('success'))

    @patch.object(File, 'get_data')
    @patch.object(File, 'handle_upload')
    def test_calls_get_data(self, mock_handle_upload, mock_get_data):
        mock_get_data.return_value = {}
        generic_file_upload(self.mock_request)
        mock_get_data.assert_called_once_with(
            file_object=mock_handle_upload.return_value)


class GenericFileServeTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.file = File.create_new('image/jpeg')
        self.url = reverse(
            file_display_route, args=('display', self.file.uuid))
        self.request = self.factory.get(self.url)

    def test_raises_404_if_invalid_action(self):
        url = reverse(file_display_route, args=('foo', 'uid'))
        res = self.client.get(url)
        self.assertEqual(res.status_code, 404)

    def test_raises_404_if_file_not_found(self):
        url = reverse(file_display_route, args=('display', 'uid'))
        res = self.client.get(url)
        self.assertEqual(res.status_code, 404)

    @patch.object(File, 'get_data')
    def test_calls_get_data(self, mock_get_data):
        self.client.get(self.url)
        mock_get_data.assert_called_once_with(file_object=self.file)

    @patch('apps.questionnaire.views.retrieve_file')
    def test_calls_retrieve_file(self, mock_retrieve_file):
        self.client.get(self.url)
        mock_retrieve_file.assert_called_once_with(self.file, thumbnail=None)

    @patch('apps.questionnaire.views.retrieve_file')
    def test_calls_retrieve_file_with_thumbnail(self, mock_retrieve_file):
        self.client.get(self.url + '?format=foo')
        mock_retrieve_file.assert_called_once_with(self.file, thumbnail='foo')

    @patch('apps.questionnaire.views.retrieve_file')
    def test_returns_file(self, mock_retrieve_file):
        mock_retrieve_file.return_value = ('file', 'filename')
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)

    @patch('apps.questionnaire.views.retrieve_file')
    def test_returns_file_download(self, mock_retrieve_file):
        url = reverse(file_display_route, args=('download', self.file.uuid))
        mock_retrieve_file.return_value = ('file', 'filename')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)


class QuestionnaireLinkSearchViewTest(TestCase):

    fixtures = [
        'global_key_values',
        'technologies',
        'approaches',
    ]

    def setUp(self):
        view = QuestionnaireLinkSearchView(configuration_code='approaches')
        self.request = RequestFactory().get(
            reverse('approaches:questionnaire_link_search'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        user1 = create_new_user()
        user2 = create_new_user(id=2, email='foo@bar.com')
        self.request.user = user1
        self.view = self.setup_view(view, self.request)
        self.q1 = Questionnaire.create_new(
            configuration_code='technologies',
            data={'qg_name': [{'name': {'en': 'Tech 1'}}]}, user=user1)
        self.q2 = Questionnaire.create_new(
            configuration_code='approaches',
            data={'qg_name': [{'name': {'en': 'App 2'}}]}, user=user1)
        self.q3 = Questionnaire.create_new(
            configuration_code='approaches',
            data={'qg_name': [{'name': {'en': 'App 3'}}]}, user=user1)
        self.q3.status = 4
        self.q3.save()
        self.q4 = Questionnaire.create_new(
            configuration_code='approaches',
            data={'qg_name': [{'name': {'en': 'App 4'}}]}, user=user2)
        self.q4.status = 4
        self.q4.save()
        self.q5 = Questionnaire.create_new(
            configuration_code='approaches',
            data={'qg_name': [{'name': {'en': 'App 5'}}]}, user=user2)

    def test_returns_all(self):
        response = self.view.get(self.request)
        json_response = json.loads(response.content)
        self.assertEqual(len(json_response), 3)
        for q in json_response:
            self.assertIn(q['name'], ['App 2', 'App 3', 'App 4'])

    def test_returns_search(self):
        self.request.GET = {'term': 'app 3'}
        response = self.view.get(self.request)
        json_response = json.loads(response.content)
        self.assertEqual(len(json_response), 1)
        self.assertEqual(json_response[0]['name'], 'App 3')

    def test_returns_empty(self):
        self.request.GET = {'term': 'nonexisting'}
        response = self.view.get(self.request)
        json_response = json.loads(response.content)
        self.assertEqual(len(json_response), 0)


class QuestionnaireViewTest(TestCase):
    fixtures = [
        'sample_global_key_values',
        'sample',
        'sample_questionnaires',
    ]

    def setUp(self):
        view = QuestionnaireView(url_namespace='sample')
        self.request = RequestFactory().get('/en/sample/view/app_1')
        self.request.user = create_new_user()
        self.request.session = dict()
        self.request._messages = MagicMock()
        self.view = self.setup_view(view, self.request, identifier='sample_1')
        get_cached_configuration.cache_clear()

    def test_get_obj_raises_404(self):
        view = self.setup_view(self.view, self.request, identifier='404')
        with self.assertRaises(Http404):
            view.get_object()

    def test_get_obj(self):
        self.view.get(self.request)
        self.assertEqual(self.view.object.code, 'sample_1')

    @patch('apps.questionnaire.views.query_questionnaire')
    def test_get_new_object(self, mock_query_questionnaire):
        view = self.setup_view(self.view, self.request, identifier='new')
        with self.assertRaises(Http404):
            view.get_object()
        self.assertFalse(mock_query_questionnaire.called)

    def test_has_object(self):
        self.assertTrue(self.view.has_object)

    def test_has_no_object(self):
        view = self.setup_view(self.view, self.request, identifier='new')
        self.assertFalse(view.has_object)

    def test_new_questionnaire_has_no_release(self):
        view = self.setup_view(self.view, self.request, identifier='new')
        self.assertFalse(view.has_release())

    def test_existing_questionnaire_has_release(self):
        self.view.get(self.request)
        self.assertTrue(self.view.has_release())

    def test_unauthenticated_no_review_panel(self):
        request = RequestFactory().get('/en/questionnaire/view/app_1')
        request.user = Mock()
        request.user.is_authenticated = False
        view = self.setup_view(self.view, request, identifier='sample_1')
        response = view.get(request)
        self.assertEquals(
            response.context_data['review_config'], {}
        )

    @patch.object(QuestionnaireView, 'get_review_config')
    def test_authenticated_review_panel(self, mock_get_review_config):
        self.view.get(self.request)
        self.assertTrue(mock_get_review_config.called)

    @patch.object(Questionnaire, 'can_edit')
    def test_is_blocked(self, mock_can_edit):
        mock_can_edit.return_value = False
        response = self.view.get(self.request)
        self.assertTrue(response.context_data['review_config']['is_blocked'])

    def test_get_template(self):
        self.assertEqual(self.view.get_template_names(), 'questionnaire/details.html')

    def test_configuration_code(self):
        self.view.get(self.request)
        self.assertIsInstance(self.view.questionnaire_configuration, QuestionnaireConfiguration)
        self.assertEqual(self.view.questionnaire_configuration.keyword, 'sample')

    def test_get_detail_url(self):
        self.view.get(self.request)
        self.assertEqual(
            self.view.get_detail_url(''), '/en/questionnaire/view/sample_1/#top'
        )

    def test_get_steps(self):
        self.assertListEqual(self.view.get_steps(), ['cat_0', 'cat_1', 'cat_2', 'cat_3', 'cat_4', 'cat_5'])

    @patch('apps.questionnaire.views.handle_review_actions')
    def test_post(self, mock_review):
        self.view.post(self.request)
        mock_review.assert_called_once_with(
            self.request, Questionnaire.objects.get(code='sample_1'), 'sample'
        )


class QuestionnaireEditViewTest(TestCase):
    fixtures = [
        'sample_global_key_values',
        'sample',
        'sample_questionnaires',
    ]

    def setUp(self):
        view = QuestionnaireEditView(url_namespace='sample')
        self.request = RequestFactory().get('/en/sample/edit/app_1')
        self.request.user = create_new_user()
        self.request.session = dict()
        self.request._messages = MagicMock()
        self.view = self.setup_view(view, self.request, identifier='sample_1')

    def test_require_user(self):
        self.request.user = AnonymousUser()
        self.assertEqual(
            self.view.dispatch(self.request).url,
            '/en/accounts/login/?next=/en/sample/edit/app_1'
        )

    def test_get_object_new(self):
        view = self.setup_view(self.view, self.request, identifier='new')
        self.assertEquals(view.get_object(), {})

    def test_create_new_version(self):
        self.request.POST = {'create_new_version': True}
        view = self.setup_view(self.view, self.request, identifier='sample_1')
        with patch.object(QuestionnaireConfiguration, 'has_new_edition'):
            with patch.object(view, 'update_case_data_for_editions') as mock_update:
                try:
                    view.post(request=self.request)
                except Exception:  # catch all, as we only want to check if the method is called.
                    pass
                mock_update.assert_called_once()

    def test_update_case_data_for_editions(self):
        view = self.setup_view(self.view, self.request, identifier='sample_1')
        view.questionnaire_configuration = MagicMock()
        view.object = MagicMock()
        with patch('apps.questionnaire.views.get_configuration') as mock_config:
            # test just one iteration.
            mock_config.return_value = MagicMock(has_new_edition=False)
            view.update_case_data_for_editions(**{})
            # This seems more readable than mocking all the objects.
            self.assertTrue(
                view.object.configuration.get_next_edition.return_value.
                    get_edition.return_value.
                    update_questionnaire_data.called
            )


class QuestionnaireStepViewTest(TestCase):
    fixtures = [
        'sample_global_key_values',
        'sample',
        'sample_questionnaires',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        view = QuestionnaireStepView(url_namespace='sample')
        self.request = self.factory.get('/en/questionnaire/view/app_1/cat_0/')
        self.request.user = create_new_user()
        self.request._messages = MagicMock()
        self.view = self.setup_view(view, self.request, identifier='sample_1', step='cat_0')
        self.view.form_has_errors = False

    def test_valid_step(self):
        self.view.get(self.request)
        self.assertEqual(self.view.category.keyword, 'cat_0')

    def test_invalid_step(self):
        view = self.setup_view(self.view, self.request, identifier='sample_1', step='cat_666')
        with self.assertRaises(Http404):
            view.get(self.request)

    @patch.object(Questionnaire, 'lock_questionnaire')
    def test_lock_questionnaire(self, lock_questionnaire):
        self.view.get(self.request)
        lock_questionnaire.assert_called_with('sample_1', self.request.user)

    @patch.object(Questionnaire, 'create_new')
    @patch.object(Questionnaire, 'unlock_questionnaire')
    def test_unlock_questionnaire(self, unlock_questionnaire, create_new):
        obj = self.view.get_object()
        self.view.object = obj
        create_new.return_value = obj
        self.view.form_valid({})
        unlock_questionnaire.assert_called_once_with()

    @patch.object(Questionnaire, 'create_new')
    @patch.object(QuestionnaireStepView, 'get_success_url_next_section')
    @patch('apps.questionnaire.signals.change_questionnaire_data.send')
    def test_next_section_route(self, mock_change_data,
                                get_success_url_next_section, create_new):
        request = self.factory.post(
            '/en/questionnaire/view/app_1/cat_0/', identifier='sample_1', step='cat_0',
            data={'goto-next-section': 'true'})
        request.user = self.request.user
        request._messages = MagicMock()
        view = self.setup_view(self.view, request, step='cat_0')
        view.object = MagicMock()
        view.object.code = 'foo'
        create_new.return_value = view.object
        view.form_valid({})
        get_success_url_next_section.assert_called_with('foo', 'cat_0')

    @patch.object(QuestionnaireStepView, 'get_steps')
    def test_next_section_url(self, get_steps):
        get_steps.return_value = ['foo', 'bar']
        response = self.view.get_success_url_next_section('sample_1', 'foo')
        self.assertEqual(response.url, '/en/questionnaire/edit/sample_1/bar/')

    @patch.object(QuestionnaireStepView, 'get_steps')
    def test_next_section_url_no_exception(self, get_steps):
        get_steps.return_value = ['foo', 'bar', 'baz']
        response = self.view.get_success_url_next_section('sample_1', 'abc')
        self.assertIsNone(response)

    @patch.object(Questionnaire, 'create_new')
    @patch('apps.questionnaire.signals.change_questionnaire_data.send')
    def test_success_url(self, mock_change_data, create_new):
        request = self.factory.post(
            '/en/questionnaire/view/app_1/cat_0/', identifier='sample_1', step='cat_0'
        )
        request.user = self.request.user
        request._messages = MagicMock()

        view = self.setup_view(self.view, request, step='cat_0')
        view.object = MagicMock()
        view.object.code = 'bar'
        create_new.return_value = view.object
        response = view.form_valid({})
        self.assertEqual(response.url, "/en/questionnaire/edit/bar/#cat_0")

    def test_get_locale_info(self):
        self.view.set_attributes()
        original_locale, show_translation = self.view.get_locale_info()
        self.assertIsNotNone(original_locale)
        self.assertFalse(show_translation)
