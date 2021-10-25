import typing
from nextcord.ext import commands
import copy

class CustomConveterMeta(type):
    def __getitem__(cls, value: typing.Any) -> 'CustomConverter':
        klass = copy.deepcopy(cls)
        klass._value = value
        return klass

class CustomConverter(commands.Converter, metaclass=CustomConveterMeta):
    _value: typing.Any
