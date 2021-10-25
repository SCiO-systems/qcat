# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0004_institution_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='institution',
            name='abbreviation',
            field=models.CharField(max_length=63, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='abbreviation',
            field=models.CharField(max_length=63, null=True, blank=True),
        ),
    ]
