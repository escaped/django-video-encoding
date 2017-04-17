=====================
django-video-encoding
=====================


.. image:: https://img.shields.io/pypi/v/django-video-encoding.svg
    :target: https://pypi.python.org/pypi/django-video-encoding

.. image:: https://travis-ci.org/escaped/django-video-encoding.png?branch=master
    :target: http://travis-ci.org/escaped/django-video-encoding
    :alt: Build Status

.. image:: https://coveralls.io/repos/github/escaped/django-video-encoding/badge.svg?branch=master
    :target: https://coveralls.io/github/escaped/django-video-encoding?branch=master
    :alt: Coverage

.. image:: https://img.shields.io/pypi/pyversions/django-video-encoding.svg

.. image:: https://img.shields.io/pypi/status/django-video-encoding.svg

.. image:: https://img.shields.io/pypi/l/django-video-encoding.svg


django-video-encoding helps to convert your videos into different formats and resolutions.



Installation
============

#. Install django-video-encoding ::

    pip install django-video-encoding

#. Add ``video_encoding`` to your ``INSTALLED_APPS``.



Integration
===========

Add a ``VideoField`` and a ``GenericRelation(Format)`` to your model.
You can optionally store the ``width``, ``height`` and ``duration`` of the video
by supplying the corresponding field names to the ``VideoField``. ::

   from django.contrib.contenttypes.fields import GenericRelation
   from django.db import models
   from video_encoding.fields import VideoField
   from video_encoding.models import Format


   class Video(models.Model):
      width = models.PositiveIntegerField(editable=False, null=True)
      height = models.PositiveIntegerField(editable=False, null=True)
      duration = models.FloatField(editable=False, null=True)

      file = VideoField(width_field='width', height_field='height',
                        duration_field='duration')

      format_set = GenericRelation(Format)


To show all converted videos in the admin, you should add the ``FormatInline``
to your ``ModelAdmin`` ::

   from django.contrib import admin
   from video_encoding.admin import FormatInline

   from .models import Video


   @admin.register(Video)
   class VideoAdmin(admin.ModelAdmin):
      inlines = (FormatInline,)

      list_dispaly = ('get_filename', 'width', 'height', 'duration')
      fields = ('file', 'width', 'height', 'duration')
      readonly_fields = fields


The conversion of the video should be done in a separate process. Typical
options are django-rq_ or celery_. We will use ``django-rq`` in the
following example. The configuration for ``celery`` is similar.
``django-video-encoding`` already provides a task (``convert_all_videos``)
for converting all videos on a model.
This task should be triggered when a video was uploaded. Hence we listen to
the ``post-save`` signal and enqueue the saved instance for processing. ::

   # signals.py
   from django.db.models.signals import post_save
   from django.dispatch import receiver
   from django_rq import enqueue

   from . import tasks
   from .models import Video


   @receiver(post_save, sender=Video)
   def convert_video(sender, instance, **kwargs):
       enqueue(tasks.convert_all_videos,
               instance.meta.app_label,
               instance.meta.model_name
               instance.pk)

After a while You can access the converted videos using ::

   video = Video.objects.get(...)
   for format in video.format_set.complete().all():
      # do something

.. _django-rq: https://github.com/ui/django-rq
.. _celery: http://www.celeryproject.org/



Configuration
=============

**VIDEO_ENCODING_THREADS** (default: ``1``)
Defines how many threads should be used for encoding. This may not be supported
by every backend.

**VIDEO_ENCODING_BACKEND** (default: ``'video_encoding.backends.ffmpeg.FFmpegBackend'``)
Choose the backend for encoding. ``django-video-encoding``  only supports ``ffmpeg``,
but you can implement your own backend. Feel free to pulish your plugin and
submit a pull request.

**VIDEO_ENCODING_BACKEND_PARAMS** (default: ``{}``)
If your backend requires some special configuration, you can specify them here
as ``dict``.

**VIDEO_ENCODING_FORMATS** (for defaults see ``video_encoding/config.py``)
This dictionary defines all required encodings and has some resonable defaults.
If you want to customize the formats, you have to specify ``name``,
``extension`` and ``params`` for each format. For example ::

    VIDEO_ENCODING_FORMATS = {
        'FFmpeg': [
            {
                'name': 'webm_sd',
                'extension': 'webm',
                'params': [
                    '-b:v', '1000k', '-maxrate', '1000k', '-bufsize', '2000k',
                    '-codec:v', 'libvpx', '-r', '30',
                    '-vf', 'scale=-1:480', '-qmin', '10', '-qmax', '42',
                    '-codec:a', 'libvorbis', '-b:a', '128k', '-f', 'webm',
               ],
            },
         ]


Encoding Backends
=================

video_encoding.backends.ffmpeg.FFmpegBackend (default)
------------------------------------------------------
Backend for using ``ffmpeg`` and ``ffprobe`` to convert your videos.

Options
.......

**VIDEO_ENCODING_FFMPEG_PATH**
Path to ``ffmpeg``. If no path is provided, the backend uses ``which`` to
locate it.
**VIDEO_ENCODING_FFPROBE_PATH**
Path to ``ffprobe``. If no path is provided, the backend uses ``which`` to
locate it.


Custom Backend
--------------

You can implement a custom encoding backend. Create a new class which inherits
from ``video_encoding.backends.base.BaseEncodingBackend``. You must set the
property ``name`` and implement the methods ``encode``, ``get_media_info`` and
``get_thumbnail``. For further details see the reference implementation:
``video_encoding.backends.ffmpeg.FFmpegBackend``.


If you want to open source your backend, follow these steps.

1. create a packages named django-video-encoding-BACKENDNAME
2. publish your package to pypi_
3. Submit a pull requests with the following changes:

   * add the package to ``extra_requires``
   * provide reasonable defaults for ``VIDEO_ENCODING_FORMATS``

.. _pypi: https://pypi.python.org/pypi
