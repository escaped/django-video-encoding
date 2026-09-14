import re

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Video


@pytest.mark.django_db
def test_video_form_renders(client):
    response = client.get('/')

    assert response.status_code == 200
    assert 'Video Upload' in response.content.decode()


@pytest.mark.django_db
def test_video_upload_through_form(client, video_path, settings, tmp_path):
    """
    Upload a real video through the form and verify the rendered page and
    the database state.
    """
    settings.MEDIA_ROOT = tmp_path

    with open(video_path, 'rb') as file_handler:
        upload = SimpleUploadedFile(
            'waterfall.mp4', file_handler.read(), content_type='video/mp4'
        )

    response = client.post('/', {'file': upload}, follow=True)

    assert response.status_code == 200
    html = response.content.decode()
    assert re.search(r'Duration: [\d.]+s, 1280x720', html)

    video = Video.objects.get()
    assert video.file.name == 'waterfall.mp4'
    assert video.file.name in html
    assert video.width == 1280
    assert video.height == 720
    assert video.duration == pytest.approx(2.0, abs=0.1)
    assert (tmp_path / video.file.name).is_file()
