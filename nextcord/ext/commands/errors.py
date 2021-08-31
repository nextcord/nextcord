"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import Optional, Any, TYPE_CHECKING, List, Type, Tuple, Union

from nextcord.errors import ClientException
from nextcord.ext.errors import (
    CommandError,
    UserInputError,
    MissingRole,
    CheckFailure,
    NoPrivateMessage,
    BotMissingRole,
    MissingAnyRole,
    BotMissingAnyRole,
    MissingPermissions,
    BotMissingPermissions,
    NSFWChannelRequired,
    CommandOnCooldown,
    MaxConcurrencyReached,
    NotOwner,
    DisabledCommand,
    CommandInvokeError,
    PrivateMessageOnly,
)
from nextcord.ext.converters.errors import (
    ObjectNotFound,
    MemberNotFound,
    GuildNotFound,
    UserNotFound,
    ChannelNotFound,
    ThreadNotFound,
    ChannelNotReadable,
    BadColourArgument,
    BadColorArgument,
    RoleNotFound,
    BadInviteArgument,
    EmojiNotFound,
    GuildStickerNotFound,
    PartialEmojiConversionFailure,
    BadArgument,
    BadUnionArgument,
    BadLiteralArgument,
    BadBoolArgument,
    ConversionError,
    MessageNotFound,
)
from nextcord.ext.interactions.errors import (
    CheckAnyFailure,
    ExtensionError,
    ExtensionFailed,
    NoEntryPointError,
    ExtensionNotFound,
    ExtensionAlreadyLoaded,
    ExtensionNotLoaded,
)

if TYPE_CHECKING:
    from inspect import Parameter

    from .converter import Converter
    from nextcord.ext.interactions import Cooldown, BucketType
    from .flags import Flag
    from nextcord.abc import GuildChannel
    from nextcord.threads import Thread
    from nextcord.types.snowflake import Snowflake, SnowflakeList


__all__ = (
    'CommandError',
    'MissingRequiredArgument',
    'BadArgument',
    'PrivateMessageOnly',
    'NoPrivateMessage',
    'CheckFailure',
    'CheckAnyFailure',
    'CommandNotFound',
    'DisabledCommand',
    'CommandInvokeError',
    'TooManyArguments',
    'UserInputError',
    'CommandOnCooldown',
    'MaxConcurrencyReached',
    'NotOwner',
    'MessageNotFound',
    'ObjectNotFound',
    'MemberNotFound',
    'GuildNotFound',
    'UserNotFound',
    'ChannelNotFound',
    'ThreadNotFound',
    'ChannelNotReadable',
    'BadColourArgument',
    'BadColorArgument',
    'RoleNotFound',
    'BadInviteArgument',
    'EmojiNotFound',
    'GuildStickerNotFound',
    'PartialEmojiConversionFailure',
    'BadBoolArgument',
    'MissingRole',
    'BotMissingRole',
    'MissingAnyRole',
    'BotMissingAnyRole',
    'MissingPermissions',
    'BotMissingPermissions',
    'NSFWChannelRequired',
    'ConversionError',
    'BadUnionArgument',
    'BadLiteralArgument',
    'ArgumentParsingError',
    'UnexpectedQuoteError',
    'InvalidEndOfQuotedStringError',
    'ExpectedClosingQuoteError',
    'ExtensionError',
    'ExtensionAlreadyLoaded',
    'ExtensionNotLoaded',
    'NoEntryPointError',
    'ExtensionFailed',
    'ExtensionNotFound',
    'CommandRegistrationError',
    'FlagError',
    'BadFlagArgument',
    'MissingFlagArgument',
    'TooManyFlags',
    'MissingRequiredFlag',
)


class CommandNotFound(CommandError):
    """Exception raised when a command is attempted to be invoked
    but no command under that name is found.

    This is not raised for invalid subcommands, rather just the
    initial main command that is attempted to be invoked.

    This inherits from :exc:`CommandError`.
    """
    pass


class MissingRequiredArgument(UserInputError):
    """Exception raised when parsing a command and a parameter
    that is required is not encountered.

    This inherits from :exc:`UserInputError`

    Attributes
    -----------
    param: :class:`inspect.Parameter`
        The argument that is missing.
    """

    def __init__(self, param: Parameter) -> None:
        self.param: Parameter = param
        super().__init__(
            f'{param.name} is a required argument that is missing.')


class TooManyArguments(UserInputError):
    """Exception raised when the command was passed too many arguments and its
    :attr:`.Command.ignore_extra` attribute was not set to ``True``.

    This inherits from :exc:`UserInputError`
    """
    pass


