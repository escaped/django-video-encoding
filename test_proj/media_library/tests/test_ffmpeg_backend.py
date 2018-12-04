import os
import tempfile

import pytest
from PIL import Image

from video_encoding import exceptions
from video_encoding.backends.ffmpeg import FFmpegBackend


def test_get_media_info(ffmpeg, video_path):
    media_info = ffmpeg.get_media_info(video_path)

    assert media_info == {'width': 1280,
                          'height': 720,
                          'duration': 2.022}


def test_encode(ffmpeg, video_path):
    __, target_path = tempfile.mkstemp(suffix='.mp4')
    encoding = ffmpeg.encode(video_path, target_path, ['-vf', 'scale=-2:320',
                                                       '-r', '20',
                                                       '-codec:v', 'libx264'])
    percent = next(encoding)
    assert 0 <= percent <= 100
    while percent:
        assert 0 <= percent <= 100
        try:
            percent = next(encoding)
        except StopIteration:
            break

    assert percent == 100
    assert os.path.isfile(target_path)
    media_info = ffmpeg.get_media_info(target_path)
    assert media_info == {'width': 568,
                          'height': 320,
                          'duration': 2.1}


def test_get_thumbnail(ffmpeg, video_path):
    thumbnail_path = ffmpeg.get_thumbnail(video_path)

    assert os.path.isfile(thumbnail_path)
    with Image.open(thumbnail_path) as im:
        width, height = im.size
        assert width == 1280
        assert height == 720


def test_get_thumbnail__invalid_time(ffmpeg, video_path):
    with pytest.raises(exceptions.InvalidTimeError):
        ffmpeg.get_thumbnail(video_path, at_time=1000000)


@pytest.mark.parametrize(
    'offset', (0, 0.02),
)
def test_get_thumbnail__too_close_to_the_end(ffmpeg, video_path, offset):
    """
    If the selected time point is close to the end of the video,
    a video frame cannot be extracted.
    """
    duration = ffmpeg.get_media_info(video_path)['duration']

    with pytest.raises(exceptions.InvalidTimeError):
        ffmpeg.get_thumbnail(
            video_path, at_time=duration - offset,
        )


def test_check():
    assert FFmpegBackend.check() == []

    path = os.environ['PATH']
    os.environ['PATH'] = ''
    assert len(FFmpegBackend.check()) == 1
    os.environ['PATH'] = path
