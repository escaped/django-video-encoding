# django-video-encoding

![PyPI](https://img.shields.io/pypi/v/django-video-encoding?style=flat-square)
![GitHub Workflow Status (master)](https://img.shields.io/github/workflow/status/escaped/django-video-encoding/Test%20&%20Lint/master?style=flat-square)
![Coveralls github branch](https://img.shields.io/coveralls/github/escaped/django-video-encoding/master?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-video-encoding?style=flat-square)
![PyPI - License](https://img.shields.io/pypi/l/django-video-encoding?style=flat-square)

django-video-encoding helps to convert your videos into different formats and resolutions.

## Requirements

* Python 3.6.1 or newer
* ffmpeg and ffprobe

## Installation

1. Install django-video-encoding

   ```sh
   pip install django-video-encoding
   ```

2. Add `video_encoding` to your `INSTALLED_APPS`.

## Integration

Add a `VideoField` and a `GenericRelation(Format)` to your model.
You can optionally store the `width`, `height` and `duration` of the video
by supplying the corresponding field names to the `VideoField`.

```python
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
```

To show all converted videos in the admin, you should add the `FormatInline`
to your `ModelAdmin`

```python
from django.contrib import admin
from video_encoding.admin import FormatInline

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
   inlines = (FormatInline,)

   list_dispaly = ('get_filename', 'width', 'height', 'duration')
   fields = ('file', 'width', 'height', 'duration')
   readonly_fields = fields
```


The conversion of the video should be done in a separate process. Typical
options are [django-rq] or [celery]. We will use `django-rq` in the
following example. The configuration for `celery` is similar.
`django-video-encoding` already provides a task (`convert_all_videos`)
for converting all videos on a model.
This task should be triggered when a video was uploaded. Hence we listen to
the `post-save` signal and enqueue the saved instance for processing.

```python
# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import enqueue

from video_encoding import tasks

from .models import Video


@receiver(post_save, sender=Video)
def convert_video(sender, instance, **kwargs):
    enqueue(tasks.convert_all_videos,
            instance._meta.app_label,
            instance._meta.model_name,
            instance.pk)
```

After a while You can access the converted videos using

```python
video = Video.objects.get(...)
for format in video.format_set.complete().all():
   # do something
```

[django-rq]: https://github.com/ui/django-rq
[celery]: http://www.celeryproject.org/

### Generate a video thumbnail

The backend provides a `get_thumbnail()` method to extract a thumbnail from a video.
Here is a basic example on how to generate the thumbnail and store it in the model.

```python
# models.py
from django.db import models

class Video(models.Model):
   width = models.PositiveIntegerField(editable=False, null=True)
   height = models.PositiveIntegerField(editable=False, null=True)
   duration = models.FloatField(editable=False, null=True)

   thumbnail = ImageField(blank=True)
   file = VideoField(width_field='width', height_field='height',
                     duration_field='duration')

   format_set = GenericRelation(Format)


# tasks.py
from django.core.files import File
from video_encoding.backends import get_backend

from .models import Video


def create_thumbnail(video_pk):
   video = Video.objects.get(pk=video_pk)
   if not video.file:
      # no video file attached
      return

   if video.thumbnail:
      # thumbnail has already been generated
      return

   encoding_backend = get_backend()
   thumbnail_path = encoding_backend.get_thumbnail(video.file.path)
   filename = os.path.basename(self.url),

   try:
      with open(thumbnail_path, 'rb') as file_handler:
         django_file = File(file_handler)
         video.thumbnail.save(filename, django_file)
      video.save()
   finally:
      os.unlink(thumbnail_path)
```

You should run this method in a separate process by using `django-rq`, `celery`
or similar) and enqueue execution from within a `post_save` signal.

```python
# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import enqueue

from . import tasks
from .models import Video


@receiver(post_save, sender=Video)
def create_thumbnail(sender, instance, **kwargs):
    enqueue(tasks.create_thumbnail, instance.pk)
```

### Signals

During the encoding multiple signals are emitted to report the progress.
You can register to the signals as described in the [Django documentation](https://docs.djangoproject.com/en/3.1/topics/signals/#connecting-to-signals-sent-by-specific-senders).

This simple example demonstrates, on how to update the "video model" once the convertion is finished.

```python
# apps.py
from django.apps import AppConfig


class MyAppConfig(AppConfig):
   # ...

    def ready(self) -> None:
      from . import signals  # register signals


# signals.py
from typing import Type

from django.dispatch import receiver
from video_encoding import signals

from myapp.models import Video


@receiver(signals.encoding_finished, sender=Video)
def mark_as_finished(sender: Type[Video], instance: Video) -> None:
   """
   Mark video as "convertion has been finished".
   """
   video.processed = True
   video.save(update_fields=['processed'])
```

#### `signals.encoding_started`

This is sent before the encoding starts.

_Arguments_  
`sender: Type[models.Model]`: Model which contains the `VideoField`.  
`instance: models.Model)`: Instance of the model containing the `VideoField`.

#### `signals.encoding_finished`

Like `encoding_started()`, but sent after the file had been converted into all formats.

_Arguments_  
`sender: Type[models.Model]`: Model which contains the `VideoField`.  
`instance: models.Model)`: Instance of the model containing the `VideoField`.

#### `signals.format_started`

This is sent before the video is converted to one of the configured formats.

_Arguments_  
`sender: Type[models.Model]`: Model which contains the `VideoField`.  
`instance: models.Model)`: Instance of the model containing the `VideoField`.  
`format: Format`: The format instance, which will reference the encoded video file.

#### `signals.format_finished`

Like `format_finished`, but sent after the video encoding process and includes whether the encoding was succesful or not.

_Arguments_  
`sender: Type[models.Model]`: Model which contains the `VideoField`.  
`instance: models.Model)`: Instance of the model containing the `VideoField`.  
`format: Format`: The format instance, which will reference the encoded video file.  
`result: ConversionResult`: Instance of `video_encoding.signals.ConversionResult` and indicates whether the convertion `FAILED`, `SUCCEEDED` or was `SKIPPED`.


## Configuration

**VIDEO_ENCODING_THREADS** (default: `1`)  
Defines how many threads should be used for encoding. This may not be supported
by every backend.

**VIDEO_ENCODING_BACKEND** (default: `'video_encoding.backends.ffmpeg.FFmpegBackend'`)  
Choose the backend for encoding. `django-video-encoding`  only supports `ffmpeg`,
but you can implement your own backend. Feel free to pulish your plugin and
submit a pull request.

**VIDEO_ENCODING_BACKEND_PARAMS** (default: `{}`)  
If your backend requires some special configuration, you can specify them here
as `dict`.

**VIDEO_ENCODING_FORMATS** (for defaults see `video_encoding/config.py`)  
This dictionary defines all required encodings and has some resonable defaults.
If you want to customize the formats, you have to specify `name`,
`extension` and `params` for each format. For example

```python
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
```

## Encoding Backends

### video_encoding.backends.ffmpeg.FFmpegBackend (default)

Backend for using `ffmpeg` and `ffprobe` to convert your videos.

#### Options

**VIDEO_ENCODING_FFMPEG_PATH**  
Path to `ffmpeg`. If no path is provided, the backend uses `which` to
locate it.
**VIDEO_ENCODING_FFPROBE_PATH**  
Path to `ffprobe`. If no path is provided, the backend uses `which` to
locate it.

### Custom Backend

You can implement a custom encoding backend. Create a new class which inherits from
[`video_encoding.backends.base.BaseEncodingBackend`](video_encoding/backends/base.py).
You must set the property `name` and implement the methods `encode`, `get_media_info`
and `get_thumbnail`. For further details see the reference implementation:
[`video_encoding.backends.ffmpeg.FFmpegBackend`](video_encoding/backends/ffmpeg.py).

If you want to open source your backend, follow these steps.

1. create a packages named django-video-encoding-BACKENDNAME
2. publish your package to [pypi]
3. Submit a pull requests with the following changes:

   * add the package to `extra_requires`
   * provide reasonable defaults for `VIDEO_ENCODING_FORMATS`

[pypi]: https://pypi.python.org/pypi

## Development

This project uses [poetry](https://poetry.eustace.io/) for packaging and
managing all dependencies and [pre-commit](https://pre-commit.com/) to run
[flake8](http://flake8.pycqa.org/), [isort](https://pycqa.github.io/isort/),
[mypy](http://mypy-lang.org/) and [black](https://github.com/python/black).

Additionally, [pdbpp](https://github.com/pdbpp/pdbpp) and [better-exceptions](https://github.com/qix-/better-exceptions) are installed to provide a better debugging experience.
To enable `better-exceptions` you have to run `export BETTER_EXCEPTIONS=1` in your current session/terminal.

Clone this repository and run

```bash
poetry install
poetry run pre-commit install
```

to create a virtual enviroment containing all dependencies.
Afterwards, You can run the test suite using

```bash
poetry run pytest
```

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/)
style.

### Cookiecutter template

This project was created using [cruft](https://github.com/cruft/cruft) and the
[cookiecutter-pyproject](https://github.com/escaped/cookiecutter-pypackage) template.
In order to update this repository to the latest template version run

```sh
cruft update
```

in the root of this repository.
