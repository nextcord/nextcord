# SPDX-License-Identifier: MIT

import nextcord.errors as nc_errors


class OngoingRecordingError(nc_errors.DiscordException):
    """
    Raised when an forbidden action is performed when a recording is ongoing.
    """


class NotRecordingError(nc_errors.DiscordException):
    """
    Raised when stopping a recording is attempted while a recording is not ongoing.
    """


class NotConnectedError(nc_errors.DiscordException):
    """
    Raised when attempting to record without being in a voice channel.
    """


class TmpNotFound(nc_errors.DiscordException):
    """
    Raised when failed attempting to access temp files.
    """

class EmptyRecordingError(nc_errors.DiscordException):
    """
    Raised when the recording was empty.
    """


class NoFFmpeg(nc_errors.DiscordException):
    """
    Raised if ffmpeg was not found.
    """


class MultipleHandlersError(nc_errors.DiscordException):
    """
    Raised when trying to set multiple audio handlers.
    """


class ExportUnavailable(nc_errors.DiscordException):
    """
    Raised when exporting is not possible due to an audio handler having been set.
    """
