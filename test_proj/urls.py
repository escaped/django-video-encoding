from django.contrib import admin
from django.urls import re_path

from .media_library.views import VideoFormView

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^$', VideoFormView.as_view()),
]
