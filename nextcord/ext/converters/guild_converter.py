from .id_converter import IDConverter
from .errors import GuildNotFound
from nextcord.ext.abc import ContextBase
from nextcord import Guild
import nextcord


class GuildConverter(IDConverter[Guild]):
    """Converts to a :class:`~Guild`.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by name. (There is no disambiguation for Guilds with multiple matching names).

    .. versionadded:: 1.7
    """

    async def convert(self, ctx: ContextBase, argument: str) -> Guild:
        match = self._get_id_match(argument)
        result = None

        if match is not None:
            guild_id = int(match.group(1))
            result = ctx.bot.get_guild(guild_id)

        if result is None:
            result = nextcord.utils.get(ctx.bot.guilds, name=argument)

            if result is None:
                raise GuildNotFound(argument)
        return result

    async def convert_from_id(self, ctx: ContextBase, id: int) -> Guild:
        if result := ctx.bot.get_guild(id):
            return result
        raise GuildNotFound(str(id))