import logging

from django.core.management.base import BaseCommand
from django.db import OperationalError
from django.utils.timezone import now

from apps.notifications.models import Log

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Send notification mails.
    """
    def __init__(self):
        super().__init__()
        self.is_blocked = False

    def handle(self, **options):
        logs = Log.objects.filter(was_processed=False)
        for log in self.logged_generator(logs):
            try:
                log.send_mails()
            except OperationalError:
                self.is_blocked = True
                logger.info(
                    '{date}: could not process logs: database blocked by other '
                    'process.'.format(
                        date=now()
                    )
                )

    def logged_generator(self, logs):
        """
        Log start of loop, each step, and end.
        """
        start = now()
        logger.info('{date}: start processing {count} logs'.format(
            date=start, count=logs.count()
        ))
        for log in logs:
            yield log
            if not self.is_blocked:
                logger.info(
                    '{date}: sent log {id} ({action}) for questionnaire '
                    '{questionnaire_code} to {recipients} recipients'.format(
                        date=now(),
                        id=log.pk,
                        questionnaire_code=log.questionnaire.code,
                        action=log.get_action_display(),
                        recipients=len(
                            [
                                r for r in log.recipients
                                if r.mailpreferences.do_send_mail(log)
                            ]
                        )
                    )
                )
        end = now()
        delta = end - start
        action = 'finished' if self.is_blocked is False else 'canceled'
        logger.info(
            '{date}: {action} processing logs, it took {delta} seconds'.format(
                action=action,
                date=end,
                delta=delta.seconds
            )
        )
