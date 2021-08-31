
from .id_converter import IDConverter
from .guild_channel_converter import GuildChannelConverter
from nextcord.ext.abc import ContextBase
from nextcord import Thread

class ThreadConverter(IDConverter[Thread]):
    """Coverts to a :class:`~nextcord.Thread`.

    All lookups are via the local guild.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name.

    .. versionadded: 2.0
    """

    async def convert(self, ctx: ContextBase, argument: str) -> Thread:
        return GuildChannelConverter.resolve_thread(ctx, argument, 'threads', Thread)

    async def convert_from_id(self, ctx: ContextBase, id: int) -> Thread:
        return GuildChannelConverter.resolve_thread_from_id(ctx, id, Thread)