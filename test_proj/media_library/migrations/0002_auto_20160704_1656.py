# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media_library', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='duration',
            field=models.FloatField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='height',
            field=models.PositiveIntegerField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='width',
            field=models.PositiveIntegerField(editable=False, null=True),
        ),
    ]
