# SPDX-License-Identifier: MIT
# pyright: strict, reportPrivateUsage = false

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Awaitable, Callable, List, Optional, Union, cast

from .audit_logs import AuditLogEntry
from .auto_moderation import AutoModerationRule
from .bans import BanEntry
from .object import Object
from .utils import snowflake_time, time_snowflake

__all__ = (
    "reaction_iterator",
    "history_iterator",
    "ban_iterator",
    "audit_log_iterator",
    "guild_iterator",
    "member_iterator",
    "archived_thread_iterator",
    "scheduled_event_iterator",
    "scheduled_event_user_iterator",
)

if TYPE_CHECKING:
    from .abc import Messageable, Snowflake, SnowflakeTime
    from .client import Client
    from .enums import AuditLogAction
    from .guild import Guild
    from .member import Member
    from .message import Message
    from .scheduled_events import ScheduledEvent
    from .types.audit_log import AuditLog as AuditLogPayload
    from .types.guild import Ban as BanPayload, Guild as GuildPayload
    from .types.member import MemberWithUser
    from .types.message import Message as MessagePayload
    from .types.scheduled_events import (
        ScheduledEvent as ScheduledEventPayload,
        ScheduledEventUser as ScheduledEventUserPayload,
    )
    from .types.threads import Thread as ThreadPayload, ThreadPaginationPayload


OLDEST_OBJECT = Object(id=0)


async def reaction_iterator(
    message: Message, emoji: str, limit: int = 100, after: Optional[Snowflake] = None
):
    from .user import User

    state = message._state

    while limit > 0:
        retrieve = min(limit, 100)

        data = await state.http.get_reaction_users(
            message.channel.id, message.id, emoji, retrieve, after=after.id if after else None
        )

        if data:
            limit -= retrieve
            after = Object(id=int(data[-1]["id"]))

        for item in reversed(data):
            user: Union[User, Member]
            if (
                message.guild is None
                or isinstance(message.guild, Object)
                or not (member := message.guild.get_member(int(item["id"])))
            ):
                user = User(state=state, data=item)
            else:
                user = member

            yield user


