# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(verbose_name='last login', default=django.utils.timezone.now)),
                ('is_superuser', models.BooleanField(help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status', default=False)),
                ('email', models.EmailField(verbose_name='email address', max_length=255, unique=True)),
                ('firstname', models.CharField(blank=True, max_length=255, null=True)),
                ('lastname', models.CharField(blank=True, max_length=255, null=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(to='auth.Group', related_query_name='user', help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', blank=True, verbose_name='groups', related_name='user_set')),
                ('user_permissions', models.ManyToManyField(to='auth.Permission', related_query_name='user', help_text='Specific permissions for this user.', blank=True, verbose_name='user permissions', related_name='user_set')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
