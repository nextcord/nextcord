"""
See https://github.com/Rapptz/nextcord.py/issues/4098.
"""
import asyncio
from nextcord import Role, ChannelType, InvalidArgument, PermissionOverwrite
import nextcord.abc


async def _edit(self, options, reason):
    try:
        parent = options.pop("category")
    except KeyError:
        parent_id = nextcord.abc._undefined
    else:
        parent_id = parent and parent.id
    try:
        options["rate_limit_per_user"] = options.pop("slowmode_delay")
    except KeyError:
        pass
    lock_permissions = options.pop("sync_permissions", False)
    try:
        position = options.pop("position")
    except KeyError:
        if parent_id is not nextcord.abc._undefined:
            if lock_permissions:
                category = self.guild.get_channel(parent_id)
                options["permission_overwrites"] = [c._asdict() for c in category._overwrites]
            options["parent_id"] = parent_id
        elif lock_permissions and self.category_id is not None:
            # if we're syncing permissions on a pre-existing channel category without changing it
            # we need to update the permissions to point to the pre-existing category
            category = self.guild.get_channel(self.category_id)
            options["permission_overwrites"] = [c._asdict() for c in category._overwrites]
    else:
        await self._move(
            position, parent_id=parent_id, lock_permissions=lock_permissions, reason=reason
        )
    overwrites = options.get("overwrites", None)
    if overwrites is not None:
        perms = []
        for target, perm in overwrites.items():
            if not isinstance(perm, PermissionOverwrite):
                raise InvalidArgument(
                    "Expected PermissionOverwrite received {0.__name__}".format(type(perm))
                )
            allow, deny = perm.pair()
            payload = {
                "allow": allow.value,
                "deny": deny.value,
                "id": target.id,
            }
            if isinstance(target, Role):
                payload["type"] = "role"
            else:
                payload["type"] = "member"
            perms.append(payload)
        options["permission_overwrites"] = perms
    try:
        ch_type = options["type"]
    except KeyError:
        pass
    else:
        if not isinstance(ch_type, ChannelType):
            raise InvalidArgument("type field must be of type ChannelType")
        options["type"] = ch_type.value

    if options:
        data = await self._state.http.edit_channel(self.id, reason=reason, **options)
        # see issue Rapptz/nextcord.py#4098
        if "parent_id" in options:
            client = self._state._get_client()
            try:
                await client.wait_for(
                    "guild_channel_update",
                    check=lambda b, a: b.id == a.id and b.id == self.id,
                    timeout=2,
                )
                return
            except asyncio.TimeoutError:
                # fallback, we didn't receive the event within 2s
                pass
        self._update(self.guild, data)


nextcord.abc.GuildChannel._edit = _edit
