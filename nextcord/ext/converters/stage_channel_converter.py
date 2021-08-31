from .id_converter import IDConverter
from .guild_channel_converter import GuildChannelConverter
from nextcord.ext.abc import ContextBase
from nextcord import StageChannel


class StageChannelConverter(IDConverter[StageChannel]):
    """Converts to a :class:`~StageChannel`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name

    .. versionchanged:: 1.5
         Raise :exc:`.ChannelNotFound` instead of generic :exc:`.BadArgument`
    """

    async def convert(self, ctx: ContextBase, argument: str) -> StageChannel:
        return GuildChannelConverter.resolve_channel(ctx, argument, 'stage_channels', StageChannel)

    async def convert_from_id(self, ctx: ContextBase, id: int) -> StageChannel:
        return GuildChannelConverter.resolve_channel_from_id(ctx, id, StageChannel)