# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0007_auto_20180111_1031'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='configuration',
            name='activated',
        ),
        migrations.RemoveField(
            model_name='configuration',
            name='active',
        ),
        migrations.RemoveField(
            model_name='configuration',
            name='base_code',
        ),
        migrations.AlterField(
            model_name='configuration',
            name='code',
            field=models.CharField(max_length=20, choices=[('approaches', 'approaches'), ('cca', 'cca'), ('technologies', 'technologies'), ('unccd', 'unccd'), ('watershed', 'watershed'), ('wocat', 'wocat')]),
        ),
        migrations.RemoveField(
            model_name='configuration',
            name='description',
        ),
        migrations.RemoveField(
            model_name='configuration',
            name='name',
        ),
        migrations.AddField(
            model_name='configuration',
            name='edition',
            field=models.CharField(max_length=10, default='2015'),
            preserve_default=False,
        ),
    ]
