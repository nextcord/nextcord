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

import inspect
from typing import (
    Any,
    Dict,
    Generic,
    Literal,
    TYPE_CHECKING,
    List,
    Type,
    TypeVar,
    Union,
)

import nextcord
from .errors import (
    CommandError,
    BadArgument,
    NoPrivateMessage,
    MessageNotFound,
    ObjectNotFound,
    MemberNotFound,
    GuildNotFound,
    UserNotFound,
    ChannelNotFound,
    ThreadNotFound,
    ChannelNotReadable,
    BadColourArgument,
    RoleNotFound,
    BadInviteArgument,
    EmojiNotFound,
    GuildStickerNotFound,
    PartialEmojiConversionFailure,
    BadBoolArgument,
    ConversionError,
    BadUnionArgument,
    BadLiteralArgument,
)

from nextcord.ext.converters import (
    BoolConverter,
    CategoryChannelConverter,
    clean_content,
    ColourConverter,
    ColorConverter,
    Converter,
    EmojiConverter,
    GameConverter,
    Greedy,
    GuildChannelConverter,
    GuildConverter,
    GuildStickerConverter,
    IDConverter,
    InviteConverter,
    MemberConverter,
    MessageConverter,
    ObjectConverter,
    PartialEmojiConverter,
    PartialMessageConverter,
    RoleConverter,
    StageChannelConverter,
    StoreChannelConverter,
    TextChannelConverter,
    ThreadConverter,
    UserConverter,
    VoiceChannelConverter,
)

if TYPE_CHECKING:
    from .core import Context


__all__ = (
    'Converter',
    'ObjectConverter',
    'MemberConverter',
    'UserConverter',
    'MessageConverter',
    'PartialMessageConverter',
    'TextChannelConverter',
    'InviteConverter',
    'GuildConverter',
    'RoleConverter',
    'GameConverter',
    'ColourConverter',
    'ColorConverter',
    'VoiceChannelConverter',
    'StageChannelConverter',
    'EmojiConverter',
    'PartialEmojiConverter',
    'CategoryChannelConverter',
    'IDConverter',
    'StoreChannelConverter',
    'ThreadConverter',
    'GuildChannelConverter',
    'GuildStickerConverter',
    'clean_content',
    'Greedy',
    'run_converters',
)


def _convert_to_bool(argument: str) -> bool:
    lowered = argument.lower()
    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False
    else:
        raise BadBoolArgument(lowered)


def get_converter(param: inspect.Parameter) -> Any:
    converter = param.annotation
    if converter is param.empty:
        if param.default is not param.empty:
            converter = str if param.default is None else type(param.default)
        else:
            converter = str
    return converter

T = TypeVar('T')
_GenericAlias = type(List[T])


def is_generic_type(tp: Any, *, _generic_alias: Type = _GenericAlias) -> bool:
    return isinstance(tp, type) and issubclass(tp, Generic) or isinstance(tp, _generic_alias)  # type: ignore


CONVERTER_MAPPING: Dict[Type[Any], Any] = {
    nextcord.Object: ObjectConverter,
    nextcord.Member: MemberConverter,
    nextcord.User: UserConverter,
    nextcord.Message: MessageConverter,
    nextcord.PartialMessage: PartialMessageConverter,
    nextcord.TextChannel: TextChannelConverter,
    nextcord.Invite: InviteConverter,
    nextcord.Guild: GuildConverter,
    nextcord.Role: RoleConverter,
    nextcord.Game: GameConverter,
    nextcord.Colour: ColourConverter,
    nextcord.VoiceChannel: VoiceChannelConverter,
    nextcord.StageChannel: StageChannelConverter,
    nextcord.Emoji: EmojiConverter,
    nextcord.PartialEmoji: PartialEmojiConverter,
    nextcord.CategoryChannel: CategoryChannelConverter,
    nextcord.StoreChannel: StoreChannelConverter,
    nextcord.Thread: ThreadConverter,
    nextcord.abc.GuildChannel: GuildChannelConverter,
    nextcord.GuildSticker: GuildStickerConverter,
    bool: BoolConverter,
}


async def _actual_conversion(ctx: Context, converter, argument: str, param: inspect.Parameter):
    if converter in CONVERTER_MAPPING:
        converter = CONVERTER_MAPPING[converter]

    try:
        if inspect.isclass(converter) and issubclass(converter, Converter):
            if inspect.ismethod(converter.convert):
                return await converter.convert(ctx, argument)
            else:
                return await converter().convert(ctx, argument)
        elif isinstance(converter, Converter):
            return await converter.convert(ctx, argument)
    except CommandError:
        raise
    except Exception as exc:
        raise ConversionError(converter, exc) from exc

    try:
        return converter(argument)
    except CommandError:
        raise
    except Exception as exc:
        try:
            name = converter.__name__
        except AttributeError:
            name = converter.__class__.__name__

        raise BadArgument(f'Converting to "{name}" failed for parameter "{param.name}".') from exc


async def run_converters(ctx: Context, converter, argument: str, param: inspect.Parameter) -> Any:
    """|coro|

    Runs converters for a given converter, argument, and parameter.

    This function does the same work that the library does under the hood.

    .. versionadded:: 2.0

    Parameters
    ------------
    ctx: :class:`Context`
        The invocation context to run the converters under.
    converter: Any
        The converter to run, this corresponds to the annotation in the function.
    argument: :class:`str`
        The argument to convert to.
    param: :class:`inspect.Parameter`
        The parameter being converted. This is mainly for error reporting.

    Raises
    -------
    CommandError
        The converter failed to convert.

    Returns
    --------
    Any
        The resulting conversion.
    """
    origin = getattr(converter, '__origin__', None)

    if origin is Union:
        errors = []
        _NoneType = type(None)
        union_args = converter.__args__
        for conv in union_args:
            # if we got to this part in the code, then the previous conversions have failed
            # so we should just undo the view, return the default, and allow parsing to continue
            # with the other parameters
            if conv is _NoneType and param.kind != param.VAR_POSITIONAL:
                ctx.view.undo()
                return None if param.default is param.empty else param.default

            try:
                value = await run_converters(ctx, conv, argument, param)
            except CommandError as exc:
                errors.append(exc)
            else:
                return value

        # if we're here, then we failed all the converters
        raise BadUnionArgument(param, union_args, errors)

    if origin is Literal:
        errors = []
        conversions: Dict[Type, Any] = {}
        literal_args = converter.__args__
        for literal in literal_args:
            literal_type = type(literal)
            try:
                value = conversions[literal_type]
            except KeyError:
                try:
                    value = await _actual_conversion(ctx, literal_type, argument, param)
                except CommandError as exc:
                    errors.append(exc)
                    conversions[literal_type] = object()
                    continue
                else:
                    conversions[literal_type] = value

            if value == literal:
                return value

        # if we're here, then we failed to match all the literals
        raise BadLiteralArgument(param, literal_args, errors)

    # This must be the last if-clause in the chain of origin checking
    # Nearly every type is a generic type within the typing library
    # So care must be taken to make sure a more specialised origin handle
    # isn't overwritten by the widest if clause
    if origin is not None and is_generic_type(converter):
        converter = origin

    return await _actual_conversion(ctx, converter, argument, param)
