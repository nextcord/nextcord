import re
from typing import Optional
from nextcord.ext.abc.context_base import ContextBase
from .id_converter import IDConverter
from .utils import get_from_guilds
from .errors import MemberNotFound
import nextcord


class MemberConverter(IDConverter[nextcord.Member]):
    """Converts to a :class:`~nextcord.Member`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name#discrim
    4. Lookup by name
    5. Lookup by nickname

    .. versionchanged:: 1.5
         Raise :exc:`.MemberNotFound` instead of generic :exc:`.BadArgument`

    .. versionchanged:: 1.5.1
        This converter now lazily fetches members from the gateway and HTTP APIs,
        optionally caching the result if :attr:`.MemberCacheFlags.joined` is enabled.
    """

    async def query_member_named(self, guild, argument):
        cache = guild._state.member_cache_flags.joined
        if len(argument) > 5 and argument[-5] == '#':
            username, _, discriminator = argument.rpartition('#')
            members = await guild.query_members(username, limit=100, cache=cache)
            return nextcord.utils.get(members, name=username, discriminator=discriminator)
        else:
            members = await guild.query_members(argument, limit=100, cache=cache)
            return nextcord.utils.find(lambda m: m.name == argument or m.nick == argument, members)

    async def query_member_by_id(self, bot, guild, user_id):
        ws = bot._get_websocket(shard_id=guild.shard_id)
        cache = guild._state.member_cache_flags.joined
        if ws.is_ratelimited():
            # If we're being rate limited on the WS, then fall back to using the HTTP API
            # So we don't have to wait ~60 seconds for the query to finish
            try:
                member = await guild.fetch_member(user_id)
            except nextcord.HTTPException:
                return None

            if cache:
                guild._add_member(member)
            return member

        # If we're not being rate limited then we can use the websocket to actually query
        members = await guild.query_members(limit=1, user_ids=[user_id], cache=cache)
        if not members:
            return None
        return members[0]

    async def convert(self, ctx: ContextBase, argument: str) -> nextcord.Member:
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]{15,20})>$', argument)
        guild = ctx.guild
        result = None
        user_id = None
        if match is None:
            # not a mention...
            if guild:
                result = guild.get_member_named(argument)
            else:
                result = get_from_guilds(bot, 'get_member_named', argument)
        else:
            user_id = int(match.group(1))
            return await self.convert_from_id(ctx, user_id)

        if result is None:
            if guild is None:
                raise MemberNotFound(argument)

            result = await self.query_member_named(guild, argument)

            if not result:
                raise MemberNotFound(argument)

        return result

    async def convert_from_id(self, ctx: ContextBase, id: int) -> nextcord.Member:
        result: Optional[nextcord.Member] = None
        result = (
            ctx.guild.get_member(id) or nextcord.utils.get(ctx.message.mentions, id=id) # type: ignore
            if ctx.guild
            else get_from_guilds(ctx.bot, 'get_member', id)
        )

        if result:
            return result

        result = await self.query_member_by_id(ctx.bot, ctx.guild, id)

        if result:
            return result

        raise MemberNotFound(str(id))