import io
import os
import subprocess
import tempfile

import pytest
from PIL import Image

from video_encoding import exceptions
from video_encoding.backends.ffmpeg import FFmpegBackend


class FakeFFmpegProcess:
    """
    Minimal stand-in for a running ffmpeg process replaying canned stderr.

    A real process writes progress lines while it runs; ``BytesIO`` delivers
    them all at once and ``TextIOWrapper`` may read ahead, so ``poll`` simply
    reports the process as running for as many loop iterations as there are
    canned lines.
    """

    def __init__(self, lines):
        self.lines = list(lines)
        self.stderr = io.BytesIO(b''.join(self.lines))
        self.returncode = 0
        self.polls = 0

    def poll(self):
        self.polls += 1
        return None if self.polls <= len(self.lines) else 0


def test_get_media_info(ffmpeg, video_path):
    media_info = ffmpeg.get_media_info(video_path)

    assert media_info['width'] == 1280
    assert media_info['height'] == 720
    # Different ffmpeg versions report the container duration with a
    # slightly different precision, so only require a close match.
    assert media_info['duration'] == pytest.approx(2.022, abs=0.05)


def test_encode(ffmpeg, video_path):
    __, target_path = tempfile.mkstemp(suffix='.mp4')
    encoding = ffmpeg.encode(
        video_path,
        target_path,
        ['-vf', 'scale=-2:320', '-r', '90', '-codec:v', 'libx264'],
    )
    percent = next(encoding)
    assert 0 <= percent <= 100
    for percent in encoding:
        assert 0 <= percent <= 100

    assert percent == 100
    assert os.path.isfile(target_path)
    media_info = ffmpeg.get_media_info(target_path)
    assert media_info['width'] == 568
    assert media_info['height'] == 320
    # See `test_get_media_info` for why the duration is compared loosely.
    assert media_info['duration'] == pytest.approx(2.027, abs=0.05)


def test_encode_progress_is_percent(ffmpeg, mocker, tmp_path):
    process = FakeFFmpegProcess(
        [
            b'frame= 10 time=00:00:01.00 bitrate=0kbits/s\r',
            b'frame= 20 time=00:00:02.00 bitrate=0kbits/s\r',
            b'frame= 30 time=00:00:05.00 bitrate=0kbits/s\r',
        ]
    )
    mocker.patch.object(ffmpeg, '_spawn', return_value=process)
    mocker.patch.object(ffmpeg, 'get_media_info', return_value={'duration': 4.0})
    target_path = tmp_path / 'encoded.mp4'
    target_path.write_bytes(b'ffmpeg output')

    progress = list(ffmpeg.encode('source.mp4', str(target_path), []))

    assert progress == [25.0, 50.0, 100, 100]


def test_encode_ignores_invalid_utf8(ffmpeg, mocker, tmp_path):
    process = FakeFFmpegProcess(
        [
            b'  Metadata:\n',
            b'    com.apple.quicktime.artwork: \xff\xfe\n',
            b'frame= 10 time=00:00:01.00 bitrate=0kbits/s\r',
        ]
    )
    mocker.patch.object(ffmpeg, '_spawn', return_value=process)
    mocker.patch.object(ffmpeg, 'get_media_info', return_value={'duration': 4.0})
    target_path = tmp_path / 'encoded.mp4'
    target_path.write_bytes(b'ffmpeg output')

    progress = list(ffmpeg.encode('source.mp4', str(target_path), []))

    assert progress == [25.0, 100]


@pytest.fixture()
def small_video_path(ffmpeg, tmp_path):
    path = tmp_path / 'small.mp4'
    subprocess.check_call(
        [
            ffmpeg.ffmpeg_path,
            '-v',
            'error',
            '-f',
            'lavfi',
            '-i',
            'testsrc=size=320x240:rate=10',
            '-t',
            '1',
            '-pix_fmt',
            'yuv420p',
            str(path),
        ]
    )
    return str(path)


def test_default_formats_do_not_upscale(ffmpeg, small_video_path, settings, tmp_path):
    source_info = ffmpeg.get_media_info(small_video_path)

    for options in settings.VIDEO_ENCODING_FORMATS['FFmpeg']:
        target_path = tmp_path / 'encoded.{}'.format(options['extension'])
        list(ffmpeg.encode(small_video_path, str(target_path), options['params']))
        target_info = ffmpeg.get_media_info(str(target_path))

        assert target_info['width'] == source_info['width']
        assert target_info['height'] == source_info['height']


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
    'offset',
    (0, 0.02),
)
def test_get_thumbnail__too_close_to_the_end(ffmpeg, video_path, offset):
    """
    If the selected time point is close to the end of the video,
    a video frame cannot be extracted.
    """
    duration = ffmpeg.get_media_info(video_path)['duration']

    with pytest.raises(exceptions.InvalidTimeError):
        ffmpeg.get_thumbnail(
            video_path,
            at_time=duration - offset,
        )


def test_check():
    assert FFmpegBackend.check() == []

    path = os.environ['PATH']
    os.environ['PATH'] = ''
    assert len(FFmpegBackend.check()) == 1
    os.environ['PATH'] = path


def test_missing_binary_error_message(mocker):
    mocker.patch('video_encoding.backends.ffmpeg.which', return_value=None)
    with pytest.raises(exceptions.FFmpegError, match=r'^ffmpeg binary not found: $'):
        FFmpegBackend()

    mocker.patch(
        'video_encoding.backends.ffmpeg.which',
        side_effect=['/usr/bin/ffmpeg', None],
    )
    with pytest.raises(exceptions.FFmpegError, match=r'^ffprobe binary not found: $'):
        FFmpegBackend()
