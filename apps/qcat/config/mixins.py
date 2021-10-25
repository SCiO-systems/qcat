from configurations import values
from os.path import join


class DevMixin:
    DEBUG = values.BooleanValue(True)
    CACHES = values.DictValue(
        environ_prefix='',
        default={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache',}}
    )
    EMAIL_BACKEND = 'eml_email_backend.EmailBackend'

    @property
    def EMAIL_FILE_PATH(self):
        return join(super().BASE_DIR, 'tmp')

    THUMBNAIL_DEBUG = True


class TestMixin:
    IS_TEST_RUN = True


class DebugToolbarMixin:
    """
    Not used by default, as it slows down request massively. Use this when
    debugging questionnaires.
    """
    @property
    def INSTALLED_APPS(self):
        return super().INSTALLED_APPS + (
            'debug_toolbar',
        )


class ProdMixin:
    DEBUG = values.BooleanValue(False)
    TEMPLATE_DEBUG = values.BooleanValue(False)

    # Image postprocessors for uploaded images; optimize images.
    THUMBNAIL_OPTIMIZE_COMMAND = {
        'png': '/usr/bin/optipng {filename}',
        'gif': '/usr/bin/optipng {filename}',
        'jpeg': '/usr/bin/jpegoptim {filename}'
    }

    # This is the default, stated here to be explicit.
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


class LogMixin:
    """
    Very basic logger - everything with 'warn' or above is written to a file.
    """
    @property
    def LOGGING(self):
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
                },
            },
            'handlers': {
                'file': {
                    'level': 'DEBUG',
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'when': 'midnight',
                    'backupCount': 5,
                    'filename': '{}/logs/django.log'.format(super().BASE_DIR),
                    'formatter': 'verbose'
                },
                'cache_info': {
                    'level': 'DEBUG',
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'when': 'midnight',
                    'backupCount': 14,
                    'filename': '{}/logs/caches.log'.format(super().BASE_DIR),
                    'formatter': 'verbose'
                }
            },
            'loggers': {
                '': {
                    'handlers': ['file'],
                    'propagate': True,
                    'level': 'WARNING',
                },
                'notifications': {
                    'handlers': ['file'],
                    'propagate': True,
                    'level': 'INFO'
                },
                'profile_log': {
                    'handlers': ['cache_info'],
                    'propagate': False,
                    'level': 'INFO'
                }
            },
        }


class SecurityMixin:
    # Security settings, as recommended from manage.py check --deploy
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    # Set the max-age to 12 months
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True


class CompressMixin:
    """Settings for the django-compressor"""
    COMPRESS_ENABLED = True
    # maybe: use different (faster) filters for css and js.


class MetricsMixin:
    """
    Error reporting on production environments.
    """

    @property
    def INSTALLED_APPS(self):
        return super().INSTALLED_APPS + ('raven.contrib.django.raven_compat', )

    @property
    def RAVEN_CONFIG(self):
        import raven

        return {
            'dsn': str(super().SENTRY_DSN),
            'release': raven.fetch_git_sha(super().BASE_DIR),
        }
