# SPDX-License-Identifier: MIT
# pyright: strict, reportPrivateUsage = false

from __future__ import annotations

import asyncio
import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
)

from .audit_logs import AuditLogEntry
from .auto_moderation import AutoModerationRule
from .bans import BanEntry
from .errors import NoMoreItems
from .object import Object
from .utils import maybe_coroutine, snowflake_time, time_snowflake

__all__ = (
    "reaction_iterator",
    "history_iterator",
    "ban_iterator",
    "audit_log_iterator",
    "GuildIterator",
    "MemberIterator",
    "ScheduledEventIterator",
    "ScheduledEventUserIterator",
)

if TYPE_CHECKING:
    from .abc import Messageable, Snowflake, SnowflakeTime
    from .client import Client
    from .enums import AuditLogAction
    from .guild import Guild
    from .http import HTTPClient
    from .member import Member
    from .message import Message
    from .scheduled_events import ScheduledEvent, ScheduledEventUser  # noqa: F401
    from .state import ConnectionState
    from .threads import Thread
    from .types.audit_log import AuditLog as AuditLogPayload, AuditLogEntry as AuditLogEntryPayload
    from .types.guild import Ban as BanPayload, Guild as GuildPayload
    from .types.member import MemberWithUser
    from .types.message import Message as MessagePayload
    from .types.scheduled_events import (
        ScheduledEvent as ScheduledEventPayload,
        ScheduledEventUser as ScheduledEventUserPayload,
    )
    from .types.threads import Thread as ThreadPayload, ThreadPaginationPayload
    from .types.user import PartialUser as PartialUserPayload
    from .user import User

T = TypeVar("T")
OT = TypeVar("OT")
_Func = Callable[[T], Union[OT, Awaitable[OT]]]

OLDEST_OBJECT = Object(id=0)


class _AsyncIterator(AsyncIterator[T]):
    __slots__ = ()

    async def next(self) -> T:
        raise NotImplementedError

    def get(self, **attrs: T) -> Awaitable[Optional[T]]:
        def predicate(elem: T):
            for attr, val in attrs.items():
                nested = attr.split("__")
                obj = elem
                for attribute in nested:
                    obj = getattr(obj, attribute)

                if obj != val:
                    return False
            return True

        return self.find(predicate)

    async def find(self, predicate: _Func[T, bool]) -> Optional[T]:
        while True:
            try:
                elem = await self.next()
            except NoMoreItems:
                return None

            ret = await maybe_coroutine(predicate, elem)
            if ret:
                return elem

    def chunk(self, max_size: int) -> _ChunkedAsyncIterator[T]:
        if max_size <= 0:
            raise ValueError("Async iterator chunk sizes must be greater than 0")
        return _ChunkedAsyncIterator(self, max_size)

    def map(self, func: _Func[T, OT]) -> _MappedAsyncIterator[T, OT]:
        return _MappedAsyncIterator(self, func)

    def filter(self, predicate: _Func[T, bool]) -> _FilteredAsyncIterator[T]:
        return _FilteredAsyncIterator(self, predicate)

    async def flatten(self) -> List[T]:
        return [element async for element in self]

    async def __anext__(self) -> T:
        try:
            return await self.next()
        except NoMoreItems:
            raise StopAsyncIteration()


def _identity(x: T) -> T:
    return x


class _ChunkedAsyncIterator(_AsyncIterator[List[T]]):
    def __init__(self, iterator: _AsyncIterator[T], max_size: int) -> None:
        self.iterator: _AsyncIterator[T] = iterator
        self.max_size: int = max_size

    async def next(self) -> List[T]:
        ret: List[T] = []
        n = 0
        while n < self.max_size:
            try:
                item = await self.iterator.next()
            except NoMoreItems:
                if ret:
                    return ret
                raise
            else:
                ret.append(item)
                n += 1
        return ret


