import pytest
from django.contrib.contenttypes.models import ContentType

from ..models import Format


@pytest.fixture
def video_format(video):
    return Format.objects.create(
        object_id=video.pk,
        content_type=ContentType.objects.get_for_model(video),
        field_name='file',
        format='mp4_hd',
        progress=100,
    )


@pytest.mark.django_db
def test_related_manager(video):
    assert hasattr(video.format_set, 'complete')
    assert hasattr(video.format_set, 'in_progress')


@pytest.mark.django_db
def test_in_progress(video_format):
    video_format.progress = 30
    video_format.save()

    assert Format.objects.complete().count() == 0
    assert Format.objects.in_progress().count() == 1
    assert Format.objects.in_progress()[0].progress < 100


@pytest.mark.django_db
def test_complete(video_format):
    assert Format.objects.in_progress().count() == 0
    assert Format.objects.complete().count() == 1
    assert Format.objects.complete()[0].progress == 100
