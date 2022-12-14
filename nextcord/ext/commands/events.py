# SPDX-License-Identifier: MIT

from enum import Enum

__all__ = ("BotEvents",)


class BotEvents(Enum):
    COMMAND = "command"
    COMMAND_COMPLETION = "command_completion"
    COMMAND_ERROR = "command_error"