class _MappedAsyncIterator(_AsyncIterator[OT], Generic[T, OT]):
    def __init__(self, iterator: _AsyncIterator[T], func: _Func[T, OT]) -> None:
        self.iterator: _AsyncIterator[T] = iterator
        self.func: _Func[T, Any] = func

    async def next(self) -> OT:
        # this raises NoMoreItems and will propagate appropriately
        item = await self.iterator.next()
        return await maybe_coroutine(self.func, item)


class _FilteredAsyncIterator(_AsyncIterator[T]):
    def __init__(self, iterator: _AsyncIterator[T], predicate: _Func[T, Any]) -> None:
        self.iterator: _AsyncIterator[T] = iterator

        if predicate is None:
            predicate = _identity

        self.predicate: _Func[T, Any] = predicate

    async def next(self) -> T:
        getter = self.iterator.next
        pred = self.predicate
        while True:
            # propagate NoMoreItems similar to _MappedAsyncIterator
            item = await getter()
            ret = await maybe_coroutine(pred, item)
            if ret:
                return item


async def reaction_iterator(message: Message, emoji: str, limit: int = 100, after: Optional[Snowflake] = None):
    from .user import User

    state = message._state

    while limit > 0:
        retrieve = limit if limit <= 100 else 100
        after_id = after.id if after else None

        data = cast(
            List[PartialUserPayload],
            await state.http.get_reaction_users(
                message.channel.id, message.id, emoji, retrieve, after=after_id
            ),
        )
        # cast needed here because of list's invariance

        if data:
            limit -= retrieve
            after = Object(id=int(data[-1]["id"]))

        for item in reversed(data):
            user: Union[User, Member]
            if message.guild is None or isinstance(message.guild, Object) or not (member := message.guild.get_member(int(item["id"]))):
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
    converted_after = after or OLDEST_OBJECT
    channel = await messageable._get_channel()
    retrieve = 0

    reverse: bool
    if oldest_first is None:
        reverse = after is not None
    else:
        reverse = oldest_first

    if around:
        if limit is None:
            raise ValueError("history does not support around with limit=None")
        if limit > 101:
            raise ValueError("history max limit 101 when specifying around parameter")
        elif limit == 101:
            limit = 100  # Thanks discord

    def get_retrieve():
        nonlocal retrieve

        if limit is None or limit > 100:
            retrieve = 100
        else:
            retrieve = limit

        return retrieve > 0

    while get_retrieve():
        data: List[MessagePayload] = await state.http.logs_from(
            channel.id, 
            retrieve, 
            before.id if before else None, 
            converted_after.id, 
            around.id if around else None,
        )

        if len(data):
            if limit:
                limit -= retrieve
            if len(data) < 100:
                limit = 0

            if before is not None:
                before = Object(id=int(data[-1]["id"]))
            if after is not None:
                converted_after = Object(id=int(data[0]["id"]))
            if around is not None:
                around = None

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
    from .user import User

    state = guild._state
    converted_after = after or OLDEST_OBJECT
    retrieve = 0

    def get_retrieve():
        nonlocal retrieve

        if limit is None or limit > 1000:
            retrieve = 1000
        else:
            retrieve = limit

        return retrieve > 0

    while get_retrieve():
        data: List[BanPayload] = await state.http.get_bans(
            guild.id, 
            retrieve, 
            before=before.id if before else None, 
            after=converted_after.id
        )

        if len(data):
            if limit:
                limit -= len(data)
            
            if before is not None:
                before = Object(id=int(data[0]["user"]["id"]))
            if after is not None:
                converted_after = Object(id=int(data[-1]["user"]["id"]))

        for item in data:
            yield BanEntry(user=User(state=state, data=item["user"]), reason=item["reason"])


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
    after = after or OLDEST_OBJECT
    retrieve = 0

    reverse: bool
    if oldest_first is None:
        reverse = after is not None
    else:
        reverse = oldest_first

    def get_retrieve():
        nonlocal retrieve

        if limit is None or limit > 100:
            retrieve = 100
        else:
            retrieve = limit

        return retrieve > 0

    while get_retrieve():
        data: AuditLogPayload = await state.http.get_audit_logs(
            guild.id,
            limit=retrieve,
            user_id=user_id,
            action_type=action_type,
            before=before.id if before else None,
        )

        entries = data.get("audit_log_entries", [])
        if len(data) and entries:
            if limit is not None:
                limit -= retrieve
            if len(data) < 100:
                limit = 0

            if before is not None:
                before = Object(id=int(entries[-1]["id"]))

        if reverse:
            entries = list(reversed(entries))
        entries = list(filter(lambda m: int(m["id"]) > after.id, entries))

        auto_moderation_rules = {
            int(rule["id"]): AutoModerationRule(data=rule, state=state)
            for rule in data.get("auto_moderation_rules", [])
        }
        users = {int(user["id"]): state.create_user(user) for user in data.get("users", [])}

        for item in entries:
            # TODO: remove this if statement later
            if item["action_type"] is None:
                continue

            yield AuditLogEntry(
                data=item,
                auto_moderation_rules=auto_moderation_rules,
                users=users,
                guild=guild,
            )