class ArgumentParsingError(UserInputError):
    """An exception raised when the parser fails to parse a user's input.

    This inherits from :exc:`UserInputError`.

    There are child classes that implement more granular parsing errors for
    i18n purposes.
    """
    pass


class UnexpectedQuoteError(ArgumentParsingError):
    """An exception raised when the parser encounters a quote mark inside a non-quoted string.

    This inherits from :exc:`ArgumentParsingError`.

    Attributes
    ------------
    quote: :class:`str`
        The quote mark that was found inside the non-quoted string.
    """

    def __init__(self, quote: str) -> None:
        self.quote: str = quote
        super().__init__(
            f'Unexpected quote mark, {quote!r}, in non-quoted string')


class InvalidEndOfQuotedStringError(ArgumentParsingError):
    """An exception raised when a space is expected after the closing quote in a string
    but a different character is found.

    This inherits from :exc:`ArgumentParsingError`.

    Attributes
    -----------
    char: :class:`str`
        The character found instead of the expected string.
    """

    def __init__(self, char: str) -> None:
        self.char: str = char
        super().__init__(
            f'Expected space after closing quotation but received {char!r}')


class ExpectedClosingQuoteError(ArgumentParsingError):
    """An exception raised when a quote character is expected but not found.

    This inherits from :exc:`ArgumentParsingError`.

    Attributes
    -----------
    close_quote: :class:`str`
        The quote character expected.
    """

    def __init__(self, close_quote: str) -> None:
        self.close_quote: str = close_quote
        super().__init__(f'Expected closing {close_quote}.')


class CommandRegistrationError(ClientException):
    """An exception raised when the command can't be added
    because the name is already taken by a different command.

    This inherits from :exc:`nextcord.ClientException`

    .. versionadded:: 1.4

    Attributes
    ----------
    name: :class:`str`
        The command name that had the error.
    alias_conflict: :class:`bool`
        Whether the name that conflicts is an alias of the command we try to add.
    """

    def __init__(self, name: str, *, alias_conflict: bool = False) -> None:
        self.name: str = name
        self.alias_conflict: bool = alias_conflict
        type_ = 'alias' if alias_conflict else 'command'
        super().__init__(
            f'The {type_} {name} is already an existing command or alias.')


class FlagError(BadArgument):
    """The base exception type for all flag parsing related errors.

    This inherits from :exc:`BadArgument`.

    .. versionadded:: 2.0
    """
    pass


class TooManyFlags(FlagError):
    """An exception raised when a flag has received too many values.

    This inherits from :exc:`FlagError`.

    .. versionadded:: 2.0

    Attributes
    ------------
    flag: :class:`~nextcord.ext.commands.Flag`
        The flag that received too many values.
    values: List[:class:`str`]
        The values that were passed.
    """

    def __init__(self, flag: Flag, values: List[str]) -> None:
        self.flag: Flag = flag
        self.values: List[str] = values
        super().__init__(
            f'Too many flag values, expected {flag.max_args} but received {len(values)}.')


class BadFlagArgument(FlagError):
    """An exception raised when a flag failed to convert a value.

    This inherits from :exc:`FlagError`

    .. versionadded:: 2.0

    Attributes
    -----------
    flag: :class:`~nextcord.ext.commands.Flag`
        The flag that failed to convert.
    """

    def __init__(self, flag: Flag) -> None:
        self.flag: Flag = flag
        try:
            name = flag.annotation.__name__
        except AttributeError:
            name = flag.annotation.__class__.__name__

        super().__init__(
            f'Could not convert to {name!r} for flag {flag.name!r}')


class MissingRequiredFlag(FlagError):
    """An exception raised when a required flag was not given.

    This inherits from :exc:`FlagError`

    .. versionadded:: 2.0

    Attributes
    -----------
    flag: :class:`~nextcord.ext.commands.Flag`
        The required flag that was not found.
    """

    def __init__(self, flag: Flag) -> None:
        self.flag: Flag = flag
        super().__init__(f'Flag {flag.name!r} is required and missing')


class MissingFlagArgument(FlagError):
    """An exception raised when a flag did not get a value.

    This inherits from :exc:`FlagError`

    .. versionadded:: 2.0

    Attributes
    -----------
    flag: :class:`~nextcord.ext.commands.Flag`
        The flag that did not get a value.
    """

    def __init__(self, flag: Flag) -> None:
        self.flag: Flag = flag
        super().__init__(f'Flag {flag.name!r} does not have an argument')
