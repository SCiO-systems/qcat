# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0008_auto_20180320_1349'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='configuration',
            unique_together=set([('code', 'edition')]),
        ),
    ]
