# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0003_valueuser'),
    ]

    operations = [
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.IntegerField(help_text='The ID must be exactly the same as on the WOCAT website!', primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('abbreviation', models.CharField(max_length=63)),
                ('active', models.BooleanField(default=True)),
                ('country', models.ForeignKey(blank=True, to='configuration.Value', null=True, on_delete=models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.IntegerField(help_text='The ID must be exactly the same as on the WOCAT website!', primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('abbreviation', models.CharField(max_length=63)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
