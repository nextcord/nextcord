from .converter import Converter
from .errors import BadInviteArgument
from nextcord import Invite
from nextcord.ext.abc import ContextBase

class InviteConverter(Converter[Invite]):
    """Converts to a :class:`~Invite`.

    This is done via an HTTP request using :meth:`.Bot.fetch_invite`.

    .. versionchanged:: 1.5
         Raise :exc:`.BadInviteArgument` instead of generic :exc:`.BadArgument`
    """

    async def convert(self, ctx: ContextBase, argument: str) -> Invite:
        try:
            invite = await ctx.bot.fetch_invite(argument)
            return invite
        except Exception as exc:
            raise BadInviteArgument(argument) from exc