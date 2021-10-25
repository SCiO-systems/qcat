# -*- coding: utf-8 -*-
import logging
import requests
from apps.accounts.models import User

from django.contrib.auth import get_user_model
from django.views.decorators.debug import sensitive_variables

from apps.qcat.decorators import log_memory_usage
from .conf import settings

logger = logging.getLogger(__name__)


class WocatWebsiteUserClient:
    """
    Client with endpoints of the relaunched wocat website.
    """

    @log_memory_usage
    def _get(self, url: str) -> requests.Response:
        """
        Simple helper to request api; all requests are GET.
        """
        return requests.get(**self._get_request_params(url=url))

    @log_memory_usage
    @sensitive_variables()
    def _post(self, url: str, **data) -> requests.Response:
        data.update(self._get_request_params(url=url))
        return requests.post(**data)

    def _get_request_params(self, url: str) -> dict:
        return {
            'url': f'{settings.AUTH_API_URL}{url}',
            'headers': {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Token {settings.AUTH_API_TOKEN}'
            }
        }

    def remote_login(self, username: str, password: str) -> dict:
        response = self._post(
            url='auth/login/',
            json={'username': username, 'password': password}
        )
        if response.ok:
            return response.json()
        return None

    def get_user_id(self, session_id):
        raise NotImplementedError('Deprecated method with new auth.')

    def api_login(self):
        raise NotImplementedError('Deprecated method with new auth.')

    def get_and_update_django_user(self, **user_info) -> User:
        user_id = user_info.pop('pk')
        user, __ = get_user_model().objects.get_or_create(id=user_id)
        self.update_user(user, user_info)
        return user

    def search_users(self, name='') -> dict:
        """
        Keep response format as in the previous API from typo3.
        """
        response = self._get(f'users/?name={name}')
        if not response.ok or not response.json():
            return {'success': True, 'message': '', 'users': [], 'count': 0}

        return {
            'success': True,
            'message': '',
            'users': [{
                'uid': user['pk'],
                'username': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
            } for user in response.json()],
            'count': len(response.json())
        }

    def get_logout_url(self, redirect):
        raise NotImplementedError('Deprecated method')

    def get_user_information(self, user_id: int) -> dict:
        """
        Get user info from remote system as dictionary.
        """
        response = self._get(f'users/{user_id}/')
        if response.ok:
            user_info = response.json()
            # backwards compatibility
            user_info['username'] = user_info.get('email')
            return user_info
        return None

    def update_user(self, user: User, user_information: dict):
        if user_information:
            user.update(
                email=user_information['email'],
                lastname=user_information['last_name'],
                firstname=user_information['first_name']
            )


remote_user_client = WocatWebsiteUserClient()
