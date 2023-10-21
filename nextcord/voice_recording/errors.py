# SPDX-License-Identifier: MIT

import nextcord as nc


class OngoingRecordingError(nc.DiscordException):
    """
    Raised when an forbidden action is performed when a recording is ongoing.
    """


class NotRecordingError(nc.DiscordException):
    """
    Raised when stopping a recording is attempted while a recording is not ongoing.
    """


class NotConnectedError(nc.DiscordException):
    """
    Raised when attempting to record without being in a voice channel.
    """


class TmpNotFound(nc.DiscordException):
    """
    Raised when failed attempting to access temp files.
    """


class NoFFmpeg(nc.DiscordException):
    """
    Raised if ffmpeg was not found.
    """


class MultipleHandlersError(nc.DiscordException):
    """
    Raised when trying to set multiple audio handlers.
    """


class ExportUnavailable(nc.DiscordException):
    """
    Raised when exporting is not possible due to an audio handler having been set.
    """
