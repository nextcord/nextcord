from .id_converter import IDConverter
from .errors import RoleNotFound
from nextcord.ext.abc import ContextBase
from nextcord.ext.errors import NoPrivateMessage
from nextcord import Role
import nextcord
import re


class RoleConverter(IDConverter[Role]):
    """Converts to a :class:`~Role`.

    All lookups are via the local guild. If in a DM context, the converter raises
    :exc:`.NoPrivateMessage` exception.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name

    .. versionchanged:: 1.5
         Raise :exc:`.RoleNotFound` instead of generic :exc:`.BadArgument`
    """

    async def convert(self, ctx: ContextBase, argument: str) -> Role:
        if not ctx.guild:
            raise NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(r'<@&([0-9]{15,20})>$', argument)
        if match:
            result = ctx.guild.get_role(int(match.group(1)))
        else:
            result = nextcord.utils.get(ctx.guild._roles.values(), name=argument)

        if result is None:
            raise RoleNotFound(argument)
        return result

    async def convert_from_id(self, ctx: ContextBase, id: int) -> Role:
        if not ctx.guild:
            raise NoPrivateMessage()
        if result := ctx.guild.get_role(id):
            return result
        raise RoleNotFound(str(id))