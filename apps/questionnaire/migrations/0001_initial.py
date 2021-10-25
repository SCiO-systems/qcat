# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import models, migrations
from django.conf import settings
import uuid

if django.VERSION[:2] >= (1, 11):
    from django.contrib.postgres.fields import JSONField
    DjangoJsonField = JSONField
else:
    import django_pgjson.fields
    DjangoJsonField = django_pgjson.fields.JsonBField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('configuration', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('uuid', models.CharField(max_length=64)),
                ('uploaded', models.DateTimeField(auto_now=True)),
                ('content_type', models.CharField(max_length=64)),
                ('size', models.BigIntegerField(null=True)),
                ('thumbnails', DjangoJsonField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Questionnaire',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('data', DjangoJsonField()),
                ('created', models.DateTimeField()),
                ('updated', models.DateTimeField()),
                ('uuid', models.CharField(max_length=64, default=uuid.uuid4)),
                ('code', models.CharField(max_length=64, default='')),
                ('blocked', models.BooleanField(default=False)),
                ('status', models.IntegerField(choices=[(1, 'Draft'), (2, 'Pending'), (3, 'Public'), (4, 'Rejected'), (5, 'Inactive')])),
                ('version', models.IntegerField()),
            ],
            options={
                'ordering': ['-updated'],
                'permissions': (('can_moderate', 'Can moderate'),),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionnaireConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('original_configuration', models.BooleanField(default=False)),
                ('configuration', models.ForeignKey(to='configuration.Configuration', on_delete=models.deletion.CASCADE)),
                ('questionnaire', models.ForeignKey(to='questionnaire.Questionnaire', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['-original_configuration'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionnaireLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('from_status', models.IntegerField(choices=[(1, 'Draft'), (2, 'Pending'), (3, 'Public'), (4, 'Rejected'), (5, 'Inactive')])),
                ('to_status', models.IntegerField(choices=[(1, 'Draft'), (2, 'Pending'), (3, 'Public'), (4, 'Rejected'), (5, 'Inactive')])),
                ('from_questionnaire', models.ForeignKey(to='questionnaire.Questionnaire', related_name='from_questionnaire', on_delete=models.deletion.CASCADE)),
                ('to_questionnaire', models.ForeignKey(to='questionnaire.Questionnaire', related_name='to_questionnaire', on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionnaireMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('author', 'Author'), ('editor', 'Editor')], max_length=64)),
                ('questionnaire', models.ForeignKey(to='questionnaire.Questionnaire', on_delete=models.deletion.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionnaireTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('language', models.CharField(choices=[('en', 'English'), ('es', 'Spanish'), ('fr', 'French')], max_length=63)),
                ('original_language', models.BooleanField(default=False)),
                ('questionnaire', models.ForeignKey(to='questionnaire.Questionnaire', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['-original_language'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='configurations',
            field=models.ManyToManyField(to='configuration.Configuration', through='questionnaire.QuestionnaireConfiguration'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='links',
            field=models.ManyToManyField(to='questionnaire.Questionnaire', null=True, through='questionnaire.QuestionnaireLink', related_name='linked_to+'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='members',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='questionnaire.QuestionnaireMembership'),
            preserve_default=True,
        ),
    ]
