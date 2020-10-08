import pytest
from django.urls import reverse


@pytest.fixture()
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client


def test_format_inline(admin_client, video):
    url = reverse('admin:media_library_video_change', args=(video.pk,))
    admin_client.get(url)
