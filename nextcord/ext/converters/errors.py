from inspect import Parameter
from nextcord import Thread
from nextcord.abc import GuildChannel
from typing import Any, List, Tuple, Type, Union
from nextcord.ext.errors import CommandError, BadArgument, UserInputError
from .converter import Converter


class ObjectNotFound(BadArgument[str]):
    """Exception raised when the argument provided did not match the format
    of an ID or a mention.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 2.0

    Attributes
    -----------
    argument: :class:`str`
        The argument supplied by the caller that was not matched
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'{argument!r} does not follow a valid ID or mention format.', argument)


class MemberNotFound(BadArgument[str]):
    """Exception raised when the member provided was not found in the bot's
    cache.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5

    Attributes
    -----------
    argument: :class:`str`
        The member supplied by the caller that was not found
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Member "{argument}" not found.', argument)


class UserNotFound(BadArgument[str]):
    """Exception raised when the user provided was not found in the bot's
    cache.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5

    Attributes
    -----------
    argument: :class:`str`
        The user supplied by the caller that was not found
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'User "{argument}" not found.', argument)


class MessageNotFound(BadArgument[str]):
    """Exception raised when the message provided was not found in the channel.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5

    Attributes
    -----------
    argument: :class:`str`
        The message supplied by the caller that was not found
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Message "{argument}" not found.', argument)


class ChannelNotFound(BadArgument[str]):
    """Exception raised when the bot can not find the channel.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5

    Attributes
    -----------
    argument: :class:`str`
        The channel supplied by the caller that was not found
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Channel "{argument}" not found.', argument)


class ChannelNotReadable(BadArgument[Union[GuildChannel, Thread]]):
    """Exception raised when the bot does not have permission to read messages
    in the channel.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5

    Attributes
    -----------
    argument: Union[:class:`.abc.GuildChannel`, :class:`.Thread`]
        The channel supplied by the caller that was not readable
    """

    def __init__(self, argument: Union[GuildChannel, Thread]) -> None:
        super().__init__(f"Can't read messages in {argument.mention}.", argument)


class ThreadNotFound(BadArgument[str]):
    """Exception raised when the bot can not find the thread.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 2.0

    Attributes
    -----------
    argument: :class:`str`
        The thread supplied by the caller that was not found
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Thread "{argument}" not found.', argument)


class BadColourArgument(BadArgument[str]):
    """Exception raised when the colour is not valid.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5

    Attributes
    -----------
    argument: :class:`str`
        The colour supplied by the caller that was not valid
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Colour "{argument}" is invalid.', argument)


BadColorArgument = BadColourArgument


class RoleNotFound(BadArgument[str]):
    """Exception raised when the bot can not find the role.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5

    Attributes
    -----------
    argument: :class:`str`
        The role supplied by the caller that was not found
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Role "{argument}" not found.', argument)


class BadInviteArgument(BadArgument[str]):
    """Exception raised when the invite is invalid or expired.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Invite "{argument}" is invalid or expired.', argument)


class GuildNotFound(BadArgument[str]):
    """Exception raised when the guild provided was not found in the bot's cache.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.7

    Attributes
    -----------
    argument: :class:`str`
        The guild supplied by the called that was not found
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Guild "{argument}" not found.', argument)


class EmojiNotFound(BadArgument[str]):
    """Exception raised when the bot can not find the emoji.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5

    Attributes
    -----------
    argument: :class:`str`
        The emoji supplied by the caller that was not found
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Emoji "{argument}" not found.', argument)


class PartialEmojiConversionFailure(BadArgument[str]):
    """Exception raised when the emoji provided does not match the correct
    format.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5

    Attributes
    -----------
    argument: :class:`str`
        The emoji supplied by the caller that did not match the regex
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Couldn\'t convert "{argument}" to PartialEmoji.', argument)


class GuildStickerNotFound(BadArgument[str]):
    """Exception raised when the bot can not find the sticker.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 2.0

    Attributes
    -----------
    argument: :class:`str`
        The sticker supplied by the caller that was not found
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'Sticker "{argument}" not found.', argument)


class BadBoolArgument(BadArgument[str]):
    """Exception raised when a boolean argument was not convertable.

    This inherits from :exc:`BadArgument`

    .. versionadded:: 1.5

    Attributes
    -----------
    argument: :class:`str`
        The boolean argument supplied by the caller that is not in the predefined list
    """

    def __init__(self, argument: str) -> None:
        super().__init__(f'{argument} is not a recognised boolean option', argument)


class ConversionError(CommandError):
    """Exception raised when a Converter class raises non-CommandError.

    This inherits from :exc:`CommandError`.

    Attributes
    ----------
    converter: :class:`nextcord.ext.commands.Converter`
        The converter that failed.
    original: :exc:`Exception`
        The original exception that was raised. You can also get this via
        the ``__cause__`` attribute.
    """

    def __init__(self, converter: Converter, original: Exception) -> None:
        self.converter: Converter = converter
        self.original: Exception = original


class BadUnionArgument(UserInputError):
    """Exception raised when a :data:`typing.Union` converter fails for all
    its associated types.

    This inherits from :exc:`UserInputError`

    Attributes
    -----------
    param: :class:`inspect.Parameter`
        The parameter that failed being converted.
    converters: Tuple[Type, ``...``]
        A tuple of converters attempted in conversion, in order of failure.
    errors: List[:class:`CommandError`]
        A list of errors that were caught from failing the conversion.
    """

    def __init__(self, param: Parameter, converters: Tuple[Type, ...], errors: List[CommandError]) -> None:
        self.param: Parameter = param
        self.converters: Tuple[Type, ...] = converters
        self.errors: List[CommandError] = errors

        def _get_name(x):
            try:
                return x.__name__
            except AttributeError:
                if hasattr(x, '__origin__'):
                    return repr(x)
                return x.__class__.__name__

        to_string = [_get_name(x) for x in converters]
        if len(to_string) > 2:
            fmt = '{}, or {}'.format(', '.join(to_string[:-1]), to_string[-1])
        else:
            fmt = ' or '.join(to_string)

        super().__init__(f'Could not convert "{param.name}" into {fmt}.')


class BadLiteralArgument(UserInputError):
    """Exception raised when a :data:`typing.Literal` converter fails for all
    its associated values.

    This inherits from :exc:`UserInputError`

    .. versionadded:: 2.0

    Attributes
    -----------
    param: :class:`inspect.Parameter`
        The parameter that failed being converted.
    literals: Tuple[Any, ``...``]
        A tuple of values compared against in conversion, in order of failure.
    errors: List[:class:`CommandError`]
        A list of errors that were caught from failing the conversion.
    """

    def __init__(self, param: Parameter, literals: Tuple[Any, ...], errors: List[CommandError]) -> None:
        self.param: Parameter = param
        self.literals: Tuple[Any, ...] = literals
        self.errors: List[CommandError] = errors

        to_string = [repr(l) for l in literals]
        if len(to_string) > 2:
            fmt = '{}, or {}'.format(', '.join(to_string[:-1]), to_string[-1])
        else:
            fmt = ' or '.join(to_string)

        super().__init__(
            f'Could not convert "{param.name}" into the literal {fmt}.')