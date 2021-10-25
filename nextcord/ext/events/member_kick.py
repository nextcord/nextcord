import nextcord

from ._events import _ALL
from .utils import fetch_recent_audit_log_entry, listens_for


EVENT_NAME = 'member_kick'


@listens_for('member_remove')
async def check_member_kick(client: nextcord.Client, member: nextcord.Member):
    guild = member.guild

    print('!RAN')

    if not guild.me.guild_permissions.view_audit_log:
        return

    entry = await fetch_recent_audit_log_entry(client, member.guild, target=member, action=nextcord.AuditLogAction.kick, retry=3)
    if entry is None:
        return

    client.dispatch(EVENT_NAME, member, entry)


_ALL[EVENT_NAME] = check_member_kick
