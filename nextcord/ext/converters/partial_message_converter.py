from nextcord.ext.abc.context_base import ContextBase
from .id_converter import IDConverter
from .errors import MessageNotFound, ChannelNotFound
from nextcord.abc import MessageableChannel
from typing import Optional
import nextcord
import re


class PartialMessageConverter(IDConverter[nextcord.PartialMessage]):
    """Converts to a :class:`nextcord.PartialMessage`.

    .. versionadded:: 1.7

    The creation strategy is as follows (in order):

    1. By "{channel ID}-{message ID}" (retrieved by shift-clicking on "Copy ID")
    2. By message ID (The message is assumed to be in the context channel.)
    3. By message URL
    """

    @staticmethod
    def _get_id_matches(ctx, argument):
        id_regex = re.compile(r'(?:(?P<channel_id>[0-9]{15,20})-)?(?P<message_id>[0-9]{15,20})$')
        link_regex = re.compile(
            r'https?://(?:(ptb|canary|www)\.)?discord(?:app)?\.com/channels/'
            r'(?P<guild_id>[0-9]{15,20}|@me)'
            r'/(?P<channel_id>[0-9]{15,20})/(?P<message_id>[0-9]{15,20})/?$'
        )
        match = id_regex.match(argument) or link_regex.match(argument)
        if not match:
            raise MessageNotFound(argument)
        data = match.groupdict()
        channel_id = nextcord.utils._get_as_snowflake(data, 'channel_id')
        message_id = int(data['message_id'])
        guild_id = data.get('guild_id')
        if guild_id is None:
            guild_id = ctx.guild and ctx.guild.id
        elif guild_id == '@me':
            guild_id = None
        else:
            guild_id = int(guild_id)
        return guild_id, message_id, channel_id

    @staticmethod
    def _resolve_channel(ctx, guild_id, channel_id) -> Optional[MessageableChannel]:
        if guild_id is not None:
            guild = ctx.bot.get_guild(guild_id)
            if guild is not None and channel_id is not None:
                return guild._resolve_channel(channel_id)
            else:
                return None
        else:
            return ctx.bot.get_channel(channel_id) if channel_id else ctx.channel

    async def convert(self, ctx: ContextBase, argument: str) -> nextcord.PartialMessage:
        guild_id, message_id, channel_id = self._get_id_matches(ctx, argument)
        channel = self._resolve_channel(ctx, guild_id, channel_id)
        if not channel:
            raise ChannelNotFound(channel_id)
        return nextcord.PartialMessage(channel=channel, id=message_id)

    async def convert_from_id(self, ctx: ContextBase, id: int) -> nextcord.PartialMessage:
        return nextcord.PartialMessage(channel=ctx.channel, id=id)