async def history_iterator(
    messageable: Messageable,
    limit: Optional[int],
    before: Optional[SnowflakeTime] = None,
    after: Optional[SnowflakeTime] = None,
    around: Optional[SnowflakeTime] = None,
    oldest_first: Optional[bool] = None,
):
    """Iterator for receiving a channel's message history.

    The messages endpoint has two behaviours we care about here:
    If ``before`` is specified, the messages endpoint returns the ``limit``
    newest messages before ``before``, sorted with newest first. For filling over
    100 messages, update the ``before`` parameter to the oldest message received.
    Messages will be returned in order by time.
    If ``after`` is specified, it returns the ``limit`` oldest messages after
    ``after``, sorted with newest first. For filling over 100 messages, update the
    ``after`` parameter to the newest message received. If messages are not
    reversed, they will be out of order (99-0, 199-100, so on)

    A note that if both ``before`` and ``after`` are specified, ``before`` is ignored by the
    messages endpoint.

    .. versionchanged:: 3.0

        This was modified from being a class to being a function to remove unneeded
        bloat.

    Parameters
    ----------
    messageable: :class:`abc.Messageable`
        Messageable class to retrieve message history from.
    limit: :class:`int`
        Maximum number of messages to retrieve
    before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Message before which all messages must be.
    after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Message after which all messages must be.
    around: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Message around which all messages must be. Limit max 101. Note that if
        limit is an even number, this will return at most limit+1 messages.
    oldest_first: Optional[:class:`bool`]
        If set to ``True``, return messages in oldest->newest order. Defaults to
        ``True`` if ``after`` is specified, otherwise ``False``.
    """
    if isinstance(before, datetime.datetime):
        before = Object(id=time_snowflake(before, high=False))
    if isinstance(after, datetime.datetime):
        after = Object(id=time_snowflake(after, high=True))
    if isinstance(around, datetime.datetime):
        around = Object(id=time_snowflake(around))

    state = messageable._state
    channel = await messageable._get_channel()
    retrieve = 0

    reverse = after is not None if oldest_first is None else oldest_first

    checks: List[Callable[[MessagePayload], bool]] = []
    if around:
        if limit is None:
            raise ValueError("history does not support around with limit=None")
        if limit > 100:
            raise ValueError("history max limit 100 when specifying around parameter")

        # in nested functions, pyright thinks that the before and after parameters are
        # their old definitions as a parameter, so we manually cast in the functions

        if before is not None:

            def _check(msg: MessagePayload):
                b = cast("Object | Snowflake | None", before)
                return b is not None and int(msg["id"]) < b.id

            checks.append(_check)

        if after is not None:

            def _check(msg: MessagePayload):
                a = cast("Object | Snowflake | None", after)
                return a is not None and a.id < int(msg["id"])

            checks.append(_check)

    # we combine all of the checks together so we only have to replace the data payload once
    check: Callable[[MessagePayload], bool] = lambda m: all(c(m) for c in checks)

    def get_retrieve():
        nonlocal retrieve
        retrieve = min(limit, 100) if limit is not None else 100

        return retrieve > 0

    while get_retrieve():
        data: List[MessagePayload] = await state.http.logs_from(
            channel.id,
            retrieve,
            before.id if before is not None and around is None else None,
            after.id if after is not None and around is None else None,
            around.id if around is not None else None,
        )

        if data:
            if limit is not None:
                limit -= retrieve

            if before is not None:
                before = Object(id=int(data[-1]["id"]))
            if after is not None:
                after = Object(id=int(data[0]["id"]))
            if around is not None:
                around = None

        if len(data) < 100:
            limit = 0

        if checks:
            data = list(filter(check, data))
        if reverse:
            data = list(reversed(data))

        for item in data:
            yield state.create_message(channel=channel, data=item)


async def ban_iterator(
    guild: Guild,
    limit: Optional[int] = None,
    before: Optional[Snowflake] = None,
    after: Optional[Snowflake] = None,
):
    """Iterator for receiving a guild's bans.

    The bans endpoint has two behaviours we care about here:
    If ``before`` is specified, the bans endpoint returns the ``limit``
    bans with user ids before ``before``, sorted with smallest first. For filling over
    1000 bans, update the ``before`` parameter to the largest user id received.
    If ``after`` is specified, it returns the ``limit`` bans with user ids after
    ``after``, sorted with smallest first. For filling over 1000 bans, update the
    ``after`` parameter to the smallest user id received.

    A note that if both ``before`` and ``after`` are specified, ``after`` is ignored by the
    bans endpoint.

    .. versionchanged:: 3.0

        This was modified from being a class to being a function to remove unneeded
        bloat.

    Parameters
    ----------
    guild: :class:`~nextcord.Guild`
        The guild to get bans from.
    limit: Optional[:class:`int`]
        Maximum number of bans to retrieve.
    before: Optional[:class:`abc.Snowflake`]
        Date or user id before which all bans must be.
    after: Optional[:class:`abc.Snowflake`]
        Date or user id after which all bans must be.
    """
    state = guild._state
    retrieve = 0

    def get_retrieve():
        nonlocal retrieve
        retrieve = min(limit, 1000) if limit is not None else 1000

        return retrieve > 0

    while get_retrieve():
        data: List[BanPayload] = await state.http.get_bans(
            guild.id,
            retrieve,
            before=before.id if before is not None else None,
            after=after.id if after is not None else None,
        )

        if data:
            if limit:
                limit -= len(data)

            if before is not None:
                before = Object(id=int(data[0]["user"]["id"]))
            if after is not None:
                after = Object(id=int(data[-1]["user"]["id"]))

        if len(data) < 1000:
            limit = 0

        for item in data:
            yield BanEntry(user=state.create_user(item["user"]), reason=item["reason"])


