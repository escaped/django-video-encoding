import pytest
from django.urls import reverse


@pytest.fixture()
def admin_client(django_app, admin_user):
    django_app.set_user(admin_user)
    return django_app


def test_format_inline(admin_client, video):
    url = reverse('admin:media_library_video_change', args=(video.pk,))
    admin_client.get(url)
