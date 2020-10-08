import os

import pytest
from django.core.files import File

from test_proj.media_library.models import Video
from video_encoding.backends.ffmpeg import FFmpegBackend


@pytest.fixture
def video_path():
    path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(path, 'waterfall.mp4')


@pytest.fixture
def ffmpeg():
    return FFmpegBackend()


@pytest.fixture
def video(video_path):
    video = Video()
    video.file.save('test.MTS', File(open(video_path, 'rb')), save=True)
    video.save()
    video.refresh_from_db()
    return video
