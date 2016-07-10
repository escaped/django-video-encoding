import pytest
from django.conf import settings

from video_encoding.tasks import convert_all_videos, convert_video


@pytest.mark.django_db
def test_encoding(video):
    assert video.format_set.count() == 0

    convert_video(video.file)

    assert video.format_set.count() == 4

    formats = dict([(o['name'], o)
                    for o in settings.VIDEO_ENCODING_FORMATS['FFmpeg']])
    assert set(video.format_set.values_list('format', flat=True)) == set(formats.keys())  # NOQA

    for f in video.format_set.all():
        assert formats[f.format]['extension'] == f.file.name.split('.')[-1]
        assert f.progress == 100


@pytest.mark.django_db
def test_encoding_auto_fields(video):
    assert video.format_set.count() == 0

    convert_all_videos(
        video._meta.app_label,
        video._meta.model_name,
        video.id,
    )

    assert video.format_set.count() == 4
