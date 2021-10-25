# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-10-20 07:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0010_auto_20180511_1250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuration',
            name='code',
            field=models.CharField(choices=[('approaches', 'approaches'), ('cca', 'cca'), ('cbp', 'cbp'), ('technologies', 'technologies'), ('unccd', 'unccd'), ('watershed', 'watershed'), ('wocat', 'wocat')], max_length=20),
        ),
    ]