class GuildIterator(_AsyncIterator["Guild"]):
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

    Parameters
    ----------
    bot: :class:`nextcord.Client`
        The client to retrieve the guilds from.
    limit: :class:`int`
        Maximum number of guilds to retrieve.
    before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Object before which all guilds must be.
    after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
        Object after which all guilds must be.
    """

    def __init__(
        self,
        bot: Client,
        limit: Optional[int],
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
    ):
        self.retrieve: int

        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))

        self.bot: Client = bot
        self.limit: Optional[int] = limit
        self.before: Optional[Snowflake] = before
        self.after: Optional[Snowflake] = after

        self._filter: Optional[Callable[[GuildPayload], bool]] = None

        self.state: ConnectionState = self.bot._connection
        self.guilds: asyncio.Queue[Guild] = asyncio.Queue()

        self.reverse: bool
        if self.before:
            self.reverse = True
            self._retrieve_guilds = self._retrieve_guilds_before_strategy
            if self.after:
                self._filter = lambda m: int(m["id"]) > self.after.id  # type: ignore
        else:
            self.reverse = False
            self._retrieve_guilds = self._retrieve_guilds_after_strategy

    async def next(self) -> Guild:
        if self.guilds.empty():
            await self.fill_guilds()

        try:
            return self.guilds.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self):
        l = self.limit
        if l is None or l > 200:
            r = 200
        else:
            r = l
        self.retrieve = r
        return r > 0

    def create_guild(self, data: GuildPayload) -> Guild:
        from .guild import Guild

        return Guild(state=self.state, data=data)

    async def fill_guilds(self) -> None:
        if self._get_retrieve():
            data = await self._retrieve_guilds(self.retrieve)
            if len(data) < 200:
                self.limit = 0

            if self.reverse:
                data = reversed(data)
            if self._filter:
                data = filter(self._filter, data)

            for element in data:
                await self.guilds.put(self.create_guild(element))

    async def _retrieve_guilds(self, retrieve: int) -> List[GuildPayload]:
        """Retrieve guilds and update next parameters."""
        raise NotImplementedError

    async def _retrieve_guilds_before_strategy(self, retrieve: int) -> List[GuildPayload]:
        """Retrieve guilds using before parameter."""
        before = self.before.id if self.before else None
        data: List[GuildPayload] = await self.bot.http.get_guilds(retrieve, before=before)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.before = Object(id=int(data[0]["id"]))
        return data

    async def _retrieve_guilds_after_strategy(self, retrieve: int) -> List[GuildPayload]:
        """Retrieve guilds using after parameter."""
        after = self.after.id if self.after else None
        data: List[GuildPayload] = await self.bot.http.get_guilds(retrieve, after=after)
        if len(data):
            if self.limit is not None:
                self.limit -= retrieve
            self.after = Object(id=int(data[-1]["id"]))
        return data


class MemberIterator(_AsyncIterator["Member"]):
    def __init__(
        self,
        guild: Guild,
        limit: Optional[int] = 1000,
        after: Optional[Union[Snowflake, datetime.datetime]] = None,
    ):
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))

        self.retrieve: int
        self.guild: Guild = guild
        self.limit: Optional[int] = limit
        self.after: Snowflake = after or OLDEST_OBJECT

        self.state: ConnectionState = self.guild._state
        self.members: asyncio.Queue[Member] = asyncio.Queue()

    async def next(self) -> Member:
        if self.members.empty():
            await self.fill_members()

        try:
            return self.members.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self):
        l = self.limit
        if l is None or l > 1000:
            r = 1000
        else:
            r = l
        self.retrieve = r
        return r > 0

    async def fill_members(self) -> None:
        if self._get_retrieve():
            after = self.after.id if self.after else None
            data = await self.state.http.get_members(self.guild.id, self.retrieve, after)
            if not data:
                # no data, terminate
                return

            if len(data) < 1000:
                self.limit = 0  # terminate loop

            self.after = Object(id=int(data[-1]["user"]["id"]))

            for element in reversed(data):
                await self.members.put(self.create_member(element))

    def create_member(self, data: MemberWithUser) -> Member:
        from .member import Member

        return Member(data=data, guild=self.guild, state=self.state)


class ArchivedThreadIterator(_AsyncIterator["Thread"]):
    def __init__(
        self,
        channel_id: int,
        guild: Guild,
        limit: Optional[int],
        joined: bool,
        private: bool,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
    ):
        self.channel_id: int = channel_id
        self.guild: Guild = guild
        self.limit: Optional[int] = limit
        self.joined: bool = joined
        self.private: bool = private
        self.http: HTTPClient = guild._state.http

        if joined and not private:
            raise ValueError("Cannot iterate over joined public archived threads")

        self.before: Optional[str]
        if before is None:
            self.before = None
        elif isinstance(before, datetime.datetime):
            if joined:
                self.before = str(time_snowflake(before, high=False))
            else:
                self.before = before.isoformat()
        else:
            if joined:
                self.before = str(before.id)
            else:
                self.before = snowflake_time(before.id).isoformat()

        self.update_before: Callable[[ThreadPayload], str] = self.get_archive_timestamp

        self.endpoint: Callable[..., Awaitable[ThreadPaginationPayload]]
        if joined:
            self.endpoint = self.http.get_joined_private_archived_threads
            self.update_before = self.get_thread_id
        elif private:
            self.endpoint = self.http.get_private_archived_threads
        else:
            self.endpoint = self.http.get_public_archived_threads

        self.queue: asyncio.Queue[Thread] = asyncio.Queue()
        self.has_more: bool = True

    async def next(self) -> Thread:
        if self.queue.empty():
            await self.fill_queue()

        try:
            return self.queue.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    @staticmethod
    def get_archive_timestamp(data: ThreadPayload) -> str:
        return data["thread_metadata"]["archive_timestamp"]

    @staticmethod
    def get_thread_id(data: ThreadPayload) -> str:
        return data["id"]  # type: ignore

    async def fill_queue(self) -> None:
        if not self.has_more:
            raise NoMoreItems()

        limit = 50 if self.limit is None else max(self.limit, 50)
        data = await self.endpoint(self.channel_id, before=self.before, limit=limit)

        # This stuff is obviously WIP because 'members' is always empty
        threads: List[ThreadPayload] = data.get("threads", [])
        for d in reversed(threads):
            self.queue.put_nowait(self.create_thread(d))

        self.has_more = data.get("has_more", False)
        if self.limit is not None:
            self.limit -= len(threads)
            if self.limit <= 0:
                self.has_more = False

        if self.has_more:
            self.before = self.update_before(threads[-1])

    def create_thread(self, data: ThreadPayload) -> Thread:
        from .threads import Thread

        return Thread(guild=self.guild, state=self.guild._state, data=data)


class ScheduledEventIterator(_AsyncIterator["ScheduledEvent"]):
    def __init__(self, guild: Guild, with_users: bool = False):
        self.guild: Guild = guild
        self.with_users: bool = with_users

        self.state: ConnectionState = self.guild._state
        self.queue: asyncio.Queue[ScheduledEvent] = asyncio.Queue()
        self.has_more: bool = True

    async def next(self) -> ScheduledEvent:
        if self.queue.empty():
            await self.fill_queue()

        try:
            return self.queue.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    async def fill_queue(self) -> None:
        if not self.has_more:
            raise NoMoreItems()

        data = await self.state.http.get_guild_events(self.guild.id, self.with_users)
        self.has_more = False
        if not data:
            # no data, terminate
            return

        for element in reversed(data):
            await self.queue.put(self.create_event(element))

    def create_event(self, data: ScheduledEventPayload) -> ScheduledEvent:
        return self.guild._store_scheduled_event(data)


class ScheduledEventUserIterator(_AsyncIterator["ScheduledEventUser"]):
    def __init__(
        self,
        guild: Guild,
        event: ScheduledEvent,
        with_member: bool = False,
        limit: Optional[int] = None,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
    ):
        self.guild: Guild = guild
        self.event: ScheduledEvent = event
        self.with_member: bool = with_member

        self.limit: Optional[int] = limit
        self.before: Optional[Snowflake] = before
        self.after: Snowflake = after or OLDEST_OBJECT

        if self.before:
            self._retrieve_users = self._retrieve_users_before_strategy
        else:
            self._retrieve_users = self._retrieve_users_after_strategy

        self.retrieve: int
        self.state: ConnectionState = self.guild._state
        self.queue: asyncio.Queue[ScheduledEventUser] = asyncio.Queue()
        self.has_more = True

    async def next(self) -> ScheduledEventUser:
        if self.queue.empty():
            await self.fill_queue()

        try:
            return self.queue.get_nowait()
        except asyncio.QueueEmpty:
            raise NoMoreItems()

    def _get_retrieve(self) -> bool:
        self.retrieve = min(self.limit, 100) if self.limit is not None else 100
        return self.retrieve > 0

    async def fill_queue(self) -> None:
        if self._get_retrieve():
            data = await self._retrieve_users(self.retrieve)
            if len(data) < 100:
                self.limit = 0  # terminate the infinite loop

            for element in reversed(data):
                await self.queue.put(self.create_user(element))

    def create_user(self, data: ScheduledEventUserPayload) -> ScheduledEventUser:
        return self.event._update_user(data=data)

    async def _retrieve_users_before_strategy(
        self, retrieve: int
    ) -> List[ScheduledEventUserPayload]:
        """Retrieve users using before parameter."""
        before = self.before.id if self.before else None
        data: List[ScheduledEventUserPayload] = await self.state.http.get_event_users(
            self.guild.id, self.event.id, limit=retrieve, before=before
        )
        if len(data):
            if self.limit is not None:
                self.limit -= len(data)
            self.before = Object(id=int(data[0]["user"]["id"]))
        return data

    async def _retrieve_users_after_strategy(
        self, retrieve: int
    ) -> List[ScheduledEventUserPayload]:
        """Retrieve users using after parameter."""
        after = self.after.id if self.after else None
        data: List[ScheduledEventUserPayload] = await self.state.http.get_event_users(
            self.guild.id, self.event.id, limit=retrieve, after=after
        )
        if len(data):
            if self.limit is not None:
                self.limit -= len(data)
            self.after = Object(id=int(data[-1]["user"]["id"]))
        return data
