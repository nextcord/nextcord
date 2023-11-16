# SPDX-License-Identifier: MIT

import nextcord.errors as nc_errors


class RecordingException(nc_errors.DiscordException):
    """Raised when any recording error occurs.

    .. versionadded:: 3.0
    """

class OngoingRecordingError(RecordingException):
    """Raised when an forbidden action is performed when a recording is ongoing.

    Subclass of :exc:`RecordingException`
    """


class NotRecordingError(RecordingException):
    """Raised when stopping a recording is attempted while a recording is not ongoing.

    Subclass of :exc:`RecordingException`
    """


class NotConnectedError(RecordingException):
    """Raised when attempting to record without being in a voice channel.

    Subclass of :exc:`RecordingException`
    """


class TmpNotFound(RecordingException):
    """Raised when failed attempting to access temp files.

    Subclass of :exc:`RecordingException`
    """


class EmptyRecordingError(RecordingException):
    """Raised when the recording was empty.

    Subclass of :exc:`RecordingException`
    """


class NoFFmpeg(RecordingException):
    """Raised if ffmpeg was not found.

    Subclass of :exc:`RecordingException`
    """


class MultipleHandlersError(RecordingException):
    """Raised when trying to set multiple audio handlers.
    
    Subclass of :exc:`RecordingException`
    """


class ExportUnavailable(RecordingException):
    """Raised when exporting is not possible due to an audio handler having been set.

    Subclass of :exc:`RecordingException`
    """
