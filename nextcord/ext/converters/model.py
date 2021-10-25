import inspect
import typing
import importlib

import nextcord
from nextcord.ext.commands import converter, Context
from .converter import CustomConverter


BASE_CONVERTERS = {
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
}


class ConverterDict(dict):
    def __init__(self):
        super().__init__(BASE_CONVERTERS)
    
    def __setitem__(self, k: typing.Any, v: typing.Any):
        if not (issubclass(v, converter.Converter) or inspect.isbuiltin(v)):
            raise TypeError("Excepted value of type 'Converter' or built-in, received {}".format(v.__name__))
        super().__setitem__(k, v)
    
    def set(self, _type: typing.Any, converter: str) -> 'ConverterDict':
        self.__setitem__(_type, converter)
        return self
    
    def get(self, _type: typing.Any, default: typing.Any = None) -> 'ConverterDict':
        if inspect.isclass(_type):
            return super().get(_type, default)
        else:
            _converter = super().get(type(_type), default)

            if issubclass(_converter, CustomConverter):
                _converter = _converter[_type]
            
            return _converter
    
    def register(self, _type: type) -> converter.Converter:
        def predicate(handler: typing.Union[typing.Callable[[Context, str], typing.Awaitable[typing.Any]], converter.Converter]):
            # _type is what is should convert to.

            _converter = handler

            if inspect.iscoroutinefunction(handler):
                _converter = type(
                        '{}Converter'.format(_type.__name__),
                        (converter.Converter,),
                        {
                            'convert': lambda s, c, a: handler(c, a) # should mean it's a coroutine.
                        }
                    )
                
                self.set(_type, _converter)
            else:
                self.set(_type, _converter)
            
            return _converter
        return predicate

    def load(self, *_converters: str) -> None:
        for c in _converters:
            importlib.import_module('nextcord.ext.converters.custom_converters.{}'.format(c)).setup(self)
