# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0002_questionnaire_data_old'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='questionnaire',
            options={'permissions': (('review_questionnaire', 'Can review questionnaire'), ('publish_questionnaire', 'Can publish questionnaire')), 'ordering': ['-updated']},
        ),
        migrations.AlterField(
            model_name='questionnaire',
            name='status',
            field=models.IntegerField(choices=[(1, 'Draft'), (2, 'Submitted'), (3, 'Reviewed'), (4, 'Public'), (5, 'Rejected'), (6, 'Inactive')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='questionnairelink',
            name='from_status',
            field=models.IntegerField(choices=[(1, 'Draft'), (2, 'Submitted'), (3, 'Reviewed'), (4, 'Public'), (5, 'Rejected'), (6, 'Inactive')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='questionnairelink',
            name='to_status',
            field=models.IntegerField(choices=[(1, 'Draft'), (2, 'Submitted'), (3, 'Reviewed'), (4, 'Public'), (5, 'Rejected'), (6, 'Inactive')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='questionnairemembership',
            name='role',
            field=models.CharField(choices=[('compiler', 'Compiler'), ('editor', 'Editor'), ('reviewer', 'Reviewer'), ('publisher', 'Publisher'), ('landuser', 'Land User')], max_length=64),
            preserve_default=True,
        ),
    ]
