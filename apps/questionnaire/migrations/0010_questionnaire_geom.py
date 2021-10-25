# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0009_auto_20160601_1037'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='geom',
            field=django.contrib.gis.db.models.fields.GeometryField(srid=4326, blank=True, null=True),
        ),
    ]
