# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import video_encoding.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('width', models.PositiveIntegerField(editable=False, default=0)),
                ('height', models.PositiveIntegerField(editable=False, default=0)),
                ('duration', models.FloatField(editable=False, default=0)),
                ('file', video_encoding.fields.VideoField(width_field='width', height_field='height', upload_to='')),
            ],
        ),
    ]
