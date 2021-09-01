from nextcord.state import ConnectionState
from .id_converter import IDConverter
from .errors import UserNotFound
from nextcord.ext.abc import ContextBase
from nextcord.ext import commands
import nextcord
import re


class UserConverter(IDConverter[nextcord.User]):
    """Converts to a :class:`~nextcord.User`.

    All lookups are via the global user cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name#discrim
    4. Lookup by name

    .. versionchanged:: 1.5
         Raise :exc:`.UserNotFound` instead of generic :exc:`.BadArgument`

    .. versionchanged:: 1.6
        This converter now lazily fetches users from the HTTP APIs if an ID is passed
        and it's not available in cache.
    """

    async def convert(self, ctx: ContextBase, argument: str) -> nextcord.User:
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]{15,20})>$', argument)
        if match is not None:
            user_id = int(match.group(1))
            return await self.convert_from_id(ctx, user_id)
        if isinstance(ctx, commands.Context):
            return self._convert_from_str(ctx._state, argument)
        raise UserNotFound(argument)

    def _convert_from_str(self, state: ConnectionState, arg: str) -> nextcord.User:
        # Remove the '@' character if this is the first character from the argument
        if arg[0] == '@':
            arg = arg[1:]

        # check for discriminator if it exists,
        if len(arg) > 5 and arg[-5] == '#':
            discrim = arg[-4:]
            name = arg[:-5]
            predicate = lambda u: u.name == name and u.discriminator == discrim
            result = nextcord.utils.find(predicate, state._users.values())
            if result is not None:
                return result

        predicate = lambda u: u.name == arg
        result = nextcord.utils.find(predicate, state._users.values())
        if result is not None:
            return result

        raise UserNotFound(arg)


    async def convert_from_id(self, ctx: ContextBase, id: int) -> nextcord.User:
        result = ctx.bot.get_user(id) or (
            nextcord.utils.get(ctx.message.mentions, id=id)
            if isinstance (ctx, commands.Context) else None
        )
        if result is None:
            try:
                result = await ctx.bot.fetch_user(id)
            except nextcord.HTTPException:
                raise UserNotFound(str(id)) from None
        return result