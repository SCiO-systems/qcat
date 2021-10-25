# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import models, migrations
if django.VERSION[:2] >= (1, 11):
    from django.contrib.postgres.fields import JSONField
    DjangoJsonField = JSONField
else:
    import django_pgjson.fields
    DjangoJsonField = django_pgjson.fields.JsonBField


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='data_old',
            field=DjangoJsonField(null=True),
            preserve_default=True,
        ),
    ]
