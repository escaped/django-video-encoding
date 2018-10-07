from django import forms
from django.views.generic import FormView

from video_encoding.fields import VideoField

from .models import Video


class VideoForm(forms.ModelForm):

    class Meta:
        fields = ('file',)
        model = Video


class VideoFormView(FormView):
    form_class = VideoForm

    success_url = '/'
    template_name = 'video_form.html'

    def get_context_data(self, *args, **kwargs):
        context = super(VideoFormView, self).get_context_data(*args, **kwargs)
        context['videos'] = Video.objects.all()
        return context

    def form_valid(self, form):
        form.save()  # store video to database
        return super(VideoFormView, self).form_valid(form)
