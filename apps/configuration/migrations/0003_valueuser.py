# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('configuration', '0002_translationcontent'),
    ]

    operations = [
        migrations.CreateModel(
            name='ValueUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('relation', models.CharField(choices=[('unccd_fp', 'UNCCD Focal Point')], max_length=64)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
                ('value', models.ForeignKey(to='configuration.Value', on_delete=models.deletion.CASCADE)),
            ],
        ),
    ]
