# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0011_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionnairemembership',
            name='role',
            field=models.CharField(choices=[('compiler', 'Compiler'), ('editor', 'Editor'), ('reviewer', 'Reviewer'), ('publisher', 'Publisher'), ('secretariat', 'WOCAT Secretariat'), ('UNCCD Focal Point', 'UNCCD Focal Point'), ('landuser', 'Land User'), ('resourceperson', 'Key resource person')], max_length=64),
        ),
    ]
