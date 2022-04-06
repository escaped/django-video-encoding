import io
import json
import logging
import os
import re
import subprocess
import tempfile
from shutil import which
from typing import Dict, Generator, List, Union

from django.core import checks

from .. import exceptions
from ..config import settings
from .base import BaseEncodingBackend

logger = logging.getLogger(__name__)

# regex to extract the progress (time) from ffmpeg
RE_TIMECODE = re.compile(r'time=(\d+:\d+:\d+.\d+) ')


class FFmpegBackend(BaseEncodingBackend):
    name = 'FFmpeg'

    def __init__(self) -> None:
        self.params: List[str] = [
            '-threads',
            str(settings.VIDEO_ENCODING_THREADS),
            '-y',  # overwrite temporary created file
            '-strict',
            '-2',  # support aac codec (which is experimental)
        ]

        self.ffmpeg_path: str = getattr(
            settings, 'VIDEO_ENCODING_FFMPEG_PATH', which('ffmpeg')
        )
        self.ffprobe_path: str = getattr(
            settings, 'VIDEO_ENCODING_FFPROBE_PATH', which('ffprobe')
        )

        if not self.ffmpeg_path:
            raise exceptions.FFmpegError(
                "ffmpeg binary not found: {}".format(self.ffmpeg_path or '')
            )

        if not self.ffprobe_path:
            raise exceptions.FFmpegError(
                "ffprobe binary not found: {}".format(self.ffmpeg_path or '')
            )

    @classmethod
    def check(cls) -> List[checks.Error]:
        errors = super(FFmpegBackend, cls).check()
        try:
            FFmpegBackend()
        except exceptions.FFmpegError as e:
            errors.append(
                checks.Error(
                    e.msg,
                    hint="Please install ffmpeg.",
                    obj=cls,
                    id='video_conversion.E001',
                )
            )
        return errors

    def _spawn(self, cmd: List[str]) -> subprocess.Popen:
        try:
            return subprocess.Popen(
                cmd,
                shell=False,
                stderr=subprocess.PIPE,  # ffmpeg reports live stats to stderr
                universal_newlines=False,  # stderr will return bytes
            )
        except OSError as e:
            raise exceptions.FFmpegError('Error while running ffmpeg binary') from e

    def encode(
        self, source_path: str, target_path: str, params: List[str]
    ) -> Generator[float, None, None]:
        """
        Encode a video.

        All encoder specific options are passed in using `params`.
        """
        total_time = self.get_media_info(source_path)['duration']

        cmd = [self.ffmpeg_path, '-i', source_path, *self.params, *params, target_path]
        process = self._spawn(cmd)
        # ffmpeg write the progress to stderr
        # each line is either terminated by \n or \r
        reader = io.TextIOWrapper(process.stderr, newline=None)  # type: ignore

        # update progress
        while process.poll() is None:  # is process terminated yet?
            try:
                line = reader.readline()
                # format 00:00:00.00
                time_str = RE_TIMECODE.findall(line)[0]
            except (UnicodeDecodeError, IndexError):
                continue

            # convert time to seconds
            time: float = 0
            for part in time_str.split(':'):
                time = 60 * time + float(part)

            percent = round(time / total_time, 2)
            logger.debug('yield {}%'.format(percent))
            yield percent

        if os.path.getsize(target_path) == 0:
            raise exceptions.FFmpegError("File size of generated file is 0")

        if process.returncode != 0:
            raise exceptions.FFmpegError(
                "`{}` exited with code {:d}".format(
                    ' '.join(map(str, process.args)), process.returncode
                )
            )

        yield 100

    def _parse_media_info(self, data: bytes) -> Dict:
        media_info = json.loads(data)
        media_info['video'] = [
            stream
            for stream in media_info['streams']
            if stream['codec_type'] == 'video'
        ]
        media_info['audio'] = [
            stream
            for stream in media_info['streams']
            if stream['codec_type'] == 'audio'
        ]
        media_info['subtitle'] = [
            stream
            for stream in media_info['streams']
            if stream['codec_type'] == 'subtitle'
        ]
        del media_info['streams']
        return media_info

    def get_media_info(self, video_path: str) -> Dict[str, Union[int, float]]:
        """
        Return information about the given video.
        """
        cmd = [self.ffprobe_path, '-i', video_path]
        cmd.extend(['-hide_banner',  '-loglevel', 'warning'])
        cmd.extend(['-print_format', 'json'])
        cmd.extend(['-show_format', '-show_streams'])

        stdout = subprocess.check_output(cmd)
        media_info = self._parse_media_info(stdout)

        return {
            'duration': float(media_info['format']['duration']),
            'width': int(media_info['video'][0]['width']),
            'height': int(media_info['video'][0]['height']),
        }

    def get_thumbnail(self, video_path: str, at_time: float = 0.5) -> str:
        """
        Extract an image from a video and return its path.

        If the requested thumbnail is not within the duration of the video
        an `InvalidTimeError` is thrown.
        """
        filename = os.path.basename(video_path)
        filename, __ = os.path.splitext(filename)
        _, image_path = tempfile.mkstemp(suffix='_{}.jpg'.format(filename))

        video_duration = self.get_media_info(video_path)['duration']
        if at_time > video_duration:
            raise exceptions.InvalidTimeError()
        thumbnail_time = at_time

        cmd = [self.ffmpeg_path, '-i', video_path, '-vframes', '1']
        cmd.extend(['-ss', str(thumbnail_time), '-y', image_path])

        subprocess.check_call(cmd)

        if not os.path.getsize(image_path):
            # we somehow failed to generate thumbnail
            os.unlink(image_path)
            raise exceptions.InvalidTimeError()

        return image_path
