import pytest

from video_encoding.files import VideoFile


def test_videofile(ffmpeg, video_path):
    media_info = ffmpeg.get_media_info(video_path)

    video_file = VideoFile(open(video_path, mode='rb'))
    assert video_file.duration == media_info['duration']
    assert video_file.width == media_info['width']
    assert video_file.height == media_info['height']


@pytest.mark.django_db
def test_videofile__with_storages(ffmpeg, video, video_path):
    media_info = ffmpeg.get_media_info(video_path)

    video_file = video.file
    assert video_file.duration == media_info['duration']
    assert video_file.width == media_info['width']
    assert video_file.height == media_info['height']
