from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from video_encoding.fields import VideoField
from video_encoding.models import Format


class Video(models.Model):
    width = models.PositiveIntegerField(
        editable=False,
        null=True,
    )
    height = models.PositiveIntegerField(
        editable=False,
        null=True,
    )
    duration = models.FloatField(
        editable=False,
        null=True,
    )

    file = VideoField(
        width_field='width',
        height_field='height',
        duration_field='duration',
    )

    format_set = GenericRelation(Format)
