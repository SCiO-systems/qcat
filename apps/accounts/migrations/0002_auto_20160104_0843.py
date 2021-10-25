# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(related_name='user_set', blank=True, verbose_name='groups', to='auth.Group', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_query_name='user'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_login',
            field=models.DateTimeField(verbose_name='last login', blank=True, null=True),
        ),
    ]
