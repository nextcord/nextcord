# SPDX-License-Identifier: MIT

from nextcord import DiscordException


class OngoingRecordingError(DiscordException):
    """
    Raised when an forbidden action is performed when a recording is ongoing.
    """


class NotRecordingError(DiscordException):
    """
    Raised when stopping a recording is attempted while a recording is not ongoing.
    """


class NotConnectedError(DiscordException):
    """
    Raised when attempting to record without being in a voice channel.
    """


class TmpNotFound(DiscordException):
    """
    Raised when failed attempting to access temp files.
    """


class NoFFmpeg(DiscordException):
    """
    Raised if ffmpeg was not found.
    """


class MultipleHandlersError(DiscordException):
    """
    Raised when trying to set multiple audio handlers.
    """


class ExportUnavailable(DiscordException):
    """
    Raised when exporting is not possible due to an audio handler having been set.
    """
