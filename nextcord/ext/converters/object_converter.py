import re
from .id_converter import IDConverter
import nextcord
from nextcord.ext.abc import ContextBase
from .errors import ObjectNotFound

class ObjectConverter(IDConverter[nextcord.Object]):
    """Converts to a :class:`~nextcord.Object`.

    The argument must follow the valid ID or mention formats (e.g. `<@80088516616269824>`).

    .. versionadded:: 2.0

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by member, role, or channel mention.
    """

    async def convert(self, ctx: ContextBase, argument: str) -> nextcord.Object:
        match = self._get_id_match(argument) or re.match(r'<(?:@(?:!|&)?|#)([0-9]{15,20})>$', argument)

        if match is None:
            raise ObjectNotFound(argument)

        object_id = int(match.group(1))

        return await self.convert_from_id(ctx, object_id)

    async def convert_from_id(self, ctx: ContextBase, id: int) -> nextcord.Object:
        return nextcord.Object(id=id)