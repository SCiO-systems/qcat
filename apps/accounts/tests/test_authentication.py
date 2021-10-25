from apps.accounts.client import WocatWebsiteUserClient
from django.contrib.auth import get_user_model

from apps.qcat.tests import TestCase

User = get_user_model()


def get_mock_validate_session_values():
    """
    Returns mock values that correspond to the actual validate_session
    function in accounts.authentication.
    """
    return 1


def get_mock_user_information_values():
    """
    Returns mock values that correspond to the actual
    get_user_information function in accounts.authentication.
    """
    return {
        'uid': 1,
        'username': 'foo@bar.com',
        'first_name': 'Foo',
        'last_name': 'Bar',
    }


def get_mock_user_information_values_cms():
    return {
        'pk': 1,
        'email': 'foo@bar.com',
        'first_name': 'Foo',
        'last_name': 'Bar',
    }


class WOCATCMSAuthenticateTest(TestCase):

    def setUp(self):
        self.remote_user_client = WocatWebsiteUserClient()

    def test_existing_user_updates(self):
        # Existing users have their information updated
        user_info = get_mock_user_information_values_cms()
        User.objects.create(id=user_info['pk'], email=user_info['email'])

        user = self.remote_user_client.get_and_update_django_user(**user_info)

        self.assertEqual(user.id, user_info['pk'])
        self.assertEqual(user.email, user_info['email'])
        self.assertEqual(user.firstname, user_info['first_name'])
        self.assertEqual(user.lastname, user_info['last_name'])

    def test_new_user_updates(self):
        # New users should also have their information updated
        user_info = get_mock_user_information_values_cms()

        user = self.remote_user_client.get_and_update_django_user(**user_info)

        self.assertEqual(user.id, user_info['pk'])
        self.assertEqual(user.email, user_info['email'])
        self.assertEqual(user.firstname, user_info['first_name'])
        self.assertEqual(user.lastname, user_info['last_name'])
