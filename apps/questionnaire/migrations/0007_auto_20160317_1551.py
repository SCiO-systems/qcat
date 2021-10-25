# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0006_questionnaire_blocked'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionnaire',
            name='blocked',
            field=models.ForeignKey(
                null=True, blank=True, related_name='blocks_questionnaire',
                help_text='Set with the method: lock_questionnaire.', to=settings.AUTH_USER_MODEL,
                on_delete=models.deletion.CASCADE
            ),
        ),
    ]
