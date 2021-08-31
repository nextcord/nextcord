from .id_converter import IDConverter
from .partial_message_converter import PartialMessageConverter
from .errors import ChannelNotFound, MessageNotFound, ChannelNotReadable
from nextcord.ext.abc import ContextBase
import nextcord

class MessageConverter(IDConverter[nextcord.Message]):
    """Converts to a :class:`nextcord.Message`.

    .. versionadded:: 1.1

    The lookup strategy is as follows (in order):

    1. Lookup by "{channel ID}-{message ID}" (retrieved by shift-clicking on "Copy ID")
    2. Lookup by message ID (the message **must** be in the context channel)
    3. Lookup by message URL

    .. versionchanged:: 1.5
         Raise :exc:`.ChannelNotFound`, :exc:`.MessageNotFound` or :exc:`.ChannelNotReadable` instead of generic :exc:`.BadArgument`
    """

    async def convert(self, ctx: ContextBase, argument: str) -> nextcord.Message:
        guild_id, message_id, channel_id = PartialMessageConverter._get_id_matches(ctx, argument)

        try:
            return await self.convert_from_id(ctx, message_id)
        except MessageNotFound:
            pass

        channel = PartialMessageConverter._resolve_channel(ctx, guild_id, channel_id)
        if not channel:
            raise ChannelNotFound(channel_id)
        try:
            return await channel.fetch_message(message_id)
        except nextcord.NotFound:
            raise MessageNotFound(argument)
        except nextcord.Forbidden:
            raise ChannelNotReadable(channel) # type: ignore

    async def convert_from_id(self, ctx: ContextBase, id: int) -> nextcord.Message:
        if message := ctx.bot._connection._get_message(id):
            return message
        raise MessageNotFound(str(id))