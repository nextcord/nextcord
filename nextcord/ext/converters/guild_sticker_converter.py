from .id_converter import IDConverter
from .errors import GuildStickerNotFound
from nextcord.ext.abc import ContextBase
from nextcord import GuildSticker
import nextcord


class GuildStickerConverter(IDConverter[GuildSticker]):
    """Converts to a :class:`~GuildSticker`.

    All lookups are done for the local guild first, if available. If that lookup
    fails, then it checks the client's global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    3. Lookup by name

    .. versionadded:: 2.0
    """

    async def convert(self, ctx: ContextBase, argument: str) -> GuildSticker:
        match = self._get_id_match(argument)
        result = None
        bot = ctx.bot
        guild = ctx.guild

        if match is None:
            # Try to get the sticker by name. Try local guild first.
            if guild:
                result = nextcord.utils.get(guild.stickers, name=argument)

            if result is None:
                result = nextcord.utils.get(bot.stickers, name=argument)
        else:
            sticker_id = int(match.group(1))

            # Try to look up sticker by id.
            result = bot.get_sticker(sticker_id)

        if result is None:
            raise GuildStickerNotFound(argument)

        return result

    async def convert_from_id(self, ctx: ContextBase, id: int) -> GuildSticker:
        if result := ctx.bot.get_sticker(id):
            return result
        raise GuildStickerNotFound(str(id))