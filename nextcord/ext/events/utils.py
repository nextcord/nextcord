import asyncio
import datetime

from functools import wraps
from typing import Callable, Optional

import nextcord


SLEEP_FOR = 2.5


async def fetch_recent_audit_log_entry(client: nextcord.Client, guild: nextcord.Guild, *, target: nextcord.User = None,
                                       action: nextcord.AuditLogAction = None, retry: int = 0) -> Optional[nextcord.AuditLogEntry]:
    """|coro|

    Attempts to retrieve an recently created :class:`~nextcord.AuditLogEntry` which meets the specified requirements.

    Parameters
    ----------
    client: :class:`~nextcord.Client`
        The nextcord client to make the api calls with.
    guild: :class:`~nextcord.Guild`
        The guild to retrieve the audit log entry from.
    target: Optional[:class:`~nextcord.User`]
        The target to filter with.
    action: Optional[:class:`~nextcord.AuditLogAction`]
        The action to filter with.
    retry: Optional[:class:`int`]
        The number of times fetching an entry should be retried.
        Defaults to 0.

    Raises
    ------
    Forbidden
        You do not have access to the guild's audit log.
    HTTPException
        Fetching the member failed.

    Returns
    --------
    Optional[:class:`~nextcord.AuditLogEntry`]
        The relevant audit log entry if found.
    """
    async for entry in guild.audit_logs(limit=1, action=action):

        delta = datetime.datetime.utcnow() - entry.created_at
        if delta < datetime.timedelta(seconds=10):
            if target is not None and entry.target != target:
                continue

            return entry

    if retry > 0:
        await asyncio.sleep(SLEEP_FOR)
        return await fetch_recent_audit_log_entry(client, guild, target=target, action=action, retry=retry - 1)

    return None


def listens_for(*events: str) -> Callable:
    """Helper decorator which defines which events an event check is listening for.

    Parameters
    ----------
    *events: :class:`str`
        The names of the events to listen for.
    """

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        async def wrapper(client, event, *args, **kwargs):
            if event in events:
                await func(client, *args, **kwargs)

        return wrapper

    return decorator
