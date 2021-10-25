from nextcord.ext import commands
from nextcord.ext.converters import converter


class InRangeConverter(converter.CustomConverter):
    _value: range

    async def convert(self, ctx, argument: str) -> int:
        try:
            argument = int(argument)
        except ValueError:
            raise commands.BadArgument("{0} is not int".format(argument))

        if argument in self._value:
            return argument
        raise commands.BadArgument("{0} not in range".format(argument))

def setup(converters):
    converters.set(range, InRangeConverter)
