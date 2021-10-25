from typing import Literal, get_args, get_origin
from nextcord.ext.commands import Command
from nextcord.ext.commands.errors import ConversionError, BadArgument

_old_actual_conversion = Command._actual_conversion


async def _actual_conversion(self, ctx, converter, argument, param):
    origin = get_origin(converter)

    if origin is Literal:
        items = get_args(converter)

        if all(i for i in items if isinstance(i, str)):
            if argument in items:
                return argument

            raise BadArgument(f"Expected literal: one of {list(map(repr, items))}")
        elif all(i for i in items if not isinstance(i, str)):
            ret = await _old_actual_conversion(self, ctx, type(items[0]), argument, param)
            return ret in items
        else:
            raise ConversionError("Literal contains multiple conflicting types.")

    return await _old_actual_conversion(self, ctx, converter, argument, param)


Command._actual_conversion = _actual_conversion
