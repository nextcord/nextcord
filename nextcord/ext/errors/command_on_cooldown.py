from typing import Callable, Any
from .command_error import CommandError
from nextcord.ext.interactions import Cooldown
from nextcord.ext.abc import ContextBase

class CommandOnCooldown(CommandError):
    """Exception raised when the command being invoked is on cooldown.

    This inherits from :exc:`CommandError`

    Attributes
    -----------
    cooldown: :class:`.Cooldown`
        A class with attributes ``rate`` and ``per`` similar to the
        :func:`.cooldown` decorator.
    type: :class:`BucketType`
        The type associated with the cooldown.
    retry_after: :class:`float`
        The amount of seconds to wait before you can retry again.
    """

    def __init__(self, cooldown: Cooldown, retry_after: float, type: Callable[[ContextBase], Any]) -> None:
        self.cooldown: Cooldown = cooldown
        self.retry_after: float = retry_after
        self.type: Callable[[ContextBase], Any] = type
        super().__init__(f'You are on cooldown. Try again in {retry_after:.2f}s')