from rest_framework.authentication import TokenAuthentication

from .models import NoteToken
from .models import AppToken

from datetime import timedelta
from datetime import datetime
import datetime as dtime
import pytz
from rest_framework import exceptions


class NoteTokenAuthentication(TokenAuthentication):
    """Use our custom model for the token auth for GET requests"""
    model = NoteToken


class AppTokenAuthentication(TokenAuthentication):
    """
    Use a custom model to authenticate POST requests
     - Expire and remove the token if not used in 24 hours
    """

    def authenticate_credentials(self, key):
        model = AppToken
        print(1)
        try:
            token = model.objects.select_related('user').get(key=key)
            print(2)
        except model.DoesNotExist:
            print(3)
            raise exceptions.AuthenticationFailed('Invalid token')

        print(4)
        if not token.user.is_active:
            print(5)
            raise exceptions.AuthenticationFailed('User inactive or deleted')

        print(6)
        # This is required for the time comparison
        utc_now = datetime.now(dtime.timezone.utc)
        utc_now = utc_now.replace(tzinfo=pytz.utc)

        # Check if the token has been used in the last 24 hours
        # - if not, delete the token and ask user to login to fetch a new token
        # - otherwise, update the updated time to now
        print(7)
        if token.updated < utc_now - timedelta(hours=24):
            print(8)
            token.delete()
            raise exceptions.AuthenticationFailed('APP Token expired, request a new APP Token')
        else:
            print(9)
            token.updated = utc_now
            token.save()

        print(10)
        return token.user, token
