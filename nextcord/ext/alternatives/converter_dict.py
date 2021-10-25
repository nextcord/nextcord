"""An experiment that allows you to register converters for classes,
as a helpful aid for readability when using typehints for custom converters.

You could also override base converters if you wanted to.

Example:
```py
class YertConverter(commands.Converter):
    async def convert(self, ctx, arg):
        return 'yert'

class Yert(object):
    ...

bot.converters[Yert] = YertConverter

@bot.command()
async def yert(ctx, yert: Yert):
    '''This will always send `yert`!'''
    await ctx.send(yert)
```
"""
from types import FunctionType

import nextcord
from nextcord.ext import commands
from nextcord.ext.commands import converter, Command

from ._common import _ALL

_BUILTINS = (
    bool,
    str,
    int,
    float,
)

_CONVERTERS = {
    # fmt: off
    nextcord.CategoryChannel: converter.CategoryChannelConverter,
    nextcord.Colour:          converter.ColourConverter,
    nextcord.Emoji:           converter.EmojiConverter,
    nextcord.Game:            converter.GameConverter,
    nextcord.Invite:          converter.InviteConverter,
    nextcord.Member:          converter.MemberConverter,
    nextcord.Message:         converter.MessageConverter,
    nextcord.PartialEmoji:    converter.PartialEmojiConverter,
    nextcord.Role:            converter.RoleConverter,
    nextcord.TextChannel:     converter.TextChannelConverter,
    nextcord.User:            converter.UserConverter,
    nextcord.VoiceChannel:    converter.VoiceChannelConverter,
    # fmt: on
}

_CONVERTERS.update({b: b for b in _BUILTINS})


class _ConverterDict(dict):
    """An easy way to register converters for classes.

    Can help for both linting and readability.
    """

    def __init__(self):
        super().__init__(_CONVERTERS)
        super().update(_ALL)

    def __setitem__(self, k, v):
        if not (isinstance(v, FunctionType) or issubclass(v, (*_BUILTINS, converter.Converter))):
            raise TypeError(
                "Excepted value of type 'Converter' or built-in, received %r" % v.__name__
            )
        super().__setitem__(k, v)

    def set(self, k, v):
        """Same as doing ``ConverterDict[Obj] = ObjConverter`` but fluid."""
        self.__setitem__(k, v)
        return self


_GLOBAL_CONVERTER_DICT = _ConverterDict()

commands.bot.BotBase.converters = _GLOBAL_CONVERTER_DICT

_old_actual_conversion = Command._actual_conversion


async def _actual_conversion(self, ctx, converter, argument, param):
    converter = _GLOBAL_CONVERTER_DICT.get(converter, converter)
    return await _old_actual_conversion(self, ctx, converter, argument, param)


Command._actual_conversion = _actual_conversion
