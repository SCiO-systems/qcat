from django.conf import settings  # noqa
from appconf import AppConf


class AccountConf(AppConf):
    """
    Custom settings for the account module. Mainly settings required for
    the login on the remote system.
    """
    PID = 3
    LOGIN_TYPE = 'login'
    LOGIN_SUCCESS_URL = 'home'

    # The name of the UNCCD role as provided by the remote system.
    UNCCD_ROLE_NAME = 'UNCCD Focal Point'
