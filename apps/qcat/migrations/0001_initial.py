# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MemoryLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('created', models.DateTimeField()),
                ('source', models.CharField(max_length=255)),
                ('params', models.CharField(max_length=255)),
                ('memory', models.BigIntegerField()),
                ('increment', models.BigIntegerField()),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
    ]
