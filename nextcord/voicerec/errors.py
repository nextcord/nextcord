"""
The MIT License (MIT)

:copyright: (c) 2021-present Nextcord Developers

:license: See license for more info
"""

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


class InvalidTempType(DiscordException):
    """
    Raised when attempting to record with an invalid temp file type.
    """


class TempNotFound(DiscordException):
    """
    Raised when failed attempting to access temp files.
    """


class NoFFmpeg(DiscordException):
    """
    Raised if ffmpeg was not found.
    """
