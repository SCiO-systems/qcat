# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_auto_20170405_1501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailpreferences',
            name='language',
            field=models.CharField(max_length=2, default='en', choices=[('en', 'English'), ('fr', 'French'), ('es', 'Spanish'), ('ru', 'Russian'), ('km', 'Khmer'), ('lo', 'Lao'), ('ar', 'Arabic'), ('pt', 'Portuguese'), ('af', 'Afrikaans')]),
        ),
    ]
