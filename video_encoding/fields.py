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

        # Nothing to update if the field doesn't have dimension fields or if
        # the field is deferred.
        has_dimension_fields = self.width_field or self.height_field
        if not has_dimension_fields or self.attname not in instance.__dict__:
            return

        # getattr will call the VideoFileDescriptor's __get__ method, which
        # coerces the assigned value into an instance of self.attr_class
        # (ImageFieldFile in this case).
        file = getattr(instance, self.attname)

        # Nothing to update if we have no file and not being forced to update.
        if not file and not force:
            return

        dimension_fields_filled = not(
            (self.width_field and not getattr(instance, self.width_field)) or
            (self.height_field and not getattr(instance, self.height_field))
        )

        # When both dimension fields have values, we are most likely loading
        # data from the database or updating an image field that already had
        # an image stored.  In the first case, we don't want to update the
        # dimension fields because we are already getting their values from the
        # database.  In the second case, we do want to update the dimensions
        # fields and will skip this return because force will be True since we
        # were called from ImageFileDescriptor.__set__.
        if dimension_fields_filled and not force:
            return

        # file should be an instance of ImageFieldFile or should be None.
        if file:
            width = file.width
            height = file.height
        else:
            # No file, so clear dimensions fields.
            width = None
            height = None

        # Update the width and height fields.
        if self.width_field:
            setattr(instance, self.width_field, width)
        if self.height_field:
            setattr(instance, self.height_field, height)

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
