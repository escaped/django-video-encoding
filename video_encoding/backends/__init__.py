from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _


def get_backend_class():
    from ..config import settings

    try:
        cls = import_string(settings.VIDEO_ENCODING_BACKEND)
    except ImportError as e:
        raise ImproperlyConfigured(
            _("Cannot retrieve backend '{}'. Error: '{}'.").format(
                settings.VIDEO_ENCODING_BACKEND, e
            )
        )
    return cls


def get_backend():
    from ..config import settings

    cls = get_backend_class()
    return cls(**settings.VIDEO_ENCODING_BACKEND_PARAMS)
