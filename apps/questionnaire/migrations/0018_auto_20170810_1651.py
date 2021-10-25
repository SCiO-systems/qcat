# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0017_auto_20170313_1724'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionnairetranslation',
            name='language',
            field=models.CharField(max_length=63, choices=[('en', 'English'), ('fr', 'French'), ('es', 'Spanish'), ('ru', 'Russian'), ('km', 'Khmer'), ('lo', 'Lao'), ('ar', 'Arabic'), ('pt', 'Portuguese'), ('af', 'Afrikaans')]),
        ),
        migrations.AlterUniqueTogether(
            name='questionnaire',
            unique_together=set([('code', 'version')]),
        ),
    ]
