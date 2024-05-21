# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple, Type

import aiohttp

from .backoff import ExponentialBackoff
from .client import Client
from .enums import Status
from .errors import (
    ClientException,
    ConnectionClosed,
    GatewayNotFound,
    HTTPException,
    PrivilegedIntentsRequired,
)
from .flags import Intents
from .gateway import *
from .state import AutoShardedConnectionState
from .utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .activity import BaseActivity
    from .flags import MemberCacheFlags
    from .gateway import DiscordWebSocket
    from .mentions import AllowedMentions

__all__ = (
    "AutoShardedClient",
    "ShardInfo",
)

_log = logging.getLogger(__name__)


class EventType:
    close = 0
    reconnect = 1
    resume = 2
    identify = 3
    terminate = 4
    clean_close = 5


class EventItem:
    __slots__ = ("type", "shard", "error")

    def __init__(self, etype: int, shard: Optional["Shard"], error: Optional[Exception]) -> None:
        self.type: int = etype
        self.shard: Optional["Shard"] = shard
        self.error: Optional[Exception] = error

    def __lt__(self, other: Self) -> bool:
        if not isinstance(other, EventItem):
            return NotImplemented
        return self.type < other.type

    def __eq__(self, other: Self) -> bool:
        if not isinstance(other, EventItem):
            return NotImplemented
        return self.type == other.type

    def __hash__(self) -> int:
        return hash(self.type)


class Shard:
    def __init__(
        self,
        ws: DiscordWebSocket,
        client: AutoShardedClient,
        queue_put: Callable[[EventItem], None],
    ) -> None:
        self.ws: DiscordWebSocket = ws
        self._client: Client = client
        self._dispatch: Callable[..., None] = client.dispatch
        self._queue_put: Callable[[EventItem], None] = queue_put
        self.loop: asyncio.AbstractEventLoop = self._client.loop
        self._disconnect: bool = False
        self._reconnect = client._reconnect
        self._backoff: ExponentialBackoff = ExponentialBackoff()
        self._task: Optional[asyncio.Task] = None
        self._handled_exceptions: Tuple[Type[Exception], ...] = (
            OSError,
            HTTPException,
            GatewayNotFound,
            ConnectionClosed,
            aiohttp.ClientError,
            asyncio.TimeoutError,
        )

    @property
    def id(self) -> int:
        # DiscordWebSocket.shard_id is set in the from_client classmethod
        return self.ws.shard_id  # type: ignore

    def launch(self) -> None:
        self._task = self.loop.create_task(self.worker())

    def _cancel_task(self) -> None:
        if self._task is not None and not self._task.done():
            self._task.cancel()

    async def close(self) -> None:
        self._cancel_task()
        await self.ws.close(code=1000)

    async def disconnect(self) -> None:
        await self.close()
        self._dispatch("shard_disconnect", self.id)

    async def _handle_disconnect(self, e: Exception) -> None:
        self._dispatch("disconnect")
        self._dispatch("shard_disconnect", self.id)
        if not self._reconnect:
            self._queue_put(EventItem(EventType.close, self, e))
            return

        if self._client.is_closed():
            return

        if isinstance(e, OSError) and e.errno in (54, 10054):
            # If we get Connection reset by peer then always try to RESUME the connection.
            exc = ReconnectWebSocket(self.id, resume=True)
            self._queue_put(EventItem(EventType.resume, self, exc))
            return

        if isinstance(e, ConnectionClosed):
            if e.code == 4014:
                self._queue_put(
                    EventItem(EventType.terminate, self, PrivilegedIntentsRequired(self.id))
                )
                return
            if e.code != 1000:
                self._queue_put(EventItem(EventType.close, self, e))
                return

        retry = self._backoff.delay()
        _log.error("Attempting a reconnect for shard ID %s in %.2fs", self.id, retry, exc_info=e)
        await asyncio.sleep(retry)
        self._queue_put(EventItem(EventType.reconnect, self, e))

    async def worker(self) -> None:
        while not self._client.is_closed():
            try:
                await self.ws.poll_event()
            except ReconnectWebSocket as e:
                etype = EventType.resume if e.resume else EventType.identify
                self._queue_put(EventItem(etype, self, e))
                break
            except self._handled_exceptions as e:
                await self._handle_disconnect(e)
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._queue_put(EventItem(EventType.terminate, self, e))
                break

    async def reidentify(self, exc: ReconnectWebSocket) -> None:
        self._cancel_task()
        self._dispatch("disconnect")
        self._dispatch("shard_disconnect", self.id)
        _log.info("Got a request to %s the websocket at Shard ID %s.", exc.op, self.id)
        try:
            coro = DiscordWebSocket.from_client(
                self._client,
                resume=exc.resume,
                shard_id=self.id,
                session=self.ws.session_id,
                sequence=self.ws.sequence,
            )
            self.ws = await asyncio.wait_for(coro, timeout=60.0)
        except self._handled_exceptions as e:
            await self._handle_disconnect(e)
        except asyncio.CancelledError:
            return
        except Exception as e:
            self._queue_put(EventItem(EventType.terminate, self, e))
        else:
            self.launch()

    async def reconnect(self) -> None:
        self._cancel_task()
        try:
            coro = DiscordWebSocket.from_client(self._client, shard_id=self.id)
            self.ws = await asyncio.wait_for(coro, timeout=60.0)
        except self._handled_exceptions as e:
            await self._handle_disconnect(e)
        except asyncio.CancelledError:
            return
        except Exception as e:
            self._queue_put(EventItem(EventType.terminate, self, e))
        else:
            self.launch()


