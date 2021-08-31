from .converter import Converter
from .errors import BadBoolArgument
from nextcord.ext.abc import ContextBase

class BoolConverter(Converter[bool]):
    """Converts to a :class:`~bool`.

    The following formats are accepted:

    - ``yes``/``no``
    - ``y``/``n``
    - ``true``/``false``
    - ``t``/``f``
    - ``1``/``0``
    - ``enable``/``disable``
    - ``enabled``/``disabled``
    - ``on``/``off``

        - These values are case insensitive.

    .. versionadded:: 2.0
    """

    true = {
        "yes",
        "y",
        "true",
        "1",
        "enable",
        "enabled",
        "on",
    }

    false = {
        "no",
        "n",
        "false",
        "0",
        "disable",
        "disabled",
        "off",
    }

    async def convert(self, ctx: ContextBase, argument: str) -> bool:
        argument = argument.lower()
        if argument in self.true:
            return True
        if argument in self.false:
            return False
        raise BadBoolArgument(argument)