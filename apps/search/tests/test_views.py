from apps.configuration.cache import get_configuration
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.test.client import RequestFactory
from unittest.mock import patch

from apps.accounts.tests.test_models import create_new_user
from apps.configuration.configuration import QuestionnaireConfiguration
from apps.qcat.tests import TestCase
from apps.search.views import (
    admin,
    delete_all,
    index,
    update,
)

route_search_delete_all = 'search:delete_all'
route_search_admin = 'search:admin'
route_search_index = 'search:index'
route_search_search = 'search:search'
route_search_update = 'search:update'


class AdminTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(route_search_admin)

    def test_login_required(self):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'login.html')

    def test_requires_superuser_permissions(self):
        request = self.factory.get(self.url)
        request.user = create_new_user()
        request.session = {}
        with self.assertRaises(PermissionDenied):
            admin(request)

    def test_renders_correct_template(self):
        request = self.factory.get(self.url)
        request.user = create_new_user()
        request.user.is_superuser = True
        request.session = {}
        res = admin(request)
        self.assertEqual(res.status_code, 200)


@patch('apps.search.views.messages')
class IndexTest(TestCase):

    fixtures = [
        'sample_global_key_values',
        'sample',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(
            route_search_index,
            kwargs={'configuration': 'sample', 'edition': '2015'})
        user = create_new_user()
        user.is_superuser = True
        self.request = self.factory.get(self.url)
        self.request.user = user
        self.request.session = {}

    def test_login_required(self, mock_messages):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'login.html')

    def test_requires_superuser_permissions(self, mock_messages):
        request = self.factory.get(self.url)
        request.user = create_new_user(id=99, email='foo@bar.com')
        request.session = {}
        with self.assertRaises(PermissionDenied):
            index(request, 'foo', 'bar')

    @patch('apps.search.views.get_configuration')
    def test_calls_QuestionnaireConfiguration(self, mock_conf, mock_messages):
        mock_conf.configuration_error = None
        index(self.request, 'sample', '2015')
        mock_conf.assert_called_once_with(code='sample', edition='2015')

    @patch('apps.search.views.get_configuration')
    def test_returns_bad_request_if_errors_in_configuration(
            self, mock_conf, mock_messages):
        mock_conf.configuration_error = 'error'
        res = index(self.request, 'sample', '2015')
        self.assertEqual(res.status_code, 400)

    @patch('apps.search.views.get_mappings')
    @patch('apps.search.views.create_or_update_index')
    @patch.object(QuestionnaireConfiguration, 'get_configuration_errors')
    def test_calls_get_mappings(self,  mock_get_conf_errors, mock_create_index,
            mock_get_mappings, mock_messages):
        mock_get_conf_errors.return_value = None
        mock_create_index.return_value = None, None, 'error_msg'
        index(self.request, 'sample', '2015')
        mock_get_mappings.assert_called_once_with()

    @patch('apps.search.views.get_configuration')
    @patch('apps.search.views.get_mappings')
    @patch('apps.search.views.create_or_update_index')
    def test_calls_create_or_update_index(
            self, mock_create_index, mock_get_mappings, mock_get_configuration,
            mock_messages):
        mock_get_configuration.return_value.get_configuration_errors.return_value = None
        mock_create_index.return_value = None, None, ''
        index(self.request, 'sample', '2015')

        mock_create_index.assert_called_once_with(
            configuration=mock_get_configuration.return_value,
            mappings=mock_get_mappings.return_value)

    @patch('apps.search.views.get_mappings')
    @patch('apps.search.views.create_or_update_index')
    @patch.object(QuestionnaireConfiguration, '__init__')
    @patch.object(QuestionnaireConfiguration, 'get_configuration_errors')
    def test_adds_message_and_redirects_if_not_successful(
            self, mock_get_conf_errors, mock_Conf, mock_create_index,
            mock_get_mappings, mock_messages):
        mock_Conf.return_value = None
        mock_get_conf_errors.return_value = None
        mock_create_index.return_value = None, None, 'error_msg'
        res = index(self.request, 'sample', '2015')
        mock_messages.error.assert_called_once_with(
            self.request, 'The following error(s) occured: error_msg')
        self.assertEqual(res.status_code, 302)

    @patch('apps.search.views.get_mappings')
    @patch('apps.search.views.create_or_update_index')
    @patch.object(QuestionnaireConfiguration, '__init__')
    @patch.object(QuestionnaireConfiguration, 'get_configuration_errors')
    def test_adds_message_and_redirects_if_successful(
            self, mock_get_conf_errors, mock_Conf, mock_create_index,
            mock_get_mappings, mock_messages):
        mock_Conf.return_value = None
        mock_get_conf_errors.return_value = None
        mock_create_index.return_value = True, None, ''
        res = index(self.request, 'sample', '2015')
        mock_messages.success.assert_called_once_with(
            self.request, 'Index "sample" was created or updated.')
        self.assertEqual(res.status_code, 302)


