from nextcord import Thread
from nextcord.abc import GuildChannel
from typing import Union
from .check_failure import CheckFailure



class NSFWChannelRequired(CheckFailure):
    """Exception raised when a channel does not have the required NSFW setting.

    This inherits from :exc:`CheckFailure`.

    .. versionadded:: 1.1

    Parameters
    -----------
    channel: Union[:class:`.abc.GuildChannel`, :class:`.Thread`]
        The channel that does not have NSFW enabled.
    """

    def __init__(self, channel: Union[GuildChannel, Thread]) -> None:
        self.channel: Union[GuildChannel, Thread] = channel
        super().__init__(
            f"Channel '{channel}' needs to be NSFW for this command to work.")