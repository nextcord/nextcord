"""An experiment that enables auto removing reactions added to menus.

"""

import nextcord
from nextcord.ext import menus


_old_update = menus.Menu.update


async def update(self: menus.Menu, payload: nextcord.RawReactionActionEvent):
    await _old_update(self, payload)

    if payload.event_type != "REACTION_ADD":
        return

    permissions = self.ctx.channel.permissions_for(self.ctx.me)
    if not (permissions.manage_messages or permissions.administrator):
        return

    await self.message.remove_reaction(payload.emoji, nextcord.Object(id=payload.user_id))


update.__doc__ = _old_update.__doc__
menus.Menu.update = update
