from django.contrib.auth.backends import ModelBackend
from .client import remote_user_client


class WocatCMSAuthenticationBackend(ModelBackend):
    """
    Authentication against new (2017) wocat website.
    """

    def authenticate(self, username=None, password=None, **kwargs):
        """
        Custom authentication. Returns a user if authentication
        successful.
        """
        user_data = remote_user_client.remote_login(username, password)
        if not user_data:
            return None

        return remote_user_client.get_and_update_django_user(**user_data)
