# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0003_auto_20151222_1158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionnaire',
            name='links',
            field=models.ManyToManyField(to='questionnaire.Questionnaire', related_name='_questionnaire_links_+', through='questionnaire.QuestionnaireLink'),
        ),
    ]
