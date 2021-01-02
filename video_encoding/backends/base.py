import abc
from typing import Dict, Generator, List, Union

from django.core import checks


class BaseEncodingBackend(metaclass=abc.ABCMeta):
    # used as key to get all defined formats from `VIDEO_ENCODING_FORMATS`
    name = 'undefined'

    @classmethod
    def check(cls) -> List[checks.Error]:
        return []

    @abc.abstractmethod
    def encode(
        self, source_path: str, target_path: str, params: List[str]
    ) -> Generator[float, None, None]:  # pragma: no cover
        """
        Encode a video.

        All encoder specific options are passed in using `params`.
        """

    @abc.abstractmethod
    def get_media_info(
        self, video_path: str
    ) -> Dict[str, Union[int, float]]:  # pragma: no cover
        """
        Return duration, width and height of the video.
        """

    @abc.abstractmethod
    def get_thumbnail(
        self, video_path: str, at_time: float = 0.5
    ) -> str:  # pragma: no cover
        """
        Extract an image from a video and return its path.

        If the requested thumbnail is not within the duration of the video
        an `InvalidTimeError` is thrown.
        """
