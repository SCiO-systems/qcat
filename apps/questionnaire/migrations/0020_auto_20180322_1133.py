# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0019_auto_20180320_1349'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionnaireconfiguration',
            name='configuration',
        ),
        migrations.RemoveField(
            model_name='questionnaireconfiguration',
            name='questionnaire',
        ),
        migrations.DeleteModel(
            name='QuestionnaireConfiguration',
        ),
    ]
