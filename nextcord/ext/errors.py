from typing import Any, Callable, List, Optional
from nextcord.errors import DiscordException
from .context import Context

__all__ = (
    "CommandError",
    "CheckFailure",
    "CheckAnyFailure",
)


class CommandError(DiscordException):
    r"""The base exception type for all command related errors.

    This inherits from :exc:`nextcord.DiscordException`.

    This exception and exceptions inherited from it are handled
    in a special way as they are caught and passed into a special event
    from :class:`.Bot`\, :func:`.on_command_error`.
    """

    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        if message is not None:
            # clean-up @everyone and @here mentions
            m = message.replace(
                '@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
            super().__init__(m, *args)
        else:
            super().__init__(*args)


class CheckFailure(CommandError):
    """Exception raised when the predicates in :attr:`.Command.checks` have failed.

    This inherits from :exc:`CommandError`
    """
    pass


class CheckAnyFailure(CheckFailure):
    """Exception raised when all predicates in :func:`check_any` fail.

    This inherits from :exc:`CheckFailure`.

    .. versionadded:: 1.3

    Attributes
    ------------
    errors: List[:class:`CheckFailure`]
        A list of errors that were caught during execution.
    checks: List[Callable[[:class:`Context`], :class:`bool`]]
        A list of check predicates that failed.
    """

    def __init__(self, errors: List[CheckFailure], checks: List[Callable[[Context], bool]]) -> None:
        self.checks: List[CheckFailure] = checks
        self.errors: List[Callable[[Context], bool]] = errors
        super().__init__('You do not have permission to run this command.')
