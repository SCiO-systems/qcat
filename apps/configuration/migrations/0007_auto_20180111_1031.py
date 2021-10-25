# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0006_auto_20170810_1651'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False, help_text='The ID must be exactly the same as on the WOCAT website!'),
        ),
    ]
