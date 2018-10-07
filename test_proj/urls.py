from django.conf.urls import url
from django.contrib import admin

from .media_library.views import VideoFormView


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', VideoFormView.as_view()),
]
