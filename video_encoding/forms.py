from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


validate_video_file_extension = FileExtensionValidator(
    allowed_extensions=['mp4', 'mov', 'flv'],
)


class VideoField(forms.FileField):
    default_validators = [validate_video_file_extension]

    content_types = ['video/mp4', 'video/quicktime', 'video/x-msvideo',
                     'video/x-ms-wmv']
    max_file_size = 429916160

    def clean(self, *args, **kwargs):
        data = super(VideoField, self).clean(*args, **kwargs)

        if hasattr(data, 'content_type'):
            if data.content_type not in self.content_types:
                raise ValidationError('File type not supported.')

        if hasattr(data, 'size'):
            if data.size > self.max_file_size:
                raise ValidationError('File size is greater than 500 MB.')

        return data
