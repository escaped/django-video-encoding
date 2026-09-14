import pytest

from ..models import Format


@pytest.mark.django_db
def test_update_progress__rejects_out_of_range_values(video_format):
    with pytest.raises(ValueError):
        video_format.update_progress(-1)

    with pytest.raises(ValueError):
        video_format.update_progress(101)

    assert Format.objects.get(pk=video_format.pk).progress == 100


@pytest.mark.django_db
def test_update_progress(video_format):
    video_format.update_progress(50)

    assert Format.objects.get(pk=video_format.pk).progress == 50


@pytest.mark.django_db
def test_update_progress__stores_an_integer(video_format):
    video_format.update_progress(33.6, commit=False)

    assert video_format.progress == 34
    assert str(video_format).endswith('(34%)')


@pytest.mark.django_db
def test_reset_progress(video_format):
    assert video_format.progress == 100

    video_format.reset_progress()

    assert Format.objects.get(pk=video_format.pk).progress == 0
