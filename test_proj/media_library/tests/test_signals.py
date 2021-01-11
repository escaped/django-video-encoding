import pytest
from matchlib import matches

from video_encoding import signals, tasks
from video_encoding.exceptions import VideoEncodingError

from .. import models


@pytest.mark.django_db
def test_signals(monkeypatch, mocker, local_video: models.Video) -> None:
    """
    Make sure encoding signals are send.

    There are currently 4 signals:
    - encoding_started
    - format_started
    - format_finished
    - encoding_finished
    """
    # encode only to one format
    encoding_format = tasks.settings.VIDEO_ENCODING_FORMATS['FFmpeg'][0]
    monkeypatch.setattr(
        tasks.settings, 'VIDEO_ENCODING_FORMATS', {'FFmpeg': [encoding_format]}
    )

    mocker.patch.object(tasks, '_encode')  # don't encode anything

    listener = mocker.MagicMock()
    signals.encoding_started.connect(listener)
    signals.format_started.connect(listener)
    signals.format_finished.connect(listener)
    signals.encoding_finished.connect(listener)

    tasks.convert_video(local_video.file)

    assert listener.call_count == 4
    # check arguments and make sure they are called in the right order
    # encoding_started
    _, kwargs = listener.call_args_list[0]
    assert kwargs == {
        'signal': signals.encoding_started,
        'sender': models.Video,
        'instance': local_video,
    }

    # format started
    _, kwargs = listener.call_args_list[1]
    assert matches(
        kwargs,
        {
            'signal': signals.format_started,
            'sender': models.Format,
            'instance': local_video,
            'format': ...,
        },
    )
    assert isinstance(kwargs['format'], models.Format)
    assert kwargs['format'].format == encoding_format['name']
    assert kwargs['format'].progress == 0

    # format finished
    _, kwargs = listener.call_args_list[2]
    assert matches(
        kwargs,
        {
            'signal': signals.format_finished,
            'sender': models.Format,
            'instance': local_video,
            'format': ...,
            'result': signals.ConversionResult.SUCCEEDED,
        },
    )
    assert isinstance(kwargs['format'], models.Format)
    assert kwargs['format'].format == encoding_format['name']

    # encoding finished
    _, kwargs = listener.call_args_list[3]
    assert kwargs == {
        'signal': signals.encoding_finished,
        'sender': models.Video,
        'instance': local_video,
    }


@pytest.mark.django_db
def test_signals__encoding_failed(
    monkeypatch, mocker, local_video: models.Video
) -> None:
    """
    Make sure encoding signal reports failed, if the encoding was not succesful.
    """
    # encode only to one format
    encoding_format = tasks.settings.VIDEO_ENCODING_FORMATS['FFmpeg'][0]
    monkeypatch.setattr(
        tasks.settings, 'VIDEO_ENCODING_FORMATS', {'FFmpeg': [encoding_format]}
    )

    mocker.patch.object(
        tasks, '_encode', side_effect=VideoEncodingError()
    )  # encoding should fail

    listener = mocker.MagicMock()
    signals.format_started.connect(listener)
    signals.format_finished.connect(listener)

    tasks.convert_video(local_video.file)

    assert listener.call_count == 2
    # check arguments and make sure they are called in the right order
    # format started
    _, kwargs = listener.call_args_list[0]
    assert matches(kwargs, {'signal': signals.format_started, ...: ...})

    # format finished, but failed
    _, kwargs = listener.call_args_list[1]
    assert matches(
        kwargs,
        {
            'signal': signals.format_finished,
            'sender': models.Format,
            'instance': local_video,
            'format': ...,
            'result': signals.ConversionResult.FAILED,
        },
    )
    assert isinstance(kwargs['format'], models.Format)
    assert kwargs['format'].format == encoding_format['name']


@pytest.mark.django_db
def test_signals__encoding_skipped(
    monkeypatch, mocker, local_video: models.Video, video_format: models.Format
) -> None:
    """
    Make sure encoding signal reports skipped, if file had been encoded before.
    """
    # encode only to one format
    encoding_format = tasks.settings.VIDEO_ENCODING_FORMATS['FFmpeg'][0]
    monkeypatch.setattr(
        tasks.settings, 'VIDEO_ENCODING_FORMATS', {'FFmpeg': [encoding_format]}
    )

    mocker.patch.object(tasks, '_encode')  # don't encode anything
    # encoding has already been done for the given format
    video_format.format = encoding_format["name"]
    video_format.save()

    listener = mocker.MagicMock()
    signals.format_started.connect(listener)
    signals.format_finished.connect(listener)

    tasks.convert_video(local_video.file)

    assert listener.call_count == 2
    # check arguments and make sure they are called in the right order
    # format started
    _, kwargs = listener.call_args_list[0]
    assert matches(kwargs, {'signal': signals.format_started, ...: ...})

    # format finished, but skipped
    _, kwargs = listener.call_args_list[1]
    assert matches(
        kwargs,
        {
            'signal': signals.format_finished,
            'sender': models.Format,
            'instance': local_video,
            'format': ...,
            'result': signals.ConversionResult.SKIPPED,
        },
    )
    assert isinstance(kwargs['format'], models.Format)
    assert kwargs['format'].format == encoding_format['name']
