import enum
import os
import shutil
from pathlib import Path
from typing import IO, Any, Generator

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.files.storage import FileSystemStorage

from test_proj.media_library.models import Format, Video
from video_encoding.backends.ffmpeg import FFmpegBackend


class StorageType(enum.Enum):
    LOCAL = enum.auto()
    REMOTE = enum.auto()


@pytest.fixture
def video_path():
    path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(path, 'waterfall.mp4')


@pytest.fixture
def ffmpeg():
    return FFmpegBackend()


@pytest.fixture
def local_video(video_path) -> Generator[Video, None, None]:
    """
    Return a video object which is stored locally.
    """
    video = Video.objects.create()
    video.file.save('test.MTS', File(open(video_path, 'rb')), save=True)
    try:
        yield video
    finally:
        try:
            video.file.delete()
        except ValueError:
            # file has already been deleted
            pass

        for format in video.format_set.all():
            format.file.delete()

        video.delete()


@pytest.fixture
def format(video_path, local_video) -> Generator[Format, None, None]:
    format = Format.objects.create(
        object_id=local_video.pk,
        content_type=ContentType.objects.get_for_model(local_video),
        field_name='file',
        format='mp4_hd',
        progress=100,
    )
    #
    format.file.save('test.MTS', File(open(video_path, 'rb')), save=True)
    yield format


@pytest.fixture
def remote_video(local_video) -> Generator[Video, None, None]:
    """
    Return a video which is stored "remotely".
    """
    storage_path = Path(local_video.file.path).parent

    remote_video = local_video
    remote_video.file.storage = FakeRemoteStorage(storage_path)
    yield remote_video


@pytest.fixture(params=StorageType)
def video(
    request, local_video: Video, remote_video: Video
) -> Generator[Video, None, None]:
    """
    Return a locally and a remotely stored video.
    """
    storage_type = request.param

    if storage_type == StorageType.LOCAL:
        yield local_video
    elif storage_type == StorageType.REMOTE:
        yield remote_video
    else:
        raise ValueError(f"Invalid storage type {storage_type}")


class FakeRemoteStorage(FileSystemStorage):
    """
    Fake remote storage which does not support accessing a file by path.
    """

    def __init__(self, root_path: Path) -> None:
        super().__init__()
        self.root_path = root_path

    def delete(self, name: str) -> None:
        file_path = self.__path(name)
        file_path.unlink()

    def exists(self, name: str) -> bool:
        return self.__path(name).exists()

    def open(self, name: str, mode: str) -> IO[Any]:
        return open(self.__path(name), mode)

    def path(self, *args, **kwargs):
        raise NotImplementedError("Remote storage does not implement path()")

    def _save(self, name: str, content: File) -> str:
        file_path = self.__path(name)
        folder_path = file_path.parent

        if not folder_path.is_dir():
            file_path.parent.mkdir(parents=True)

        if hasattr(content, 'temporary_file_path'):
            shutil.move(content.temporary_file_path(), file_path)
        else:
            with open(file_path, 'wb') as fp:
                fp.write(content.read())

        return str(file_path)

    def __path(self, name: str) -> Path:
        """
        Return path to local file.
        """
        return self.root_path / name
