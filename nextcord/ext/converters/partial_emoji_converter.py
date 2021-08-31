from .converter import Converter
from .errors import PartialEmojiConversionFailure
from nextcord.ext.abc import ContextBase
from nextcord import PartialEmoji
import re


class PartialEmojiConverter(Converter[PartialEmoji]):
    """Converts to a :class:`~PartialEmoji`.

    This is done by extracting the animated flag, name and ID from the emoji.

    .. versionchanged:: 1.5
         Raise :exc:`.PartialEmojiConversionFailure` instead of generic :exc:`.BadArgument`
    """

    async def convert(self, ctx: ContextBase, argument: str) -> PartialEmoji:
        match = re.match(r'<(a?):([a-zA-Z0-9\_]{1,32}):([0-9]{15,20})>$', argument)

        if match:
            emoji_animated = bool(match.group(1))
            emoji_name = match.group(2)
            emoji_id = int(match.group(3))

            return PartialEmoji.with_state(
                ctx.bot._connection, animated=emoji_animated, name=emoji_name, id=emoji_id
            )

        raise PartialEmojiConversionFailure(argument)