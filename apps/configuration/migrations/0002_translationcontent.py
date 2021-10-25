# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    - Create new table for migration content
    - Install rule which prevents updates on the translations. This is required
      so that changes in the translations always result in a new row, after
      which a new string is created for the translators.

    """

    dependencies = [
        ('configuration', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TranslationContent',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('keyword', models.CharField(max_length=50)),
                ('configuration', models.CharField(default='wocat', max_length=50)),
                ('text', models.TextField()),
                ('translation', models.ForeignKey(to='configuration.Translation', on_delete=models.deletion.PROTECT)),
            ],
        ),
        # migrations.RunSQL(
        #     'CREATE RULE translation_data_protect_update AS ON UPDATE TO configuration_translation DO INSTEAD NOTHING;'
        # )
    ]

