# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0009_auto_20160601_1037'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