class ShardInfo:
    """A class that gives information and control over a specific shard.

    You can retrieve this object via :meth:`AutoShardedClient.get_shard`
    or :attr:`AutoShardedClient.shards`.

    .. versionadded:: 1.4

    Attributes
    ----------
    id: :class:`int`
        The shard ID for this shard.
    shard_count: Optional[:class:`int`]
        The shard count for this cluster. If this is ``None`` then the bot has not started yet.
    """

    __slots__ = ("_parent", "id", "shard_count")

    def __init__(self, parent: Shard, shard_count: Optional[int]) -> None:
        self._parent: Shard = parent
        self.id: int = parent.id
        self.shard_count: Optional[int] = shard_count

    def is_closed(self) -> bool:
        """:class:`bool`: Whether the shard connection is currently closed."""
        return not self._parent.ws.open

    async def disconnect(self) -> None:
        """|coro|

        Disconnects a shard. When this is called, the shard connection will no
        longer be open.

        If the shard is already disconnected this does nothing.
        """
        if self.is_closed():
            return

        await self._parent.disconnect()

    async def reconnect(self) -> None:
        """|coro|

        Disconnects and then connects the shard again.
        """
        if not self.is_closed():
            await self._parent.disconnect()
        await self._parent.reconnect()

    async def connect(self) -> None:
        """|coro|

        Connects a shard. If the shard is already connected this does nothing.
        """
        if not self.is_closed():
            return

        await self._parent.reconnect()

    @property
    def latency(self) -> float:
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds for this shard."""
        return self._parent.ws.latency

    def is_ws_ratelimited(self) -> bool:
        """:class:`bool`: Whether the websocket is currently rate limited.

        This can be useful to know when deciding whether you should query members
        using HTTP or via the gateway.

        .. versionadded:: 1.6
        """
        return self._parent.ws.is_ratelimited()


class AutoShardedClient(Client):
    """A client similar to :class:`Client` except it handles the complications
    of sharding for the user into a more manageable and transparent single
    process bot.

    When using this client, you will be able to use it as-if it was a regular
    :class:`Client` with a single shard when implementation wise internally it
    is split up into multiple shards. This allows you to not have to deal with
    IPC or other complicated infrastructure.

    It is recommended to use this client only if you have surpassed at least
    1000 guilds.

    If no :attr:`.shard_count` is provided, then the library will use the
    Bot Gateway endpoint call to figure out how many shards to use.

    If a ``shard_ids`` parameter is given, then those shard IDs will be used
    to launch the internal shards. Note that :attr:`.shard_count` must be provided
    if this is used. By default, when omitted, the client will launch shards from
    0 to ``shard_count - 1``.

    Attributes
    ----------
    shard_ids: Optional[List[:class:`int`]]
        An optional list of shard_ids to launch the shards with.
    """

    if TYPE_CHECKING:
        _connection: AutoShardedConnectionState

    def __init__(
        self,
        *,
        shard_ids: Optional[list[int]] = None,
        max_messages: Optional[int] = 1000,
        connector: Optional[aiohttp.BaseConnector] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        shard_id: Optional[int] = None,
        shard_count: Optional[int] = None,
        application_id: Optional[int] = None,
        intents: Intents = Intents.default(),
        member_cache_flags: MemberCacheFlags = MISSING,
        chunk_guilds_at_startup: bool = MISSING,
        status: Optional[Status] = None,
        activity: Optional[BaseActivity] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        heartbeat_timeout: float = 60.0,
        guild_ready_timeout: float = 2.0,
        assume_unsync_clock: bool = True,
        enable_debug_events: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        lazy_load_commands: bool = True,
        rollout_associate_known: bool = True,
        rollout_delete_unknown: bool = True,
        rollout_register_new: bool = True,
        rollout_update_known: bool = True,
        rollout_all_guilds: bool = False,
        default_guild_ids: Optional[List[int]] = None,
    ) -> None:
        self.shard_ids: Optional[List[int]] = shard_ids
        super().__init__(
            max_messages=max_messages,
            connector=connector,
            proxy=proxy,
            proxy_auth=proxy_auth,
            shard_id=shard_id,
            shard_count=shard_count,
            application_id=application_id,
            intents=intents,
            member_cache_flags=member_cache_flags,
            chunk_guilds_at_startup=chunk_guilds_at_startup,
            status=status,
            activity=activity,
            allowed_mentions=allowed_mentions,
            heartbeat_timeout=heartbeat_timeout,
            guild_ready_timeout=guild_ready_timeout,
            assume_unsync_clock=assume_unsync_clock,
            enable_debug_events=enable_debug_events,
            loop=loop,
            lazy_load_commands=lazy_load_commands,
            rollout_associate_known=rollout_associate_known,
            rollout_delete_unknown=rollout_delete_unknown,
            rollout_register_new=rollout_register_new,
            rollout_update_known=rollout_update_known,
            rollout_all_guilds=rollout_all_guilds,
            default_guild_ids=default_guild_ids,
        )

        if self.shard_ids is not None:
            if self.shard_count is None:
                raise ClientException(
                    "When passing manual shard_ids, you must provide a shard_count."
                )

            if not isinstance(self.shard_ids, (list, tuple)):
                raise ClientException("shard_ids parameter must be a list or a tuple.")

        # instead of a single websocket, we have multiple
        # the key is the shard_id
        self.__shards = {}
        self._connection._get_websocket = self._get_websocket
        self._connection._get_client = lambda: self
        self.__queue = asyncio.PriorityQueue()

    def _get_websocket(
        self, guild_id: Optional[int] = None, *, shard_id: Optional[int] = None
    ) -> DiscordWebSocket:
        if shard_id is None:
            # guild_id won't be None if shard_id is None and shard_count won't be None here
            shard_id = (guild_id >> 22) % self.shard_count  # type: ignore
        return self.__shards[shard_id].ws

    def _get_state(
        self,
        max_messages: Optional[int],
        application_id: Optional[int],
        heartbeat_timeout: float,
        guild_ready_timeout: float,
        allowed_mentions: Optional[AllowedMentions],
        activity: Optional[BaseActivity],
        status: Optional[Status],
        intents: Intents,
        chunk_guilds_at_startup: bool,
        member_cache_flags: MemberCacheFlags,
    ) -> AutoShardedConnectionState:
        return AutoShardedConnectionState(
            dispatch=self.dispatch,
            handlers=self._handlers,
            hooks=self._hooks,
            http=self.http,
            loop=self.loop,
            max_messages=max_messages,
            application_id=application_id,
            heartbeat_timeout=heartbeat_timeout,
            guild_ready_timeout=guild_ready_timeout,
            allowed_mentions=allowed_mentions,
            activity=activity,
            status=status,
            intents=intents,
            chunk_guilds_at_startup=chunk_guilds_at_startup,
            member_cache_flags=member_cache_flags,
        )

    @property
    def latency(self) -> float:
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This operates similarly to :meth:`Client.latency` except it uses the average
        latency of every shard's latency. To get a list of shard latency, check the
        :attr:`latencies` property. Returns ``nan`` if there are no shards ready.
        """
        if not self.__shards:
            return float("nan")
        return sum(latency for _, latency in self.latencies) / len(self.__shards)

    @property
    def latencies(self) -> List[Tuple[int, float]]:
        """List[Tuple[:class:`int`, :class:`float`]]: A list of latencies between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This returns a list of tuples with elements ``(shard_id, latency)``.
        """
        return [(shard_id, shard.ws.latency) for shard_id, shard in self.__shards.items()]

    def get_shard(self, shard_id: int) -> Optional[ShardInfo]:
        """Optional[:class:`ShardInfo`]: Gets the shard information at a given shard ID or ``None`` if not found."""
        try:
            parent = self.__shards[shard_id]
        except KeyError:
            return None
        else:
            return ShardInfo(parent, self.shard_count)

    @property
    def shards(self) -> Dict[int, ShardInfo]:
        """Mapping[int, :class:`ShardInfo`]: Returns a mapping of shard IDs to their respective info object."""
        return {
            shard_id: ShardInfo(parent, self.shard_count)
            for shard_id, parent in self.__shards.items()
        }

    async def launch_shard(self, gateway: str, shard_id: int, *, initial: bool = False) -> None:
        try:
            coro = DiscordWebSocket.from_client(
                self, initial=initial, gateway=gateway, shard_id=shard_id
            )
            ws = await asyncio.wait_for(coro, timeout=180.0)
        except Exception:
            _log.exception("Failed to connect for shard_id: %s. Retrying...", shard_id)
            await asyncio.sleep(5.0)
            return await self.launch_shard(gateway, shard_id)

        # keep reading the shard while others connect
        self.__shards[shard_id] = ret = Shard(ws, self, self.__queue.put_nowait)
        ret.launch()
        return None

    async def launch_shards(self) -> None:
        if self.shard_count is None:
            self.shard_count, gateway = await self.http.get_bot_gateway()
        else:
            gateway = await self.http.get_gateway()

        self._connection.shard_count = self.shard_count

        shard_ids = self.shard_ids or range(self.shard_count)
        self._connection.shard_ids = shard_ids

        for shard_id in shard_ids:
            initial = shard_id == shard_ids[0]
            await self.launch_shard(gateway, shard_id, initial=initial)

        self._connection.shards_launched.set()

    async def connect(self, *, reconnect: bool = True) -> None:
        self._reconnect = reconnect
        await self.launch_shards()

        while not self.is_closed():
            item = await self.__queue.get()
            if item.type == EventType.close:
                await self.close()
                if isinstance(item.error, ConnectionClosed):
                    if item.error.code != 1000:
                        raise item.error
                    if item.error.code == 4014:  # type: ignore # "false always"
                        raise PrivilegedIntentsRequired(item.shard.id) from None
                return
            if item.type in (EventType.identify, EventType.resume):
                await item.shard.reidentify(item.error)
            elif item.type == EventType.reconnect:
                await item.shard.reconnect()
            elif item.type == EventType.terminate:
                await self.close()
                raise item.error
            elif item.type == EventType.clean_close:
                return

    async def close(self) -> None:
        """|coro|

        Closes the connection to Discord.
        """
        if self.is_closed():
            return

        self._closed = True

        for vc in self.voice_clients:
            with contextlib.suppress(Exception):
                await vc.disconnect(force=True)

        to_close = [
            asyncio.ensure_future(shard.close(), loop=self.loop) for shard in self.__shards.values()
        ]
        if to_close:
            await asyncio.wait(to_close)

        await self.http.close()
        self.__queue.put_nowait(EventItem(EventType.clean_close, None, None))

    async def change_presence(
        self,
        *,
        activity: Optional[BaseActivity] = None,
        status: Optional[Status] = None,
        shard_id: Optional[int] = None,
    ) -> None:
        """|coro|

        Changes the client's presence.

        Example: ::

            game = nextcord.Game("with the API")
            await client.change_presence(status=nextcord.Status.idle, activity=game)

        .. versionchanged:: 2.0
            Removed the ``afk`` keyword-only parameter.

        Parameters
        ----------
        activity: Optional[:class:`BaseActivity`]
            The activity being done. ``None`` if no currently active activity is done.
        status: Optional[:class:`Status`]
            Indicates what status to change to. If ``None``, then
            :attr:`Status.online` is used.
        shard_id: Optional[:class:`int`]
            The shard_id to change the presence to. If not specified
            or ``None``, then it will change the presence of every
            shard the bot can see.

        Raises
        ------
        InvalidArgument
            If the ``activity`` parameter is not of proper type.
        """

        if status is None:
            status_value = "online"
            status_enum = Status.online
        elif status is Status.offline:
            status_value = "invisible"
            status_enum = Status.offline
        else:
            status_enum = status
            status_value = str(status)

        if shard_id is None:
            for shard in self.__shards.values():
                await shard.ws.change_presence(activity=activity, status=status_value)

            guilds = self._connection.guilds
        else:
            shard = self.__shards[shard_id]
            await shard.ws.change_presence(activity=activity, status=status_value)
            guilds = [g for g in self._connection.guilds if g.shard_id == shard_id]

        activities = () if activity is None else (activity,)
        for guild in guilds:
            me = guild.me
            if me is None:  # type: ignore
                continue

            # Member.activities is typehinted as Tuple[ActivityType, ...], we may be setting it as Tuple[BaseActivity, ...]
            me.activities = activities  # type: ignore
            me.status = status_enum

    def is_ws_ratelimited(self) -> bool:
        """:class:`bool`: Whether the websocket is currently rate limited.

        This can be useful to know when deciding whether you should query members
        using HTTP or via the gateway.

        This implementation checks if any of the shards are rate limited.
        For more granular control, consider :meth:`ShardInfo.is_ws_ratelimited`.

        .. versionadded:: 1.6
        """
        return any(shard.ws.is_ratelimited() for shard in self.__shards.values())
