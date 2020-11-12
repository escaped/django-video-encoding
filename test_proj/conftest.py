import enum
import os
import shutil
from pathlib import Path
from typing import IO, Any, Generator

import pytest
from django.core.files import File
from django.core.files.storage import FileSystemStorage

from test_proj.media_library.models import Video
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
def local_video(video_path):
    video = Video()
    video.file.save('test.MTS', File(open(video_path, 'rb')), save=True)
    video.save()
    video.refresh_from_db()
    return video


@pytest.fixture
def remote_video(mocker, local_video):
    video = Video.objects.get(pk=local_video.pk)
    video_path = Path(video.file.path)

    def path(name: str) -> Path:
        return video_path.parent / name

    def remote_exists(name: str) -> bool:
        return path(name).exists()

    def remote_open(name: str, mode: str) -> IO[Any]:
        return open(video_path, mode)

    def remote_path(*args, **kwargs):
        raise NotImplementedError("Remote storage does not implement path()")

    def remote_save(name: str, content: File) -> str:
        file_path = path(name)
        folder_path = file_path.parent

        if not folder_path.is_dir():
            file_path.parent.mkdir(parents=True)

        if hasattr(content, 'temporary_file_path'):
            shutil.move(content.temporary_file_path(), file_path)
        else:
            with open(file_path, 'wb') as fp:
                fp.write(content.read())

        return str(file_path)

    def remote_delete(name: str) -> None:
        file_path = path(name)
        file_path.unlink()

    storage = FileSystemStorage()
    mocker.patch.object(storage, 'exists', remote_exists)
    mocker.patch.object(storage, 'open', remote_open)
    mocker.patch.object(storage, 'path', remote_path)
    mocker.patch.object(storage, '_save', remote_save)
    mocker.patch.object(storage, 'delete', remote_delete)

    video.file.storage = storage
    yield video


@pytest.fixture(params=StorageType)
def video(
    request, local_video: Video, remote_video: Video
) -> Generator[Video, None, None]:
    storage_type = request.param

    if storage_type == StorageType.LOCAL:
        yield local_video
    elif storage_type == StorageType.REMOTE:
        yield remote_video
    else:
        raise ValueError(f"Invalid storage type {storage_type}")
