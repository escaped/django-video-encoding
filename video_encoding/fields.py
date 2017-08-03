from django.db.models.fields.files import (FieldFile, FileField,
                                           ImageFileDescriptor)
from django.utils.translation import ugettext as _

from .backends import get_backend_class
from .files import VideoFile
from .forms import VideoField as VideoFormField


class VideoFileDescriptor(ImageFileDescriptor):
    pass


class VideoFieldFile(VideoFile, FieldFile):
    def delete(self, save=True):
        # Clear the video info cache
        if hasattr(self, '_info_cache'):
            del self._info_cache
        super(VideoFieldFile, self).delete(save=save)


class VideoField(FileField):
    attr_class = VideoFieldFile
    descriptor_class = VideoFileDescriptor
    description = _("Video")

    def __init__(self, verbose_name=None, name=None, duration_field=None,
                 width_field=None, height_field=None,
                 **kwargs):
        self.duration_field = duration_field
        self.width_field, self.height_field = width_field, height_field
        super(VideoField, self).__init__(verbose_name, name, **kwargs)

    def check(self, **kwargs):
        errors = super(VideoField, self).check(**kwargs)
        errors.extend(self._check_backend())
        return errors

    def _check_backend(self):
        backend = get_backend_class()
        return backend.check()

    def to_python(self, data):
        # use FileField method
        return super(VideoField, self).to_python(data)

    def update_dimension_fields(self, instance, force=False, *args, **kwargs):
        _file = getattr(instance, self.attname)

        # we need a real file
        if not _file._committed:
            return

        if not self.duration_field:
            return

        # Nothing to update if we have no file and not being forced to update.
        if not _file and not force:
            return
        if getattr(instance, self.duration_field) and not force:
            return

        # get duration if file is defined
        duration = _file.duration if _file else None

        # update duration
        setattr(instance, self.duration_field, duration)

    def formfield(self, **kwargs):
        # use normal FileFieldWidget for now
        defaults = {'form_class': VideoFormField}
        defaults.update(kwargs)
        return super().formfield(**kwargs)