@patch('apps.search.views.messages')
class UpdateTest(TestCase):

    fixtures = [
        'sample_global_key_values',
        'sample',
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(
            route_search_update,
            kwargs={'configuration': 'sample', 'edition': '2015'})
        user = create_new_user()
        user.is_superuser = True
        self.request = self.factory.get(self.url)
        self.request.user = user
        self.request.session = {}

    def test_login_required(self, mock_messages):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'login.html')

    def test_requires_superuser_permissions(self, mock_messages):
        request = self.factory.get(self.url)
        request.user = create_new_user(id=99, email='foo@bar.com')
        request.session = {}
        with self.assertRaises(PermissionDenied):
            update(request, 'sample', '2015')

    @patch('apps.search.views.put_questionnaire_data')
    @patch.object(QuestionnaireConfiguration, '__init__')
    @patch.object(QuestionnaireConfiguration, 'get_configuration_errors')
    def test_calls_put_questionnaire_data(
            self, mock_get_conf_errors, mock_Conf, mock_put_questionnaire_data,
            mock_messages):
        mock_Conf.return_value = None
        mock_get_conf_errors.return_value = None
        mock_put_questionnaire_data.return_value = None, []
        update(self.request, 'sample', '2015')
        self.assertEqual(mock_put_questionnaire_data.call_count, 1)

    @patch('apps.search.views.put_questionnaire_data')
    @patch.object(QuestionnaireConfiguration, '__init__')
    @patch.object(QuestionnaireConfiguration, 'get_configuration_errors')
    def test_adds_message_and_redirects_if_not_successful(
            self, mock_get_conf_errors, mock_Conf, mock_put_questionnaire_data,
            mock_messages):
        mock_Conf.return_value = None
        mock_get_conf_errors.return_value = None
        mock_put_questionnaire_data.return_value = None, ['error_msg']
        res = update(self.request, 'sample', '2015')
        mock_messages.error.assert_called_once_with(
            self.request, 'The following error(s) occured: error_msg')
        self.assertEqual(res.status_code, 302)

    @patch('apps.search.views.put_questionnaire_data')
    @patch.object(QuestionnaireConfiguration, '__init__')
    @patch.object(QuestionnaireConfiguration, 'get_configuration_errors')
    def test_adds_message_and_redirects_if_successful(
            self, mock_get_conf_errors, mock_Conf, mock_put_questionnaire_data,
            mock_messages):
        mock_Conf.return_value = None
        mock_get_conf_errors.return_value = None
        mock_put_questionnaire_data.return_value = 0, []
        res = update(self.request, 'sample', '2015')
        mock_messages.success.assert_called_once_with(
            self.request,
            '0 Questionnaires of configuration "sample" successfully indexed.')
        self.assertEqual(res.status_code, 302)


@patch('apps.search.views.messages')
class DeleteTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse(route_search_delete_all)
        user = create_new_user()
        user.is_superuser = True
        self.request = self.factory.get(self.url)
        self.request.user = user
        self.request.session = {}

    def test_login_required(self, mock_messages):
        res = self.client.get(self.url, follow=True)
        self.assertTemplateUsed(res, 'login.html')

    def test_requires_superuser_permissions(self, mock_messages):
        request = self.factory.get(self.url)
        request.user = create_new_user(id=99, email='foo@bar.com')
        request.session = {}
        with self.assertRaises(PermissionDenied):
            delete_all(request)

    @patch('apps.search.views.delete_all_indices')
    def test_calls_delete_all_indices(
            self, mock_delete_all_indices, mock_messages):
        mock_delete_all_indices.return_value = True, ''
        delete_all(self.request)
        mock_delete_all_indices.assert_called_once_with()

    @patch('apps.search.views.delete_all_indices')
    def test_adds_message_and_redirects_if_not_successful(
            self, mock_delete_all_indices, mock_messages):
        mock_delete_all_indices.return_value = False, 'foo'
        res = delete_all(self.request)
        mock_messages.error.assert_called_once_with(
            self.request, 'The following error(s) occured: foo')
        self.assertEqual(res.status_code, 302)

    @patch('apps.search.views.delete_all_indices')
    def test_adds_message_and_redirects_if_successful(
            self, mock_delete_all_indices, mock_messages):
        mock_delete_all_indices.return_value = True, ''
        res = delete_all(self.request)
        mock_messages.success.assert_called_once_with(
            self.request, 'All indices successfully deleted.')
        self.assertEqual(res.status_code, 302)
