import re
from typing import Optional

from nextcord.ext import commands
from nextcord.ext.converters import converter


class MatchConverter(converter.CustomConverter):
    _value: re.Pattern

    async def convert(self, ctx, argument: str) -> re.Match:
        match: Optional[re.Match] = self._value.fullmatch(argument)
        if match is None:
            raise commands.BadArgument(
                "{0} does not match the provided pattern".format(argument)
            )
        return match

def setup(converters):
    converters.set(re.Pattern, MatchConverter)
