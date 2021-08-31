from .id_converter import IDConverter
from .errors import EmojiNotFound
from nextcord import Emoji
from nextcord.ext.abc import ContextBase
import re
import nextcord


class EmojiConverter(IDConverter[Emoji]):
    """Converts to a :class:`~Emoji`.

    All lookups are done for the local guild first, if available. If that lookup
    fails, then it checks the client's global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by extracting ID from the emoji.
    3. Lookup by name

    .. versionchanged:: 1.5
         Raise :exc:`.EmojiNotFound` instead of generic :exc:`.BadArgument`
    """

    async def convert(self, ctx: ContextBase, argument: str) -> Emoji:
        match = self._get_id_match(argument) or re.match(r'<a?:[a-zA-Z0-9\_]{1,32}:([0-9]{15,20})>$', argument)
        result = None
        bot = ctx.bot
        guild = ctx.guild

        if match is None:
            # Try to get the emoji by name. Try local guild first.
            if guild:
                result = nextcord.utils.get(guild.emojis, name=argument)

            if result is None:
                result = nextcord.utils.get(bot.emojis, name=argument)
        else:
            emoji_id = int(match.group(1))

            # Try to look up emoji by id.
            result = bot.get_emoji(emoji_id)

        if result is None:
            raise EmojiNotFound(argument)

        return result

    async def convert_from_id(self, ctx: ContextBase, id: int) -> Emoji:
        if result := ctx.bot.get_emoji(id):
            return result
        raise EmojiNotFound(str(id))
