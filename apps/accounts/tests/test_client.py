from unittest.mock import patch, MagicMock, PropertyMock

from apps.qcat.tests import TestCase
from .test_models import create_new_user
from ..client import WocatWebsiteUserClient


class TestClient(TestCase):
    def setUp(self):
        self.remote_user_client = WocatWebsiteUserClient()
        self.user = create_new_user()

    def api_login_response(self, status_code, login_status='foo'):
        api_response = MagicMock()
        api_response.configure_mock(status_code=status_code)
        api_response.json = lambda: {'status': login_status}
        return api_response

    @patch('apps.accounts.client.remote_user_client.get_user_information')
    def test_get_and_update_django_user(self, mock_user_information):
        user_mock = dict(
            pk=self.user.id,
            last_name='last_test',
            first_name='first_test',
            username=self.user.email,
            email=self.user.email,
            usergroup=[],
        )
        with patch.object(WocatWebsiteUserClient, 'get_user_information') as user_info:
            user_info.return_value = user_mock
            user = self.remote_user_client.get_and_update_django_user(**user_mock)
            self.assertEqual(user.lastname, 'last_test')
            self.assertEqual(user.firstname, 'first_test')
            self.assertEqual(user.email, self.user.email)
            self.assertEqual(user, self.user)

    @patch('requests.get')
    def test_get_user_info(self, mock_request_get):
        api_request = MagicMock()
        api_request.status_code = 200
        api_request.ok = PropertyMock(return_value=True)
        api_request.json = lambda: dict(success=True)
        mock_request_get.return_value = api_request
        self.assertIsInstance(
            self.remote_user_client.get_user_information('123'), dict
        )

    @patch('requests.post')
    @patch.object(WocatWebsiteUserClient, '_get')
    def test_search_users(self, mock_get, mock_request_post):
        request_post = MagicMock()
        request_post.status_code = 200
        request_post.ok = PropertyMock(return_value=True)
        request_post.json = lambda: dict(success=True)
        mock_request_post.return_value = request_post
        self.assertIsInstance(
            self.remote_user_client.search_users('foo'), dict
        )

    def test_update_user(self):
        # This is tested within test_models.
        pass