async def audit_log_iterator(
    guild: Guild,
    limit: Optional[int] = None,
    before: Optional[SnowflakeTime] = None,
    after: Optional[SnowflakeTime] = None,
    oldest_first: Optional[bool] = None,
    user_id: Optional[int] = None,
    action_type: Optional[AuditLogAction] = None,
):
    if isinstance(before, datetime.datetime):
        before = Object(id=time_snowflake(before, high=False))
    if isinstance(after, datetime.datetime):
        after = Object(id=time_snowflake(after, high=True))

    state = guild._state
    retrieve = 0

    reverse = bool(oldest_first)

    def get_retrieve():
        nonlocal retrieve
        retrieve = min(limit, 100) if limit is not None else 100

        return retrieve > 0

    while get_retrieve():
        data: AuditLogPayload = await state.http.get_audit_logs(
            guild.id,
            limit=retrieve,
            user_id=user_id,
            action_type=action_type,
            before=before.id if before is not None else None,
            after=after.id if after is not None else None,
        )

        entries = data.get("audit_log_entries", [])
        if data and entries:
            if limit is not None:
                limit -= retrieve

            before = Object(id=int(entries[-1]["id"]))

        if len(entries) < 100:
            limit = 0

        if reverse:
            entries = list(reversed(entries))

        auto_moderation_rules = {
            int(rule["id"]): AutoModerationRule(data=rule, state=state)
            for rule in data.get("auto_moderation_rules", [])
        }
        users = {int(user["id"]): state.create_user(user) for user in data.get("users", [])}

        for item in entries:
            yield AuditLogEntry(
                data=item,
                auto_moderation_rules=auto_moderation_rules,
                users=users,
                guild=guild,
            )


async def guild_iterator(
    client: Client,
    limit: Optional[int],
    with_counts: bool = False,
    before: Optional[SnowflakeTime] = None,
    after: Optional[SnowflakeTime] = None,
):
    """Iterator for receiving the client's guilds.

    The guilds endpoint has the same two behaviours as described
    in :class:`HistoryIterator`:
    If ``before`` is specified, the guilds endpoint returns the ``limit``
    newest guilds before ``before``, sorted with newest first. For filling over
    100 guilds, update the ``before`` parameter to the oldest guild received.
    Guilds will be returned in order by time.
    If ``after`` is specified, it returns the ``limit`` oldest guilds after ``after``,
    sorted with newest first. For filling over 100 guilds, update the ``after``
    parameter to the newest guild received, If guilds are not reversed, they
    will be out of order (99-0, 199-100, so on)

    Not that if both ``before`` and ``after`` are specified, ``before`` is ignored by the
    guilds endpoint.

    .. versionchanged:: 3.0

        This was modified from being a class to being a function to remove unneeded
        bloat.

    Parameters
    ----------
    client: :class:`nextcord.Client`
        The client to retrieve the guilds from.
    limit: :class:`int`
        Maximum number of guilds to retrieve.
    with_counts: :class:`bool`
        Whether to include approximate member and presence counts for the guilds.
        Defaults to ``False``.

        .. versionadded:: 2.6
    before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Object before which all guilds must be.
    after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Object after which all guilds must be.
    """
    from .guild import Guild

    if isinstance(before, datetime.datetime):
        before = Object(id=time_snowflake(before, high=False))
    if isinstance(after, datetime.datetime):
        after = Object(id=time_snowflake(after, high=True))

    state = client._connection
    retrieve = 0
    reverse = bool(before)

    check: Optional[Callable[[GuildPayload], bool]] = None
    if before is not None and after is not None:

        def _check(guild: GuildPayload):
            a = cast("Object | Snowflake | None", after)
            return a is not None and int(guild["id"]) > a.id

        check = _check

    def get_retrieve():
        nonlocal retrieve
        retrieve = min(limit, 200) if limit is not None else 200

        return retrieve > 0

    while get_retrieve():
        data: List[GuildPayload] = await state.http.get_guilds(
            retrieve,
            before=before.id if before is not None else None,
            after=after.id if after is not None else None,
            with_counts=with_counts,
        )

        if data:
            if limit is not None:
                limit -= retrieve

            if before is not None:
                before = Object(id=int(data[0]["id"]))
            if after is not None:
                after = Object(id=int(data[-1]["id"]))

        if len(data) < 200:
            limit = 0

        if check is not None:
            data = list(filter(check, data))
        if reverse:
            data = list(reversed(data))

        for item in data:
            yield Guild(state=state, data=item)


