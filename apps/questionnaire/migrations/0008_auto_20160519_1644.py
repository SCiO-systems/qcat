# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0007_auto_20160317_1551'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='questionnaire',
            options={'permissions': (('review_questionnaire', 'Can review questionnaire'), ('publish_questionnaire', 'Can publish questionnaire'), ('assign_questionnaire', 'Can assign questionnaire (for review/publish)')), 'ordering': ['-updated']},
        ),
    ]
