# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0005_auto_20160804_0736'),
    ]

    operations = [
        migrations.AlterField(
            model_name='institution',
            name='abbreviation',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
    ]
