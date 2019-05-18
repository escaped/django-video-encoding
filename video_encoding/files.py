import os

from django.core.files import File
from django.core.files.storage import default_storage

from .backends import get_backend
from .exceptions import FFmpegError


class VideoFile(File):
    """
    A mixin for use alongside django.core.files.base.File, which provides
    additional features for dealing with videos.
    """

    def _get_width(self):
        """
        Returns video width in pixels.
        """
        return self._get_video_info().get('width', 0)
    width = property(_get_width)

    def _get_height(self):
        """
        Returns video height in pixels.
        """
        return self._get_video_info().get('height', 0)
    height = property(_get_height)

    def _get_duration(self):
        """
        Returns duration in seconds.
        """
        return self._get_video_info().get('duration', 0)
    duration = property(_get_duration)

    def _get_video_info(self):
        """
        Returns basic information about the video as dictionary.
        """
        if not hasattr(self, '_info_cache'):
            encoding_backend = get_backend()
            try:
                _path = getattr(self, 'path', self.name)
            except NotImplementedError:
                _path = self.name
            try:
                path = default_storage.path(_path)
            except NotImplementedError:
                path = default_storage.url(_path)
            try:
                self._info_cache = encoding_backend.get_media_info(path)
            except FFmpegError:
                self._info_cache = {}
        return self._info_cache
