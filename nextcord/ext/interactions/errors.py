from typing import Any, Callable, List, Optional
from nextcord.errors import DiscordException
from nextcord.ext.errors import CommandError, CheckFailure
from nextcord.ext.abc import ContextBase

__all__ = (
    "CommandError",
    "CheckFailure",
    "CheckAnyFailure",
)


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

    def __init__(self, errors: List[CheckFailure], checks: List[Callable[[ContextBase], bool]]) -> None:
        self.errors: List[CheckFailure] = errors
        self.checks: List[Callable[[ContextBase], bool]] = checks
        super().__init__('You do not have permission to run this command.')



class ExtensionError(DiscordException):
    """Base exception for extension related errors.

    This inherits from :exc:`~nextcord.DiscordException`.

    Attributes
    ------------
    name: :class:`str`
        The extension that had an error.
    """

    def __init__(self, message: Optional[str] = None, *args: Any, name: str) -> None:
        self.name: str = name
        message = message or f'Extension {name!r} had an error.'
        # clean-up @everyone and @here mentions
        m = message.replace(
            '@everyone', '@\u200beveryone').replace('@here', '@\u200bhere')
        super().__init__(m, *args)


class NoEntryPointError(ExtensionError):
    """An exception raised when an extension does not have a ``setup`` entry point function.

    This inherits from :exc:`ExtensionError`
    """

    def __init__(self, name: str) -> None:
        super().__init__(
            f"Extension {name!r} has no 'setup' function.", name=name)



class ExtensionFailed(ExtensionError):
    """An exception raised when an extension failed to load during execution of the module or ``setup`` entry point.

    This inherits from :exc:`ExtensionError`

    Attributes
    -----------
    name: :class:`str`
        The extension that had the error.
    original: :exc:`Exception`
        The original exception that was raised. You can also get this via
        the ``__cause__`` attribute.
    """

    def __init__(self, name: str, original: Exception) -> None:
        self.original: Exception = original
        msg = f'Extension {name!r} raised an error: {original.__class__.__name__}: {original}'
        super().__init__(msg, name=name)


class ExtensionNotFound(ExtensionError):
    """An exception raised when an extension is not found.

    This inherits from :exc:`ExtensionError`

    .. versionchanged:: 1.3
        Made the ``original`` attribute always None.

    Attributes
    -----------
    name: :class:`str`
        The extension that had the error.
    """

    def __init__(self, name: str) -> None:
        msg = f'Extension {name!r} could not be loaded.'
        super().__init__(msg, name=name)


class ExtensionAlreadyLoaded(ExtensionError):
    """An exception raised when an extension has already been loaded.

    This inherits from :exc:`ExtensionError`
    """

    def __init__(self, name: str) -> None:
        super().__init__(f'Extension {name!r} is already loaded.', name=name)


class ExtensionNotLoaded(ExtensionError):
    """An exception raised when an extension was not loaded.

    This inherits from :exc:`ExtensionError`
    """

    def __init__(self, name: str) -> None:
        super().__init__(f'Extension {name!r} has not been loaded.', name=name)