async def member_iterator(
    guild: Guild,
    limit: Optional[int] = 1000,
    after: Optional[Union[Snowflake, datetime.datetime]] = None,
):
    from .member import Member

    if isinstance(after, datetime.datetime):
        after = Object(id=time_snowflake(after, high=True))

    state = guild._state
    after = after or OLDEST_OBJECT
    retrieve = 0

    def get_retrieve():
        nonlocal retrieve
        retrieve = min(limit, 1000) if limit is not None else 1000

        return retrieve > 0

    while get_retrieve():
        data: List[MemberWithUser] = await state.http.get_members(guild.id, retrieve, after.id)

        if len(data) < 1000:
            limit = 0

        after = Object(id=int(data[-1]["user"]["id"]))

        for item in reversed(data):
            yield Member(data=item, guild=guild, state=state)


async def archived_thread_iterator(
    channel_id: int,
    guild: Guild,
    limit: Optional[int],
    joined: bool,
    private: bool,
    before: Optional[Union[Snowflake, datetime.datetime]] = None,
):
    from .threads import Thread

    state = guild._state
    has_more = True

    cbefore: Optional[str]
    if before is None:
        cbefore = None
    elif isinstance(before, datetime.datetime):
        cbefore = str(time_snowflake(before, high=False)) if joined else before.isoformat()
    else:
        cbefore = str(before.id) if joined else snowflake_time(before.id).isoformat()

    update_before: Callable[[ThreadPayload], str] = lambda d: d["thread_metadata"][
        "archive_timestamp"
    ]
    endpoint: Callable[..., Awaitable[ThreadPaginationPayload]]
    if joined:
        endpoint = state.http.get_joined_private_archived_threads
        update_before = lambda d: str(d["id"])
    elif private:
        endpoint = state.http.get_private_archived_threads
    else:
        endpoint = state.http.get_public_archived_threads

    while has_more:
        limit = max(limit, 50) if limit is not None else 50
        data = await endpoint(channel_id, before=cbefore, limit=limit)

        threads = data["threads"]
        has_more = data["has_more"]

        limit -= len(threads)
        if limit <= 0:
            has_more = False

        if has_more:
            cbefore = update_before(threads[-1])

        for item in reversed(threads):
            yield Thread(guild=guild, state=state, data=item)


async def scheduled_event_iterator(
    guild: Guild,
    with_users: bool = False,
):
    state = guild._state
    data: List[ScheduledEventPayload] = await state.http.get_guild_events(guild.id, with_users)

    for item in reversed(data):
        yield guild._store_scheduled_event(item)


async def scheduled_event_user_iterator(
    guild: Guild,
    event: ScheduledEvent,
    limit: Optional[int] = None,
    before: Optional[Snowflake] = None,
    after: Optional[Snowflake] = None,
):
    state = guild._state
    retrieve = 0

    def get_retrieve():
        nonlocal retrieve
        retrieve = min(limit, 100) if limit is not None else 100

        return retrieve > 0

    while get_retrieve():
        data: List[ScheduledEventUserPayload] = await state.http.get_event_users(
            guild.id,
            event.id,
            limit=retrieve,
            before=before.id if before else None,
            after=after.id if after else None,
        )

        if data:
            if limit is not None:
                limit -= len(data)

            if before is not None:
                before = Object(id=int(data[0]["user"]["id"]))
            if after is not None:
                after = Object(id=int(data[-1]["user"]["id"]))

        if len(data) < 100:
            limit = 0  # terminate the infinte loop

        for item in reversed(data):
            yield event._update_user(item)
