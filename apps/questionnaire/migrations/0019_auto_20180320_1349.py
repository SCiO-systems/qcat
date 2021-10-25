# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def restore_configuration(apps, schema_editor):
    Questionnaire = apps.get_model("questionnaire", "Questionnaire")
    Configuration = apps.get_model("configuration", "Configuration")
    available_configurations = dict(Configuration.objects.values_list('code', 'id'))
    for questionnaire in Questionnaire.objects.all():
        configuration_code = questionnaire.code.split('_')[0]
        questionnaire.configuration_id = available_configurations[configuration_code]
        questionnaire.save()


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0008_auto_20180320_1349'),
        ('questionnaire', '0018_auto_20170810_1651'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionnaire',
            name='configurations',
        ),
        migrations.AddField(
            model_name='questionnaire',
            name='configuration',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='configuration.Configuration'),
            preserve_default=False,
        ),
        migrations.RunPython(restore_configuration),
    ]


