# SPDX-License-Identifier: MIT

import nextcord.errors as nextcord_errors


class OngoingRecordingError(nextcord_errors.DiscordException):
    """
    Raised when an forbidden action is performed when a recording is ongoing.
    """


class NotRecordingError(nextcord_errors.DiscordException):
    """
    Raised when stopping a recording is attempted while a recording is not ongoing.
    """


class NotConnectedError(nextcord_errors.DiscordException):
    """
    Raised when attempting to record without being in a voice channel.
    """


class TmpNotFound(nextcord_errors.DiscordException):
    """
    Raised when failed attempting to access temp files.
    """


class NoFFmpeg(nextcord_errors.DiscordException):
    """
    Raised if ffmpeg was not found.
    """


class MultipleHandlersError(nextcord_errors.DiscordException):
    """
    Raised when trying to set multiple audio handlers.
    """


class ExportUnavailable(nextcord_errors.DiscordException):
    """
    Raised when exporting is not possible due to an audio handler having been set.
    """
