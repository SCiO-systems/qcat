# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0008_auto_20160519_1644'),
    ]

    operations = [
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('flag', models.CharField(choices=[('unccd_bp', 'UNCCD Best Practice')], max_length=64)),
            ],
        ),
        migrations.AlterModelOptions(
            name='questionnaire',
            options={'ordering': ['-updated'], 'permissions': (('review_questionnaire', 'Can review questionnaire'), ('publish_questionnaire', 'Can publish questionnaire'), ('assign_questionnaire', 'Can assign questionnaire (for review/publish)'), ('flag_unccd_questionnaire', 'Can flag UNCCD questionnaire'), ('unflag_unccd_questionnaire', 'Can unflag UNCCD questionnaire'))},
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='flags',
            field=models.ManyToManyField(to='questionnaire.Flag'),
        ),
    ]
