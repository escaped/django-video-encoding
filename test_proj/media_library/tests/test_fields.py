import os

import pytest

from video_encoding.backends.ffmpeg import FFmpegBackend

from ..models import Video


@pytest.mark.django_db
def test_info_forward(ffmpeg, video, video_path):
    media_info = ffmpeg.get_media_info(video_path)

    assert video.duration == media_info['duration']
    assert video.width == media_info['width']
    assert video.height == media_info['height']


@pytest.mark.django_db
def test_delete(ffmpeg, video):
    video.file.delete()
    video = Video.objects.get(pk=video.pk)
    assert not video.file


def test_check():
    field = Video._meta.get_field('file')
    assert field.check() == FFmpegBackend.check()

    path = os.environ['PATH']
    os.environ['PATH'] = ''
    assert field.check() == FFmpegBackend.check()
    os.environ['PATH'] = path
