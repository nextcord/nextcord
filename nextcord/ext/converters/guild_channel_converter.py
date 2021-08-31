from nextcord.abc import GuildChannel
from typing import Iterable, Optional, Type
from .id_converter import IDConverter
from ._types import ChannelT, ThreadT
from .utils import get_from_guilds
from .errors import ChannelNotFound, ThreadNotFound
from nextcord.ext.abc import ContextBase
import nextcord
import re


class GuildChannelConverter(IDConverter[GuildChannel]):
    """Converts to a :class:`~GuildChannel`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name.

    .. versionadded:: 2.0
    """

    async def convert(self, ctx: ContextBase, argument: str) -> GuildChannel:
        return self.resolve_channel(ctx, argument, 'channels', GuildChannel)

    async def convert_from_id(self, ctx: ContextBase, id: int) -> GuildChannel:
        return self.resolve_channel_from_id(ctx, id, GuildChannel)

    @staticmethod
    def resolve_channel(ctx: ContextBase, argument: str, attribute: str, type: Type[ChannelT]) -> ChannelT:
        bot = ctx.bot

        match = IDConverter._get_id_match(argument) or re.match(r'<#([0-9]{15,20})>$', argument)
        result: Optional[GuildChannel] = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                iterable: Iterable[ChannelT] = getattr(guild, attribute)
                result = nextcord.utils.get(iterable, name=argument)
            else:
                def check(c):
                    return isinstance(c, type) and c.name == argument

                result = nextcord.utils.find(check, bot.get_all_channels())

            if not isinstance(result, type):
                raise ChannelNotFound(argument)

        else:
            channel_id = int(match.group(1))
            result = GuildChannelConverter.resolve_channel_from_id(ctx, channel_id, type)

        return result

    @staticmethod
    def resolve_thread(ctx: ContextBase, argument: str, attribute: str, type: Type[ThreadT]) -> ThreadT:
        match = IDConverter._get_id_match(argument) or re.match(r'<#([0-9]{15,20})>$', argument)
        result: Optional[nextcord.Thread] = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                iterable: Iterable[ThreadT] = getattr(guild, attribute)
                result = nextcord.utils.get(iterable, name=argument)
        else:
            thread_id = int(match.group(1))
            if guild:
                result = guild.get_thread(thread_id)

        if not result or not isinstance(result, type):
            raise ThreadNotFound(argument)

        return result

    @staticmethod
    def resolve_channel_from_id(ctx: ContextBase, id: int, type: Type[ChannelT]) -> ChannelT:
        if ctx.guild:
            result = ctx.guild.get_channel(id)
        else:
            result = get_from_guilds(ctx.bot, 'get_channel', id)
        if not result or not isinstance(result, type):
            raise ChannelNotFound(str(id))
        return result

    @staticmethod
    def resolve_thread_from_id(ctx: ContextBase, id: int, type: Type[ThreadT]) -> ThreadT:
        if ctx.guild and (thread := ctx.guild.get_thread(id)) and isinstance(thread, type):
            return thread
        raise ThreadNotFound(str(id))
