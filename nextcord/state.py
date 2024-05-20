# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
import contextlib
import copy
import inspect
import itertools
import logging
import os
import warnings
from collections import OrderedDict, deque
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Deque,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from . import utils
from .activity import BaseActivity
from .application_command import BaseApplicationCommand
from .audit_logs import AuditLogEntry
from .auto_moderation import AutoModerationActionExecution, AutoModerationRule
from .channel import *
from .channel import _channel_factory
from .emoji import Emoji
from .enums import ChannelType, Status, try_enum
from .errors import Forbidden
from .flags import ApplicationFlags, Intents, MemberCacheFlags
from .guild import Guild
from .integrations import _integration_factory
from .invite import Invite
from .member import Member
from .mentions import AllowedMentions
from .message import Message
from .object import Object
from .partial_emoji import PartialEmoji
from .raw_models import *
from .role import Role
from .scheduled_events import ScheduledEvent, ScheduledEventUser
from .soundboard import PartialSoundboardSound, SoundboardSound
from .stage_instance import StageInstance
from .sticker import GuildSticker
from .threads import Thread, ThreadMember
from .ui.modal import Modal, ModalStore
from .ui.view import View, ViewStore
from .user import ClientUser, User
from .voice_channel_effect import VoiceChannelEffect

if TYPE_CHECKING:
    from asyncio import Future

    from .abc import MessageableChannel, PrivateChannel
    from .application_command import SlashApplicationSubcommand
    from .client import Client
    from .gateway import DiscordWebSocket
    from .guild import GuildChannel, VocalGuildChannel
    from .http import HTTPClient
    from .types.activity import Activity as ActivityPayload
    from .types.channel import DMChannel as DMChannelPayload
    from .types.emoji import Emoji as EmojiPayload
    from .types.guild import Guild as GuildPayload
    from .types.interactions import ApplicationCommand as ApplicationCommandPayload
    from .types.message import Message as MessagePayload
    from .types.scheduled_events import ScheduledEvent as ScheduledEventPayload
    from .types.soundboard import SoundboardSound as SoundboardSoundPayload
    from .types.sticker import GuildSticker as GuildStickerPayload
    from .types.user import PartialUser as PartialUserPayload, User as UserPayload
    from .types.voice import VoiceChannelEffectSend as VoiceChannelEffectSendPayload
    from .voice_client import VoiceProtocol

    T = TypeVar("T")
    CS = TypeVar("CS", bound="ConnectionState")
    Channel = Union[GuildChannel, VocalGuildChannel, PrivateChannel, PartialMessageable]


MISSING = utils.MISSING


class ChunkRequest:
    def __init__(
        self,
        guild_id: int,
        loop: asyncio.AbstractEventLoop,
        resolver: Callable[[int], Any],
        *,
        cache: bool = True,
    ) -> None:
        self.guild_id: int = guild_id
        self.resolver: Callable[[int], Any] = resolver
        self.loop: asyncio.AbstractEventLoop = loop
        self.cache: bool = cache
        self.nonce: str = os.urandom(16).hex()
        self.buffer: List[Member] = []
        self.waiters: List[asyncio.Future[List[Member]]] = []

    def add_members(self, members: List[Member]) -> None:
        self.buffer.extend(members)
        if self.cache:
            guild = self.resolver(self.guild_id)
            if guild is None:
                return

            for member in members:
                existing = guild.get_member(member.id)
                if existing is None or existing.joined_at is None:
                    guild._add_member(member)

    async def wait(self) -> List[Member]:
        future = self.loop.create_future()
        self.waiters.append(future)
        try:
            return await future
        finally:
            self.waiters.remove(future)

    def get_future(self) -> asyncio.Future[List[Member]]:
        future = self.loop.create_future()
        self.waiters.append(future)
        return future

    def done(self) -> None:
        for future in self.waiters:
            if not future.done():
                future.set_result(self.buffer)


_log = logging.getLogger(__name__)


async def logging_coroutine(coroutine: Coroutine[Any, Any, T], *, info: str) -> Optional[T]:
    try:
        await coroutine
    except Exception:
        _log.exception("Exception occurred during %s", info)


class ConnectionState:
    if TYPE_CHECKING:
        _get_websocket: Callable[..., DiscordWebSocket]
        _get_client: Callable[..., Client]
        _parsers: Dict[str, Callable[[Dict[str, Any]], None]]

    def __init__(
        self,
        *,
        dispatch: Callable,
        handlers: Dict[str, Callable],
        hooks: Dict[str, Callable],
        http: HTTPClient,
        loop: asyncio.AbstractEventLoop,
        max_messages: Optional[int] = 1000,
        application_id: Optional[int] = None,
        heartbeat_timeout: float = 60.0,
        guild_ready_timeout: float = 2.0,
        allowed_mentions: Optional[AllowedMentions] = None,
        activity: Optional[BaseActivity] = None,
        status: Optional[Status] = None,
        intents: Intents = Intents.default(),
        chunk_guilds_at_startup: bool = MISSING,
        member_cache_flags: MemberCacheFlags = MISSING,
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = loop
        self.http: HTTPClient = http
        self.max_messages: Optional[int] = max_messages
        if self.max_messages is not None and self.max_messages <= 0:
            self.max_messages = 1000

        self.dispatch: Callable = dispatch
        self.handlers: Dict[str, Callable] = handlers
        self.hooks: Dict[str, Callable] = hooks
        self.shard_count: Optional[int] = None
        self._ready_task: Optional[asyncio.Task] = None
        self.application_id: Optional[int] = application_id
        self.heartbeat_timeout: float = heartbeat_timeout
        self.guild_ready_timeout: float = guild_ready_timeout
        if self.guild_ready_timeout < 0:
            raise ValueError("guild_ready_timeout cannot be negative")

        if allowed_mentions is not None and not isinstance(allowed_mentions, AllowedMentions):
            raise TypeError("allowed_mentions parameter must be AllowedMentions")

        self.allowed_mentions: Optional[AllowedMentions] = allowed_mentions
        self._chunk_requests: Dict[Union[int, str], ChunkRequest] = {}
        self._chunk_tasks: Dict[Union[int, str], asyncio.Task[None]] = {}
        self._background_tasks: Set[asyncio.Task] = set()

        if activity is not None:
            if not isinstance(activity, BaseActivity):
                raise TypeError("activity parameter must derive from BaseActivity.")

            raw_activity = activity.to_dict()
        else:
            raw_activity = activity

        raw_status = ("invisible" if status is Status.offline else str(status)) if status else None

        if not isinstance(intents, Intents):
            raise TypeError(f"intents parameter must be Intent not {type(intents)!r}")

        if not intents.guilds:
            _log.warning("Guilds intent seems to be disabled. This may cause state related issues.")

        if chunk_guilds_at_startup is MISSING:
            chunk_guilds_at_startup = intents.members

        self._chunk_guilds: bool = chunk_guilds_at_startup

        # Ensure these two are set properly
        if not intents.members and self._chunk_guilds:
            raise ValueError("Intents.members must be enabled to chunk guilds at startup.")

        if member_cache_flags is MISSING:
            member_cache_flags = MemberCacheFlags.from_intents(intents)
        else:
            if not isinstance(member_cache_flags, MemberCacheFlags):
                raise TypeError(
                    "member_cache_flags parameter must be MemberCacheFlags "
                    f"not {type(member_cache_flags)!r}"
                )

            member_cache_flags._verify_intents(intents)

        self.member_cache_flags: MemberCacheFlags = member_cache_flags
        self._activity: Optional[ActivityPayload] = raw_activity
        self._status: Optional[str] = raw_status
        self._intents: Intents = intents
        # A set of all application command objects available. Set because duplicates should not exist.
        self._application_commands: Set[BaseApplicationCommand] = set()
        # A dictionary of all available unique command signatures. Compiled at runtime because needing to iterate
        # through all application commands would take far more time. If memory is problematic, perhaps this can go?
        self._application_command_signatures: Dict[
            Tuple[Optional[str], int, Optional[int]], BaseApplicationCommand
        ] = {}
        # A dictionary of Discord Application Command ID's and the ApplicationCommand object they correspond to.
        self._application_command_ids: Dict[int, BaseApplicationCommand] = {}

        if not intents.members or member_cache_flags._empty:
            self.store_user = self.create_user
            self.deref_user = self.deref_user_no_intents

        self.parsers = parsers = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith("parse_"):
                parsers[attr[6:].upper()] = func

        self.clear()

    def clear(self, *, views: bool = True, modals: bool = True) -> None:
        self.user: Optional[ClientUser] = None
        # Originally, this code used WeakValueDictionary to maintain references to the
        # global user mapping.

        # However, profiling showed that this came with two cons:

        # 1. The __weakref__ slot caused a non-trivial increase in memory
        # 2. The performance of the mapping caused store_user to be a bottleneck.

        # Since this is undesirable, a mapping is now used instead with stored
        # references now using a regular dictionary with eviction being done
        # using __del__. Testing this for memory leaks led to no discernible leaks,
        # though more testing will have to be done.
        self._users: Dict[int, User] = {}
        self._emojis: Dict[int, Emoji] = {}
        self._stickers: Dict[int, GuildSticker] = {}
        self._guilds: Dict[int, Guild] = {}
        self._soundboard_sounds: Dict[int, SoundboardSound] = {}
        # TODO: Why aren't the above and stuff below application_commands declared in __init__?
        self._application_commands = set()
        # Thought about making these two weakref.WeakValueDictionary's, but the bot could theoretically be holding on
        # to them in a dev-defined, which would desync the bot from itself.
        self._application_command_signatures = {}
        self._application_command_ids = {}
        if views:
            self._view_store: ViewStore = ViewStore(self)
        if modals:
            self._modal_store: ModalStore = ModalStore(self)

        self._voice_clients: Dict[int, VoiceProtocol] = {}

        # LRU of max size 128
        self._private_channels: OrderedDict[int, PrivateChannel] = OrderedDict()
        # extra dict to look up private channels by user id
        self._private_channels_by_user: Dict[int, DMChannel] = {}
        if self.max_messages is not None:
            self._messages: Optional[Deque[Message]] = deque(maxlen=self.max_messages)
        else:
            self._messages: Optional[Deque[Message]] = None

    def process_chunk_requests(
        self, guild_id: int, nonce: Optional[str], members: List[Member], complete: bool
    ) -> None:
        removed = []
        for key, request in self._chunk_requests.items():
            if request.guild_id == guild_id and request.nonce == nonce:
                request.add_members(members)
                if complete:
                    request.done()
                    removed.append(key)

        for key in removed:
            del self._chunk_requests[key]

    def call_handlers(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            func = self.handlers[key]
        except KeyError:
            pass
        else:
            func(*args, **kwargs)

    async def call_hooks(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            coro = self.hooks[key]
        except KeyError:
            pass
        else:
            await coro(*args, **kwargs)

    @property
    def self_id(self) -> Optional[int]:
        u = self.user
        return u.id if u else None

    @property
    def intents(self) -> Intents:
        ret = Intents.none()
        ret.value = self._intents.value
        return ret

    @property
    def voice_clients(self) -> List[VoiceProtocol]:
        return list(self._voice_clients.values())

    def _get_voice_client(self, guild_id: Optional[int]) -> Optional[VoiceProtocol]:
        # the keys of self._voice_clients are ints
        return self._voice_clients.get(guild_id)  # type: ignore

    def _add_voice_client(self, guild_id: int, voice: VoiceProtocol) -> None:
        self._voice_clients[guild_id] = voice

    def _remove_voice_client(self, guild_id: int) -> None:
        self._voice_clients.pop(guild_id, None)

    def _update_references(self, ws: DiscordWebSocket) -> None:
        for vc in self.voice_clients:
            vc.main_ws = ws  # type: ignore

    def store_user(self, data: UserPayload) -> User:
        user_id = int(data["id"])
        try:
            return self._users[user_id]
        except KeyError:
            user = User(state=self, data=data)
            if user.discriminator != "0000":
                self._users[user_id] = user
                user._stored = True
            return user

    def deref_user(self, user_id: int) -> None:
        self._users.pop(user_id, None)

    def create_user(self, data: Union[PartialUserPayload, UserPayload]) -> User:
        return User(state=self, data=data)

    def deref_user_no_intents(self, user_id: int) -> None:
        return

    def get_user(self, id: Optional[int]) -> Optional[User]:
        # the keys of self._users are ints
        return self._users.get(id)  # type: ignore

    def store_emoji(self, guild: Guild, data: EmojiPayload) -> Emoji:
        # the id will be present here
        emoji_id = int(data["id"])  # type: ignore
        self._emojis[emoji_id] = emoji = Emoji(guild=guild, state=self, data=data)
        return emoji

    def store_sticker(self, guild: Guild, data: GuildStickerPayload) -> GuildSticker:
        sticker_id = int(data["id"])
        self._stickers[sticker_id] = sticker = GuildSticker(state=self, data=data)
        return sticker

    def store_soundboard_sound(
        self, guild: Optional[Guild], data: SoundboardSoundPayload
    ) -> SoundboardSound:
        sound = SoundboardSound(data=data, guild=guild, state=self)
        self._soundboard_sounds[sound.id] = sound
        return sound

    def store_view(self, view: View, message_id: Optional[int] = None) -> None:
        self._view_store.add_view(view, message_id)

    def store_modal(self, modal: Modal, user_id: Optional[int] = None) -> None:
        self._modal_store.add_modal(modal, user_id)

    def remove_view(self, view: View, message_id: Optional[int] = None) -> None:
        self._view_store.remove_view(view, message_id)

    def remove_modal(self, modal: Modal) -> None:
        self._modal_store.remove_modal(modal)

    def prevent_view_updates_for(self, message_id: Optional[int]) -> Optional[View]:
        return self._view_store.remove_message_tracking(message_id)  # type: ignore

    def all_views(self) -> List[View]:
        return self._view_store.all_views()

    def views(self, persistent: bool = True) -> List[View]:
        return self._view_store.views(persistent)

    @property
    def guilds(self) -> List[Guild]:
        return list(self._guilds.values())

    def _get_guild(self, guild_id: Optional[int]) -> Optional[Guild]:
        # the keys of self._guilds are ints
        return self._guilds.get(guild_id)  # type: ignore

    def _add_guild(self, guild: Guild) -> None:
        self._guilds[guild.id] = guild

    def _remove_guild(self, guild: Guild) -> None:
        self._guilds.pop(guild.id, None)

        for emoji in guild.emojis:
            self._emojis.pop(emoji.id, None)

        for sticker in guild.stickers:
            self._stickers.pop(sticker.id, None)

        del guild

    @property
    def emojis(self) -> List[Emoji]:
        return list(self._emojis.values())

    @property
    def stickers(self) -> List[GuildSticker]:
        return list(self._stickers.values())

    def get_emoji(self, emoji_id: Optional[int]) -> Optional[Emoji]:
        # the keys of self._emojis are ints
        return self._emojis.get(emoji_id)  # type: ignore

    def get_sticker(self, sticker_id: Optional[int]) -> Optional[GuildSticker]:
        # the keys of self._stickers are ints
        return self._stickers.get(sticker_id)  # type: ignore

    def get_soundboard_sound(self, sound_id: Optional[int]) -> Optional[SoundboardSound]:
        # the keys of self._soundboard_sounds are ints
        return self._soundboard_sounds.get(sound_id)  # type: ignore

    @property
    def private_channels(self) -> List[PrivateChannel]:
        return list(self._private_channels.values())

    def _get_private_channel(self, channel_id: Optional[int]) -> Optional[PrivateChannel]:
        try:
            # the keys of self._private_channels are ints
            value = self._private_channels[channel_id]  # type: ignore
        except KeyError:
            return None
        else:
            self._private_channels.move_to_end(channel_id)  # type: ignore
            return value

    def _get_private_channel_by_user(self, user_id: Optional[int]) -> Optional[DMChannel]:
        # the keys of self._private_channels are ints
        return self._private_channels_by_user.get(user_id)  # type: ignore

    def _add_private_channel(self, channel: PrivateChannel) -> None:
        channel_id = channel.id
        self._private_channels[channel_id] = channel

        if len(self._private_channels) > 128:
            _, to_remove = self._private_channels.popitem(last=False)
            if isinstance(to_remove, DMChannel) and to_remove.recipient:
                self._private_channels_by_user.pop(to_remove.recipient.id, None)

        if isinstance(channel, DMChannel) and channel.recipient:
            self._private_channels_by_user[channel.recipient.id] = channel

    def add_dm_channel(self, data: DMChannelPayload) -> DMChannel:
        # self.user is *always* cached when this is called
        channel = DMChannel(me=self.user, state=self, data=data)  # type: ignore
        self._add_private_channel(channel)
        return channel

    def _remove_private_channel(self, channel: PrivateChannel) -> None:
        self._private_channels.pop(channel.id, None)
        if isinstance(channel, DMChannel):
            recipient = channel.recipient
            if recipient is not None:
                self._private_channels_by_user.pop(recipient.id, None)

    def _get_message(self, msg_id: Optional[int]) -> Optional[Message]:
        return (
            utils.find(lambda m: m.id == msg_id, reversed(self._messages))
            if self._messages
            else None
        )

    def _add_guild_from_data(self, data: GuildPayload) -> Guild:
        guild = Guild(data=data, state=self)
        self._add_guild(guild)
        return guild

    def _guild_needs_chunking(self, guild: Guild) -> bool:
        # If presences are enabled then we get back the old guild.large behaviour
        return (
            self._chunk_guilds
            and not guild.chunked
            and not (self._intents.presences and not guild.large)
        )

    def _get_guild_channel(
        self, data: MessagePayload
    ) -> Tuple[Union[Channel, Thread], Optional[Guild]]:
        channel_id = int(data["channel_id"])
        try:
            guild = self._get_guild(int(data["guild_id"]))
        except KeyError:
            channel = self.get_channel(channel_id)

            if channel is None:
                channel = DMChannel._from_message(self, channel_id)

            guild = getattr(channel, "guild", None)
        else:
            channel = guild and guild._resolve_channel(channel_id)

        return channel or PartialMessageable(state=self, id=channel_id), guild

    @property
    def application_commands(self) -> Set[BaseApplicationCommand]:
        """Gets a copy of the ApplicationCommand object set. If the original is given out and modified, massive desyncs
        may occur. This should be used internally as well if size-changed-during-iteration is a worry.
        """
        return self._application_commands.copy()

    def get_application_command(self, command_id: int) -> Optional[BaseApplicationCommand]:
        return self._application_command_ids.get(command_id, None)

    def get_application_command_from_signature(
        self,
        *,
        type: int,
        qualified_name: str,
        guild_id: Optional[int],
        search_localizations: bool = False,
    ) -> Optional[Union[BaseApplicationCommand, SlashApplicationSubcommand]]:
        def get_parent_command(name: str, /) -> Optional[BaseApplicationCommand]:
            found = self._application_command_signatures.get((name, type, guild_id))
            if not search_localizations:
                return found

            for command in self._application_command_signatures.values():
                if command.name_localizations and name in command.name_localizations.values():
                    found = command
                    break

            return found

        def find_children(
            parent: Union[BaseApplicationCommand, SlashApplicationSubcommand], name: str, /
        ) -> Optional[Union[BaseApplicationCommand, SlashApplicationSubcommand]]:
            children: Dict[str, SlashApplicationSubcommand] = getattr(parent, "children", {})
            if not children:
                return parent

            found = children.get(name)
            if not search_localizations:
                return found

            subcommand: Union[BaseApplicationCommand, SlashApplicationSubcommand]
            for subcommand in children.values():
                if subcommand.name_localizations and name in subcommand.name_localizations.values():
                    found = subcommand
                    break

            return found

        parent: Optional[Union[BaseApplicationCommand, SlashApplicationSubcommand]] = None

        if not qualified_name:
            return None

        if " " not in qualified_name:
            return get_parent_command(qualified_name)

        for command_name in qualified_name.split(" "):
            if parent is None:
                parent = get_parent_command(command_name)
            else:
                parent = find_children(parent, command_name)

        return parent

    def get_guild_application_commands(
        self, guild_id: Optional[int] = None, rollout: bool = False
    ) -> List[BaseApplicationCommand]:
        """Gets all commands that have the given guild ID. If guild_id is None, all guild commands are returned. if
        rollout is True, guild_ids_to_rollout is used.
        """
        return [
            app_cmd
            for app_cmd in self.application_commands
            if guild_id is None
            or guild_id in app_cmd.guild_ids
            or (rollout and guild_id in app_cmd.guild_ids_to_rollout)
        ]

    def get_global_application_commands(
        self, rollout: bool = False
    ) -> List[BaseApplicationCommand]:
        """Gets all commands that are registered globally. If rollout is True, is_global is used."""
        return [
            app_cmd
            for app_cmd in self.application_commands
            if (rollout and app_cmd.is_global) or None in app_cmd.command_ids
        ]

    def add_application_command(
        self,
        command: BaseApplicationCommand,
        *,
        overwrite: bool = False,
        use_rollout: bool = False,
        pre_remove: bool = True,
    ) -> None:
        """Adds the command to the state and updates the state with any changes made to the command.
        Removes all existing references, then adds them.
        Safe to call multiple times on the same application command.

        Parameters
        ----------
        command: :class:`BaseApplicationCommand`
            The command to add/update the state with.
        overwrite: :class:`bool`
            If the library will let you add a command that overlaps with an existing command. Default ``False``.
        use_rollout: :class:`bool`
            If the command should be added to the state with its rollout guild IDs.
        pre_remove: :class:`bool`
            If the command should be removed before adding it. This will clear all signatures from storage, including
            rollout ones.
        """
        if pre_remove:
            self.remove_application_command(command)
        signature_set = (
            command.get_rollout_signatures() if use_rollout else command.get_signatures()
        )
        for signature in signature_set:
            if not overwrite and (
                found_command := self._application_command_signatures.get(signature, None)
            ):
                if found_command is not command:
                    raise ValueError(
                        f"{command.error_name} You cannot add application commands with duplicate "
                        f"signatures."
                    )
                # No else because we do not care if the command has its own signature already in.
            else:
                self._application_command_signatures[signature] = command
        for command_id in command.command_ids.values():
            # PyCharm flags found_command as it "might be referenced before assignment", but that can't happen due to it
            #  being in an AND statement.
            # noinspection PyUnboundLocalVariable
            if (
                not overwrite
                and (found_command := self._application_command_ids.get(command_id, None))
                and found_command is not command
            ):
                raise ValueError(
                    f"{command.error_name} You cannot add application commands with duplicate IDs."
                )

            self._application_command_ids[command_id] = command
        # TODO: Add the command to guilds. Should it? Check if it does in the Guild add.
        self._application_commands.add(command)

    def remove_application_command(self, command: BaseApplicationCommand) -> None:
        """Removes the command and all signatures + associated IDs from the state.
        Safe to call with commands that aren't in the state.

        Parameters
        ----------
        command: :class:`BaseApplicationCommand`
            the command to remove from the state.
        """
        signature_set = command.get_rollout_signatures()
        for signature in signature_set:
            self._application_command_signatures.pop(signature, None)
        for cmd_id in command.command_ids.values():
            self._application_command_ids.pop(cmd_id, None)
        self._application_commands.discard(command)

    def add_all_rollout_signatures(self) -> None:
        """This adds all command signatures for rollouts to the signature cache."""
        for command in self._application_commands:
            self.add_application_command(command, use_rollout=True)

    async def sync_all_application_commands(
        self,
        data: Optional[Dict[Optional[int], List[ApplicationCommandPayload]]] = None,
        *,
        use_rollout: bool = True,
        associate_known: bool = True,
        delete_unknown: bool = True,
        update_known: bool = True,
        register_new: bool = True,
        ignore_forbidden: bool = True,
    ):
        """|coro|

        Syncs all application commands with Discord. Will sync global commands if any commands added are global, and
        syncs with all guilds that have an application command targeting them.

        This may call Discord many times depending on how different guilds you have local commands for, and how many
        commands Discord needs to be updated or added, which may cause your bot to be rate limited or even Cloudflare
        banned in VERY extreme cases.

        This may incur high CPU usage depending on how many commands you have and how complex they are, which may cause
        your bot to halt while it checks local commands against the existing commands that Discord has.

        For a more targeted version of this method, see :func:`Client.sync_application_commands`

        Parameters
        ----------
        data: Optional[Dict[Optional[:class:`int`], List[:class:`dict`]]]
            Data to use when comparing local application commands to what Discord has. The key should be the
            :class:`int` guild ID (`None` for global) corresponding to the value list of application command payloads
            from Discord. Any guild ID's not provided will be fetched if needed. Defaults to ``None``
        use_rollout: :class:`bool`
            If the rollout guild IDs of commands should be used. Defaults to ``True``
        associate_known: :class:`bool`
            If local commands that match a command already on Discord should be associated with each other.
            Defaults to ``True``
        delete_unknown: :class:`bool`
            If commands on Discord that don't match a local command should be deleted. Defaults to ``True``.
        update_known: :class:`bool`
            If commands on Discord have a basic match with a local command, but don't fully match, should be updated.
            Defaults to ``True``
        register_new: :class:`bool`
            If a local command that doesn't have a basic match on Discord should be added to Discord.
            Defaults to ``True``
        ignore_forbidden: :class:`bool`
            If this command should raise an :class:`errors.Forbidden` exception when the bot encounters a guild where
            it doesn't have permissions to view application commands.
            Defaults to ``True``
        """
        _log.debug("Beginning sync of all application commands.")
        self._get_client().add_all_application_commands()
        data = {} if data is None else data.copy()

        if self.application_id is None:
            raise TypeError("Could not get the current application's id")

        for app_cmd in self.application_commands:
            self.add_application_command(command=app_cmd, use_rollout=use_rollout)

            if app_cmd.is_global and None not in data:
                data[None] = await self.http.get_global_commands(self.application_id)
                _log.debug("Fetched global application command data.")

            if app_cmd.is_guild:
                for guild_id in app_cmd.guild_ids_to_rollout if use_rollout else app_cmd.guild_ids:
                    if guild_id not in data:
                        try:
                            data[guild_id] = await self.http.get_guild_commands(
                                self.application_id, guild_id
                            )
                            _log.debug(
                                "Fetched guild application command data for guild ID %s", guild_id
                            )
                        except Forbidden as e:
                            if ignore_forbidden:
                                _log.warning(
                                    "nextcord.Client: Forbidden error for %s, is the applications.commands "
                                    "Oauth scope enabled? %s",
                                    guild_id,
                                    e,
                                )
                            else:
                                raise e

        for guild_id in data:
            _log.debug("Running sync for %s", "global" if guild_id is None else f"Guild {guild_id}")
            await self.sync_application_commands(
                data=data[guild_id],
                guild_id=guild_id,
                associate_known=associate_known,
                delete_unknown=delete_unknown,
                update_known=update_known,
                register_new=register_new,
            )

    async def sync_application_commands(
        self,
        data: Optional[List[ApplicationCommandPayload]] = None,
        guild_id: Optional[int] = None,
        associate_known: bool = True,
        delete_unknown: bool = True,
        update_known: bool = True,
        register_new: bool = True,
    ) -> None:
        """|coro|
        Syncs the locally added application commands with the Guild corresponding to the given ID, or syncs
        global commands if the guild_id is ``None``.

        Parameters
        ----------
        data: Optional[List[:class:`dict`]]
            Data to use when comparing local application commands to what Discord has. Should be a list of application
            command data from Discord. If left as ``None``, it will be fetched if needed. Defaults to ``None``.
        guild_id: Optional[:class:`int`]
            ID of the guild to sync application commands with. If set to ``None``, global commands will be synced instead.
            Defaults to ``None``.
        associate_known: :class:`bool`
            If local commands that match a command already on Discord should be associated with each other.
            Defaults to ``True``.
        delete_unknown: :class:`bool`
            If commands on Discord that don't match a local command should be deleted. Defaults to ``True``.
        update_known: :class:`bool`
            If commands on Discord have a basic match with a local command, but don't fully match, should be updated.
            Defaults to ``True``.
        register_new: :class:`bool`
            If a local command that doesn't have a basic match on Discord should be added to Discord.
            Defaults to ``True``.

        """
        _log.debug("Syncing commands to %s", guild_id)

        if self.application_id is None:
            raise TypeError("Could not get the current application's id")

        if not data:
            if guild_id:
                data = await self.http.get_guild_commands(self.application_id, guild_id)
            else:
                data = await self.http.get_global_commands(self.application_id)

        await self.discover_application_commands(
            data=data,
            guild_id=guild_id,
            associate_known=associate_known,
            delete_unknown=delete_unknown,
            update_known=update_known,
        )
        if register_new:
            await self.register_new_application_commands(data=data, guild_id=guild_id)

        _log.debug("Command sync with Guild %s finished.", guild_id)

    async def discover_application_commands(
        self,
        data: Optional[List[ApplicationCommandPayload]] = None,
        guild_id: Optional[int] = None,
        associate_known: bool = True,
        delete_unknown: bool = True,
        update_known: bool = True,
    ) -> None:
        """|coro|
        Associates existing, deletes unknown, and updates modified commands for either global commands or a specific
        guild. This does a deep check on found commands, which may be expensive CPU-wise.

        Running this for global or the same guild multiple times at once may cause unexpected or unstable behavior.

        Parameters
        ----------
        data: Optional[List[:class:`dict]]
            Payload from ``HTTPClient.get_guild_commands`` or ``HTTPClient.get_global_commands`` to deploy with. If None,
            the payload will be retrieved from Discord.
        guild_id: Optional[:class:`int`]
            Guild ID to deploy application commands to. If ``None``, global commands are deployed to.
        associate_known: :class:`bool`
            If True, commands on Discord that pass a signature check and a deep check will be associated with locally
            added ApplicationCommand objects.
        delete_unknown: :class:`bool`
            If ``True``, commands on Discord that fail a signature check will be removed. If ``update_known`` is False,
            commands that pass the signature check but fail the deep check will also be removed.
        update_known: :class:`bool`
            If ``True``, commands on Discord that pass a signature check but fail the deep check will be updated.
        """
        if not associate_known and not delete_unknown and not update_known:
            # If everything is disabled, there is no point in doing anything.
            return

        if self.application_id is None:
            raise NotImplementedError("Could not get the current application id")

        if not data:
            if guild_id:
                # we do not care about typeddict specificity here
                data = await self.http.get_guild_commands(self.application_id, guild_id)
            else:
                data = await self.http.get_global_commands(self.application_id)

        for raw_response in data:
            payload_type = raw_response["type"] if "type" in raw_response else 1
            fixed_guild_id = raw_response.get("guild_id", None)

            response_signature = {
                "type": int(payload_type),
                "qualified_name": raw_response["name"],
                "guild_id": None if not fixed_guild_id else int(fixed_guild_id),
            }
            app_cmd = self.get_application_command_from_signature(**response_signature)
            if app_cmd:
                if not isinstance(app_cmd, BaseApplicationCommand):
                    raise ValueError(
                        (
                            f".get_application_command_from_signature with kwargs: {response_signature} "
                            f"returned {type(app_cmd)} but BaseApplicationCommand was expected."
                        )
                    )

                if app_cmd.is_payload_valid(raw_response, guild_id):
                    if associate_known:
                        _log.debug(
                            "nextcord.ConnectionState: Command with signature %s associated with added command.",
                            response_signature,
                        )
                        app_cmd.parse_discord_response(self, raw_response)
                        self.add_application_command(app_cmd, use_rollout=True)

                elif update_known:
                    _log.debug(
                        "nextcord.ConnectionState: Command with signature %s found but failed deep check, updating.",
                        response_signature,
                    )
                    await self.register_application_command(app_cmd, guild_id)
                elif delete_unknown:
                    _log.debug(
                        "nextcord.ConnectionState: Command with signature %s found but failed deep check, removing.",
                        response_signature,
                    )
                    # TODO: Re-examine how worthwhile this is.
                    await self.delete_application_command(app_cmd, guild_id)

            elif delete_unknown:
                _log.debug(
                    "nextcord.ConnectionState: Command with signature %s found but failed deep check, removing.",
                    response_signature,
                )
                if guild_id:
                    await self.http.delete_guild_command(
                        self.application_id, guild_id, raw_response["id"]
                    )
                else:
                    await self.http.delete_global_command(self.application_id, raw_response["id"])

    async def deploy_application_commands(
        self,
        data: Optional[List[ApplicationCommandPayload]] = None,
        *,
        guild_id: Optional[int] = None,
        associate_known: bool = True,
        delete_unknown: bool = True,
        update_known: bool = True,
    ) -> None:
        warnings.warn(
            ".deploy_application_commands is deprecated, use .discover_application_commands instead.",
            stacklevel=2,
            category=FutureWarning,
        )
        await self.discover_application_commands(
            data=data,
            guild_id=guild_id,
            associate_known=associate_known,
            delete_unknown=delete_unknown,
            update_known=update_known,
        )

    async def associate_application_commands(
        self, data: Optional[List[ApplicationCommandPayload]] = None, guild_id: Optional[int] = None
    ) -> None:
        warnings.warn(
            ".associate_application_commands is deprecated, use .deploy_application_commands and set "
            "kwargs in it instead.",
            stacklevel=2,
            category=FutureWarning,
        )
        await self.deploy_application_commands(
            data=data,
            guild_id=guild_id,
            associate_known=True,
            delete_unknown=False,
            update_known=False,
        )

    async def delete_unknown_application_commands(
        self, data: Optional[List[ApplicationCommandPayload]] = None, guild_id: Optional[int] = None
    ) -> None:
        warnings.warn(
            ".delete_unknown_application_commands is deprecated, use .deploy_application_commands and set "
            "kwargs in it instead.",
            stacklevel=2,
            category=FutureWarning,
        )
        await self.deploy_application_commands(
            data=data,
            guild_id=guild_id,
            associate_known=False,
            delete_unknown=True,
            update_known=False,
        )

    async def update_application_commands(
        self, data: Optional[List[ApplicationCommandPayload]] = None, guild_id: Optional[int] = None
    ) -> None:
        warnings.warn(
            ".update_application_commands is deprecated, use .deploy_application_commands and set "
            "kwargs in it instead.",
            stacklevel=2,
            category=FutureWarning,
        )
        await self.deploy_application_commands(
            data=data,
            guild_id=guild_id,
            associate_known=False,
            delete_unknown=False,
            update_known=True,
        )

    async def register_new_application_commands(
        self, data: Optional[List[ApplicationCommandPayload]] = None, guild_id: Optional[int] = None
    ) -> None:
        """|coro|
        Registers locally added application commands that don't match a signature that Discord has registered for
        either global commands or a specific guild.

        Parameters
        ----------
        data: Optional[List[:class:`dict`]]
            Data to use when comparing local application commands to what Discord has. Should be a list of application
            command data from Discord. If left as ``None``, it will be fetched if needed. Defaults to ``None``
        guild_id: Optional[:class:`int`]
            ID of the guild to sync application commands with. If set to ``None``, global commands will be synced instead.
            Defaults to ``None``.
        """
        if not data:
            if self.application_id is None:
                raise TypeError("Could not get the current application id")

            if guild_id:
                data = await self.http.get_guild_commands(self.application_id, guild_id)
            else:
                data = await self.http.get_global_commands(self.application_id)

        data_signatures = [
            (
                raw_response["name"],
                int(raw_response["type"] if "type" in raw_response else 1),
                int(temp) if (temp := raw_response.get("guild_id", None)) else temp,
            )
            for raw_response in data
        ]
        # add_application_command can change the size of the dictionary, and apparently .items() doesn't prevent that
        # "RuntimeError: dictionary changed size during iteration" from happening. So a copy is made for just this.
        for signature, app_cmd in self._application_command_signatures.copy().items():
            if (
                signature not in data_signatures and signature[2] == guild_id
            ):  # index 2 of the tuple is the guild ID.
                await self.register_application_command(app_cmd, guild_id)

    async def register_application_command(
        self, command: BaseApplicationCommand, guild_id: Optional[int] = None
    ) -> None:
        """|coro|
        Registers the given application command either for a specific guild or globally and adds the command to the bot.

        Parameters
        ----------
        command: :class:`BaseApplicationCommand`
            Application command to register.
        guild_id: Optional[:class:`int`]
            ID of the guild to register the application commands to. If set to ``None``, the commands will be registered
            as global commands instead. Defaults to ``None``.
        """
        payload: EditApplicationCommand = command.get_payload(guild_id)  # type: ignore
        _log.info(
            "nextcord.ConnectionState: Registering command with signature %s",
            command.get_signature(guild_id),
        )

        if self.application_id is None:
            raise TypeError("Could not get the current application's id")

        try:
            if guild_id:
                raw_response = await self.http.upsert_guild_command(
                    self.application_id, guild_id, payload
                )
            else:
                raw_response = await self.http.upsert_global_command(self.application_id, payload)

        except Exception as e:
            _log.error("Error registering command %s: %s", command.error_name, e)
            raise e
        command.parse_discord_response(self, raw_response)
        self.add_application_command(command, pre_remove=False)

    async def delete_application_command(
        self, command: BaseApplicationCommand, guild_id: Optional[int] = None
    ) -> None:
        """|coro|
        Deletes the given application from Discord for the given guild ID or globally, then removes the signature and
        command ID from the cache if possible.

        Parameters
        ----------
        command: :class:`ApplicationCommand`
            Application command to delete.
        guild_id: Optional[:class:`int`]
            Guild ID to delete the application commands from. If ``None``, the command is deleted from global.
        """
        if self.application_id is None:
            raise NotImplementedError("Could not get the current application id")

        try:
            if guild_id:
                await self.http.delete_guild_command(
                    self.application_id, guild_id, command.command_ids[guild_id]
                )
            else:
                await self.http.delete_global_command(
                    self.application_id, command.command_ids[guild_id]
                )

            self._application_command_ids.pop(command.command_ids[guild_id], None)
            self._application_command_signatures.pop(command.get_signature(guild_id), None)

        except KeyError as e:
            if guild_id:
                _log.error(
                    "Could not globally unregister command %s "
                    "as it is not registered in the provided guild.",
                    command.error_name,
                )
                raise KeyError(
                    "This command cannot be globally unregistered, "
                    "as it is not registered in the provided guild."
                ) from e

            _log.error(
                "Could not globally unregister command %s as it is not a global command.",
                command.error_name,
            )
            raise KeyError(
                "This command cannot be globally unregistered, as it is not a global command."
            ) from e

        except Exception as e:
            _log.error("Error unregistering command %s: %s", command.error_name, e)
            raise e

    # async def register_bulk_application_commands(self) -> None:
    #     # TODO: Using Bulk upsert seems to delete all commands
    #     # It might be good to keep this around as a reminder for future work. Bulk upsert seem to delete everything
    #     # that isn't part of that bulk upsert, for both global and guild commands. While useful, this will
    #     # update/overwrite existing commands, which may (needs testing) wipe out all permissions associated with those
    #     # commands. Look for an opportunity to use bulk upsert.
    #     raise NotImplementedError

    async def chunker(
        self,
        guild_id: int,
        query: str = "",
        limit: int = 0,
        presences: bool = False,
        *,
        nonce: Optional[str] = None,
    ) -> None:
        ws = self._get_websocket(guild_id)  # This is ignored upstream
        await ws.request_chunks(
            guild_id, query=query, limit=limit, presences=presences, nonce=nonce
        )

    async def query_members(
        self,
        guild: Guild,
        query: Optional[str],
        limit: int,
        user_ids: Optional[List[int]],
        cache: bool,
        presences: bool,
    ) -> List[Member]:
        guild_id = guild.id
        ws = self._get_websocket(guild_id)
        if ws is None:  # pyright: ignore[reportUnnecessaryComparison]
            raise RuntimeError("Somehow do not have a websocket for this guild_id")

        request = ChunkRequest(guild.id, self.loop, self._get_guild, cache=cache)
        self._chunk_requests[request.nonce] = request

        try:
            # start the query operation
            await ws.request_chunks(
                guild_id,
                query=query,
                limit=limit,
                user_ids=user_ids,
                presences=presences,
                nonce=request.nonce,
            )
            return await asyncio.wait_for(request.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            _log.warning(
                "Timed out waiting for chunks with query %r and limit %d for guild_id %d",
                query,
                limit,
                guild_id,
            )
            raise

    async def _delay_ready(self) -> None:
        try:
            states = []
            while True:
                # this snippet of code is basically waiting N seconds
                # until the last GUILD_CREATE was sent
                try:
                    guild = await asyncio.wait_for(
                        self._ready_state.get(), timeout=self.guild_ready_timeout
                    )
                except asyncio.TimeoutError:
                    break
                else:
                    if self._guild_needs_chunking(guild):
                        future = await self.chunk_guild(guild, wait=False)
                        states.append((guild, future))
                    elif guild.unavailable is False:
                        self.dispatch("guild_available", guild)
                    else:
                        self.dispatch("guild_join", guild)

            for guild, future in states:
                try:
                    await asyncio.wait_for(future, timeout=5.0)
                except asyncio.TimeoutError:
                    _log.warning(
                        "Shard ID %s timed out waiting for chunks for guild_id %s.",
                        guild.shard_id,
                        guild.id,
                    )

                if guild.unavailable is False:
                    self.dispatch("guild_available", guild)
                else:
                    self.dispatch("guild_join", guild)

            # remove the state
            # AttributeError: already been deleted somehow
            with contextlib.suppress(AttributeError):
                del self._ready_state

        except asyncio.CancelledError:
            pass
        else:
            # dispatch the event
            self.call_handlers("ready")
            self.dispatch("ready")
        finally:
            self._ready_task = None

    def parse_ready(self, data) -> None:
        if self._ready_task is not None:
            self._ready_task.cancel()

        self._ready_state = asyncio.Queue()
        self.clear(views=False)
        self.user = ClientUser(state=self, data=data["user"])
        self.store_user(data["user"])

        if self.application_id is None:
            try:
                application = data["application"]
            except KeyError:
                pass
            else:
                self.application_id = utils.get_as_snowflake(application, "id")
                # flags will always be present here
                self.application_flags = ApplicationFlags._from_value(application["flags"])

        for guild_data in data["guilds"]:
            self._add_guild_from_data(guild_data)

        self.dispatch("connect")
        self._ready_task = asyncio.create_task(self._delay_ready())

    def parse_resumed(self, data) -> None:
        self.dispatch("resumed")

    def parse_message_create(self, data) -> None:
        channel, _ = self._get_guild_channel(data)
        # channel would be the correct type here
        message = Message(channel=channel, data=data, state=self)  # type: ignore
        self.dispatch("message", message)
        if self._messages is not None:
            self._messages.append(message)
        # we ensure that the channel is either a TextChannel, ForumChannel, Thread or VoiceChannel
        if channel and channel.__class__ in (TextChannel, ForumChannel, Thread, VoiceChannel):
            channel.last_message_id = message.id  # type: ignore

    def parse_message_delete(self, data) -> None:
        raw = RawMessageDeleteEvent(data)
        found = self._get_message(raw.message_id)
        raw.cached_message = found
        self.dispatch("raw_message_delete", raw)
        if self._messages is not None and found is not None:
            self.dispatch("message_delete", found)
            self._messages.remove(found)

    def parse_message_delete_bulk(self, data) -> None:
        raw = RawBulkMessageDeleteEvent(data)
        if self._messages:
            found_messages = [
                message for message in self._messages if message.id in raw.message_ids
            ]
        else:
            found_messages = []
        raw.cached_messages = found_messages
        self.dispatch("raw_bulk_message_delete", raw)
        if found_messages:
            self.dispatch("bulk_message_delete", found_messages)
            for msg in found_messages:
                # self._messages won't be None here
                self._messages.remove(msg)  # type: ignore

    def parse_message_update(self, data) -> None:
        raw = RawMessageUpdateEvent(data)
        message = self._get_message(raw.message_id)
        if message is not None:
            older_message = copy.copy(message)
            raw.cached_message = older_message
            self.dispatch("raw_message_edit", raw)
            message._update(data)
            # Coerce the `after` parameter to take the new updated Member
            # ref: #5999
            older_message.author = message.author
            self.dispatch("message_edit", older_message, message)
        else:
            self.dispatch("raw_message_edit", raw)

        if "components" in data and self._view_store.is_message_tracked(raw.message_id):
            self._view_store.update_from_message(raw.message_id, data["components"])

    def parse_message_reaction_add(self, data) -> None:
        emoji = data["emoji"]
        emoji_id = utils.get_as_snowflake(emoji, "id")
        emoji = PartialEmoji.with_state(
            self, id=emoji_id, animated=emoji.get("animated", False), name=emoji["name"]
        )
        raw = RawReactionActionEvent(data, emoji, "REACTION_ADD")

        member_data = data.get("member")
        if member_data:
            guild = self._get_guild(raw.guild_id)
            if guild is not None:
                raw.member = Member(data=member_data, guild=guild, state=self)
            else:
                raw.member = None
        else:
            raw.member = None
        self.dispatch("raw_reaction_add", raw)

        # rich interface here
        message = self._get_message(raw.message_id)
        if message is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            reaction = message._add_reaction(data, emoji, raw.user_id)
            user = raw.member or self._get_reaction_user(message.channel, raw.user_id)

            if user:
                self.dispatch("reaction_add", reaction, user)

    def parse_message_reaction_remove_all(self, data) -> None:
        raw = RawReactionClearEvent(data)
        self.dispatch("raw_reaction_clear", raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            old_reactions = message.reactions.copy()
            message.reactions.clear()
            self.dispatch("reaction_clear", message, old_reactions)

    def parse_message_reaction_remove(self, data) -> None:
        emoji = data["emoji"]
        emoji_id = utils.get_as_snowflake(emoji, "id")
        emoji = PartialEmoji.with_state(self, id=emoji_id, name=emoji["name"])
        raw = RawReactionActionEvent(data, emoji, "REACTION_REMOVE")
        self.dispatch("raw_reaction_remove", raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            try:
                reaction = message._remove_reaction(data, emoji, raw.user_id)
            except (AttributeError, ValueError):  # eventual consistency lol
                pass
            else:
                user = self._get_reaction_user(message.channel, raw.user_id)
                if user:
                    self.dispatch("reaction_remove", reaction, user)

    def parse_message_reaction_remove_emoji(self, data) -> None:
        emoji = data["emoji"]
        emoji_id = utils.get_as_snowflake(emoji, "id")
        emoji = PartialEmoji.with_state(self, id=emoji_id, name=emoji["name"])
        raw = RawReactionClearEmojiEvent(data, emoji)
        self.dispatch("raw_reaction_clear_emoji", raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            try:
                reaction = message._clear_emoji(emoji)
            except (AttributeError, ValueError):  # eventual consistency lol
                pass
            else:
                if reaction:
                    self.dispatch("reaction_clear_emoji", reaction)

    def parse_interaction_create(self, data) -> None:
        interaction = self._get_client().get_interaction(data=data)
        if data["type"] == 3:  # interaction component
            custom_id = interaction.data["custom_id"]  # type: ignore
            component_type = interaction.data["component_type"]  # type: ignore
            self._view_store.dispatch(component_type, custom_id, interaction)
        if data["type"] == 5:  # modal submit
            custom_id = interaction.data["custom_id"]  # type: ignore
            # key exists if type is 5 etc
            self._modal_store.dispatch(custom_id, interaction)

        self.dispatch("interaction", interaction)

    def parse_presence_update(self, data) -> None:
        guild_id = utils.get_as_snowflake(data, "guild_id")
        # guild_id won't be None here
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug("PRESENCE_UPDATE referencing an unknown guild ID: %s. Discarding.", guild_id)
            return

        user = data["user"]
        member_id = int(user["id"])
        member = guild.get_member(member_id)
        if member is None:
            _log.debug(
                "PRESENCE_UPDATE referencing an unknown member ID: %s. Discarding", member_id
            )
            return

        old_member = Member._copy(member)
        user_update = member._presence_update(data=data, user=user)
        if user_update:
            self.dispatch("user_update", user_update[0], user_update[1])

        self.dispatch("presence_update", old_member, member)

    def parse_user_update(self, data) -> None:
        # self.user is *always* cached when this is called
        user: ClientUser = self.user  # type: ignore
        user._update(data)
        ref = self._users.get(user.id)
        if ref:
            ref._update(data)

    def parse_invite_create(self, data) -> None:
        invite = Invite.from_gateway(state=self, data=data)
        self.dispatch("invite_create", invite)

    def parse_invite_delete(self, data) -> None:
        invite = Invite.from_gateway(state=self, data=data)
        self.dispatch("invite_delete", invite)

    def parse_channel_delete(self, data) -> None:
        guild = self._get_guild(utils.get_as_snowflake(data, "guild_id"))
        channel_id = int(data["id"])
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                guild._remove_channel(channel)
                self.dispatch("guild_channel_delete", channel)

    def parse_channel_update(self, data) -> None:
        channel_type = try_enum(ChannelType, data.get("type"))
        channel_id = int(data["id"])
        if channel_type is ChannelType.group:
            channel = self._get_private_channel(channel_id)
            old_channel = copy.copy(channel)
            # the channel is a GroupChannel
            channel._update_group(data)  # type: ignore
            self.dispatch("private_channel_update", old_channel, channel)
            return

        guild_id = utils.get_as_snowflake(data, "guild_id")
        guild = self._get_guild(guild_id)
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                old_channel = copy.copy(channel)
                channel._update(guild, data)
                self.dispatch("guild_channel_update", old_channel, channel)
            else:
                _log.debug(
                    "CHANNEL_UPDATE referencing an unknown channel ID: %s. Discarding.", channel_id
                )
        else:
            _log.debug("CHANNEL_UPDATE referencing an unknown guild ID: %s. Discarding.", guild_id)

    def parse_channel_create(self, data) -> None:
        factory, _ = _channel_factory(data["type"])
        if factory is None:
            _log.debug(
                "CHANNEL_CREATE referencing an unknown channel type %s. Discarding.", data["type"]
            )
            return

        guild_id = utils.get_as_snowflake(data, "guild_id")
        guild = self._get_guild(guild_id)
        if guild is not None:
            # the factory can't be a DMChannel or GroupChannel here
            channel = factory(guild=guild, state=self, data=data)  # type: ignore
            guild._add_channel(channel)  # type: ignore
            self.dispatch("guild_channel_create", channel)
        else:
            _log.debug("CHANNEL_CREATE referencing an unknown guild ID: %s. Discarding.", guild_id)
            return

    def parse_channel_pins_update(self, data) -> None:
        channel_id = int(data["channel_id"])
        try:
            guild = self._get_guild(int(data["guild_id"]))
        except KeyError:
            guild = None
            channel = self._get_private_channel(channel_id)
        else:
            channel = guild and guild._resolve_channel(channel_id)

        if channel is None:
            _log.debug(
                "CHANNEL_PINS_UPDATE referencing an unknown channel ID: %s. Discarding.", channel_id
            )
            return

        last_pin = (
            utils.parse_time(data["last_pin_timestamp"]) if data["last_pin_timestamp"] else None
        )

        if guild is None:
            self.dispatch("private_channel_pins_update", channel, last_pin)
        else:
            self.dispatch("guild_channel_pins_update", channel, last_pin)

    def parse_thread_create(self, data) -> None:
        guild_id = int(data["guild_id"])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug("THREAD_CREATE referencing an unknown guild ID: %s. Discarding", guild_id)
            return

        thread = Thread(guild=guild, state=guild._state, data=data)
        has_thread = guild.get_thread(thread.id)
        guild._add_thread(thread)
        if not has_thread:
            # `newly_created` is documented outside of a thread's fields:
            # https://discord.dev/topics/gateway-events#thread-create
            if data.get("newly_created", False):
                if isinstance(thread.parent, ForumChannel):
                    thread.parent.last_message_id = thread.id

                self.dispatch("thread_create", thread)

            # Avoid an unnecessary breaking change right now by dispatching `thread_join` for
            # threads that were already created.
            self.dispatch("thread_join", thread)

    def parse_thread_update(self, data) -> None:
        guild_id = int(data["guild_id"])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug("THREAD_UPDATE referencing an unknown guild ID: %s. Discarding", guild_id)
            return

        thread_id = int(data["id"])
        thread = guild.get_thread(thread_id)
        if thread is not None:
            old = copy.copy(thread)
            thread._update(data)
            self.dispatch("thread_update", old, thread)
        else:
            thread = Thread(guild=guild, state=guild._state, data=data)
            guild._add_thread(thread)
            self.dispatch("thread_join", thread)

    def parse_thread_delete(self, data) -> None:
        guild_id = int(data["guild_id"])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug("THREAD_DELETE referencing an unknown guild ID: %s. Discarding", guild_id)
            return

        thread_id = int(data["id"])
        thread = guild.get_thread(thread_id)
        if thread is not None:
            guild._remove_thread(thread)
            self.dispatch("thread_delete", thread)

    def parse_thread_list_sync(self, data) -> None:
        guild_id = int(data["guild_id"])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug("THREAD_LIST_SYNC referencing an unknown guild ID: %s. Discarding", guild_id)
            return

        try:
            channel_ids = set(data["channel_ids"])
        except KeyError:
            # If not provided, then the entire guild is being synced
            # So all previous thread data should be overwritten
            previous_threads = guild._threads.copy()
            guild._clear_threads()
        else:
            previous_threads = guild._filter_threads(channel_ids)

        threads = {d["id"]: guild._store_thread(d) for d in data.get("threads", [])}

        for member in data.get("members", []):
            try:
                # note: member['id'] is the thread_id
                thread = threads[member["id"]]
            except KeyError:
                continue
            else:
                thread._add_member(ThreadMember(thread, member))

        for thread in threads.values():
            old = previous_threads.pop(thread.id, None)
            if old is None:
                self.dispatch("thread_join", thread)

        for thread in previous_threads.values():
            self.dispatch("thread_remove", thread)

    def parse_thread_member_update(self, data) -> None:
        guild_id = int(data["guild_id"])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug(
                "THREAD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding", guild_id
            )
            return

        thread_id = int(data["id"])
        thread: Optional[Thread] = guild.get_thread(thread_id)
        if thread is None:
            _log.debug(
                "THREAD_MEMBER_UPDATE referencing an unknown thread ID: %s. Discarding", thread_id
            )
            return

        member = ThreadMember(thread, data)
        thread.me = member

    def parse_thread_members_update(self, data) -> None:
        guild_id = int(data["guild_id"])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug(
                "THREAD_MEMBERS_UPDATE referencing an unknown guild ID: %s. Discarding", guild_id
            )
            return

        thread_id = int(data["id"])
        thread: Optional[Thread] = guild.get_thread(thread_id)
        if thread is None:
            _log.debug(
                "THREAD_MEMBERS_UPDATE referencing an unknown thread ID: %s. Discarding", thread_id
            )
            return

        added_members = [ThreadMember(thread, d) for d in data.get("added_members", [])]
        removed_member_ids = [int(x) for x in data.get("removed_member_ids", [])]
        self_id = self.self_id
        for member in added_members:
            if member.id != self_id:
                thread._add_member(member)
                self.dispatch("thread_member_join", member)
            else:
                thread.me = member
                self.dispatch("thread_join", thread)

        for member_id in removed_member_ids:
            if member_id != self_id:
                member = thread._pop_member(member_id)
                if member is not None:
                    self.dispatch("thread_member_remove", member)
            else:
                self.dispatch("thread_remove", thread)

    def parse_guild_member_add(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_MEMBER_ADD referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        member = Member(guild=guild, data=data, state=self)
        if self.member_cache_flags.joined:
            guild._add_member(member)

        with contextlib.suppress(AttributeError):
            guild._member_count += 1

        self.dispatch("member_join", member)

    def parse_guild_member_remove(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is not None:
            with contextlib.suppress(AttributeError):
                guild._member_count -= 1

            user_id = int(data["user"]["id"])
            member = guild.get_member(user_id)
            if member is not None:
                guild._remove_member(member)
                self.dispatch("member_remove", member)
        else:
            _log.debug(
                (
                    "GUILD_MEMBER_REMOVE referencing an unknown guild ID: %s."
                    "Falling back to raw data."
                ),
                data["guild_id"],
            )

        raw = RawMemberRemoveEvent(data=data, state=self)
        self.dispatch("raw_member_remove", raw)

    def parse_guild_member_update(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        user = data["user"]
        user_id = int(user["id"])
        if guild is None:
            _log.debug(
                "GUILD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        member = guild.get_member(user_id)
        if member is not None:
            old_member = Member._copy(member)
            member._update(data)
            user_update = member._update_inner_user(user)
            if user_update:
                self.dispatch("user_update", user_update[0], user_update[1])

            self.dispatch("member_update", old_member, member)
        else:
            if self.member_cache_flags.joined:
                member = Member(data=data, guild=guild, state=self)

                # Force an update on the inner user if necessary
                user_update = member._update_inner_user(user)
                if user_update:
                    self.dispatch("user_update", user_update[0], user_update[1])

                guild._add_member(member)
            _log.debug(
                "GUILD_MEMBER_UPDATE referencing an unknown member ID: %s. Discarding.", user_id
            )

    def parse_guild_emojis_update(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_EMOJIS_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        before_emojis = guild.emojis
        for emoji in before_emojis:
            self._emojis.pop(emoji.id, None)
        guild.emojis = tuple([self.store_emoji(guild, d) for d in data["emojis"]])
        self.dispatch("guild_emojis_update", guild, before_emojis, guild.emojis)

    def parse_guild_stickers_update(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_STICKERS_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        before_stickers = guild.stickers
        for emoji in before_stickers:
            self._stickers.pop(emoji.id, None)
        guild.stickers = tuple([self.store_sticker(guild, d) for d in data["stickers"]])
        self.dispatch("guild_stickers_update", guild, before_stickers, guild.stickers)

    def _get_create_guild(self, data):
        if data.get("unavailable") is False:
            # GUILD_CREATE with unavailable in the response
            # usually means that the guild has become available
            # and is therefore in the cache
            guild = self._get_guild(int(data["id"]))
            if guild is not None:
                guild.unavailable = False
                guild._from_data(data)
                return guild

        return self._add_guild_from_data(data)

    def is_guild_evicted(self, guild) -> bool:
        return guild.id not in self._guilds

    async def chunk_guild(self, guild, *, wait: bool = True, cache=None):
        if cache is None:
            cache = self.member_cache_flags.joined
        request = self._chunk_requests.get(guild.id)
        if request is None:
            self._chunk_requests[guild.id] = request = ChunkRequest(
                guild.id, self.loop, self._get_guild, cache=cache
            )
            await self.chunker(guild.id, nonce=request.nonce)

        if wait:
            return await request.wait()
        return request.get_future()

    async def _chunk_and_dispatch(self, guild, unavailable) -> None:
        try:
            await asyncio.wait_for(self.chunk_guild(guild), timeout=60.0)
        except asyncio.TimeoutError:
            _log.info("Somehow timed out waiting for chunks.")

        if unavailable is False:
            self.dispatch("guild_available", guild)
        else:
            self.dispatch("guild_join", guild)

    def parse_guild_create(self, data) -> None:
        unavailable = data.get("unavailable")
        if unavailable is True:
            # joined a guild with unavailable == True so..
            return

        guild = self._get_create_guild(data)

        try:
            # Notify the on_ready state, if any, that this guild is complete.
            self._ready_state.put_nowait(guild)
        except AttributeError:
            pass
        else:
            # If we're waiting for the event, put the rest on hold
            return

        # check if it requires chunking
        if self._guild_needs_chunking(guild):
            task = asyncio.create_task(self._chunk_and_dispatch(guild, unavailable))
            self._chunk_tasks[guild.id] = task
            task.add_done_callback(lambda _t: self._chunk_tasks.pop(guild.id, None))
            return

        # Dispatch available if newly available
        if unavailable is False:
            self.dispatch("guild_available", guild)
        else:
            self.dispatch("guild_join", guild)

    def parse_guild_update(self, data) -> None:
        guild = self._get_guild(int(data["id"]))
        if guild is not None:
            old_guild = copy.copy(guild)
            guild._from_data(data)
            self.dispatch("guild_update", old_guild, guild)
        else:
            _log.debug("GUILD_UPDATE referencing an unknown guild ID: %s. Discarding.", data["id"])

    def parse_guild_delete(self, data) -> None:
        guild = self._get_guild(int(data["id"]))
        if guild is None:
            _log.debug("GUILD_DELETE referencing an unknown guild ID: %s. Discarding.", data["id"])
            return

        if data.get("unavailable", False):
            # GUILD_DELETE with unavailable being True means that the
            # guild that was available is now currently unavailable
            guild.unavailable = True
            self.dispatch("guild_unavailable", guild)
            return

        # do a cleanup of the messages cache
        if self._messages is not None:
            self._messages: Optional[Deque[Message]] = deque(
                (msg for msg in self._messages if msg.guild != guild), maxlen=self.max_messages
            )

        self._remove_guild(guild)
        self.dispatch("guild_remove", guild)

    def parse_guild_ban_add(self, data) -> None:
        # we make the assumption that GUILD_BAN_ADD is done
        # before GUILD_MEMBER_REMOVE is called
        # hence we don't remove it from cache or do anything
        # strange with it, the main purpose of this event
        # is mainly to dispatch to another event worth listening to for logging
        guild = self._get_guild(int(data["guild_id"]))
        if guild is not None:
            try:
                user = User(data=data["user"], state=self)
            except KeyError:
                pass
            else:
                member = guild.get_member(user.id) or user
                self.dispatch("member_ban", guild, member)

    def parse_guild_ban_remove(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is not None and "user" in data:
            user = self.store_user(data["user"])
            self.dispatch("member_unban", guild, user)

    def parse_guild_role_create(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_ROLE_CREATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        role_data = data["role"]
        role = Role(guild=guild, data=role_data, state=self)
        guild._add_role(role)
        self.dispatch("guild_role_create", role)

    def parse_guild_role_delete(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is not None:
            role_id = int(data["role_id"])
            try:
                role = guild._remove_role(role_id)
            except KeyError:
                return
            else:
                self.dispatch("guild_role_delete", role)
        else:
            _log.debug(
                "GUILD_ROLE_DELETE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_guild_role_update(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is not None:
            role_data = data["role"]
            role_id = int(role_data["id"])
            role = guild.get_role(role_id)
            if role is not None:
                old_role = copy.copy(role)
                role._update(role_data)
                self.dispatch("guild_role_update", old_role, role)
        else:
            _log.debug(
                "GUILD_ROLE_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_guild_members_chunk(self, data) -> None:
        guild_id = int(data["guild_id"])
        guild = self._get_guild(guild_id)
        presences = data.get("presences", [])

        # the guild won't be None here
        members = [Member(guild=guild, data=member, state=self) for member in data.get("members", [])]  # type: ignore
        _log.debug("Processed a chunk for %s members in guild ID %s.", len(members), guild_id)

        if presences:
            member_dict = {str(member.id): member for member in members}
            for presence in presences:
                user = presence["user"]
                member_id = user["id"]
                member = member_dict.get(member_id)
                if member is not None:
                    member._presence_update(presence, user)

        complete = data.get("chunk_index", 0) + 1 == data.get("chunk_count")
        self.process_chunk_requests(guild_id, data.get("nonce"), members, complete)

    def parse_guild_integrations_update(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is not None:
            self.dispatch("guild_integrations_update", guild)
        else:
            _log.debug(
                "GUILD_INTEGRATIONS_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_integration_create(self, data) -> None:
        guild_id = int(data.pop("guild_id"))
        guild = self._get_guild(guild_id)
        if guild is not None:
            cls, _ = _integration_factory(data["type"])
            integration = cls(data=data, guild=guild)
            self.dispatch("integration_create", integration)
        else:
            _log.debug(
                "INTEGRATION_CREATE referencing an unknown guild ID: %s. Discarding.", guild_id
            )

    def parse_integration_update(self, data) -> None:
        guild_id = int(data.pop("guild_id"))
        guild = self._get_guild(guild_id)
        if guild is not None:
            cls, _ = _integration_factory(data["type"])
            integration = cls(data=data, guild=guild)
            self.dispatch("integration_update", integration)
        else:
            _log.debug(
                "INTEGRATION_UPDATE referencing an unknown guild ID: %s. Discarding.", guild_id
            )

    def parse_integration_delete(self, data) -> None:
        guild_id = int(data["guild_id"])
        guild = self._get_guild(guild_id)
        if guild is not None:
            raw = RawIntegrationDeleteEvent(data)
            self.dispatch("raw_integration_delete", raw)
        else:
            _log.debug(
                "INTEGRATION_DELETE referencing an unknown guild ID: %s. Discarding.", guild_id
            )

    def parse_webhooks_update(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "WEBHOOKS_UPDATE referencing an unknown guild ID: %s. Discarding", data["guild_id"]
            )
            return

        channel = guild.get_channel(int(data["channel_id"]))
        if channel is not None:
            self.dispatch("webhooks_update", channel)
        else:
            _log.debug(
                "WEBHOOKS_UPDATE referencing an unknown channel ID: %s. Discarding.",
                data["channel_id"],
            )

    def parse_stage_instance_create(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is not None:
            stage_instance = StageInstance(guild=guild, state=self, data=data)
            guild._stage_instances[stage_instance.id] = stage_instance
            self.dispatch("stage_instance_create", stage_instance)
        else:
            _log.debug(
                "STAGE_INSTANCE_CREATE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_stage_instance_update(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is not None:
            stage_instance = guild._stage_instances.get(int(data["id"]))
            if stage_instance is not None:
                old_stage_instance = copy.copy(stage_instance)
                stage_instance._update(data)
                self.dispatch("stage_instance_update", old_stage_instance, stage_instance)
            else:
                _log.debug(
                    "STAGE_INSTANCE_UPDATE referencing unknown stage instance ID: %s. Discarding.",
                    data["id"],
                )
        else:
            _log.debug(
                "STAGE_INSTANCE_UPDATE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_stage_instance_delete(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        if guild is not None:
            try:
                stage_instance = guild._stage_instances.pop(int(data["id"]))
            except KeyError:
                pass
            else:
                self.dispatch("stage_instance_delete", stage_instance)
        else:
            _log.debug(
                "STAGE_INSTANCE_DELETE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_voice_state_update(self, data) -> None:
        guild = self._get_guild(utils.get_as_snowflake(data, "guild_id"))
        channel_id = utils.get_as_snowflake(data, "channel_id")
        flags = self.member_cache_flags
        # self.user is *always* cached when this is called
        self_id = self.user.id  # type: ignore
        if guild is not None:
            if int(data["user_id"]) == self_id:
                voice = self._get_voice_client(guild.id)
                if voice is not None:
                    coro = voice.on_voice_state_update(data)
                    task = asyncio.create_task(
                        logging_coroutine(coro, info="Voice Protocol voice state update handler")
                    )
                    self._background_tasks.add(task)
                    task.add_done_callback(self._background_tasks.discard)

            member, before, after = guild._update_voice_state(data, channel_id)  # type: ignore
            after = copy.copy(after)
            if member is not None:
                if flags.voice:
                    if channel_id is None and flags._voice_only and member.id != self_id:
                        # Only remove from cache if we only have the voice flag enabled
                        # Member doesn't meet the Snowflake protocol currently
                        guild._remove_member(member)
                    elif channel_id is not None:
                        guild._add_member(member)

                self.dispatch("voice_state_update", member, before, after)
            else:
                _log.debug(
                    "VOICE_STATE_UPDATE referencing an unknown member ID: %s. Discarding.",
                    data["user_id"],
                )

    def parse_voice_server_update(self, data) -> None:
        try:
            key_id = int(data["guild_id"])
        except KeyError:
            key_id = int(data["channel_id"])

        vc = self._get_voice_client(key_id)
        if vc is not None:
            coro = vc.on_voice_server_update(data)
            task = asyncio.create_task(
                logging_coroutine(coro, info="Voice Protocol voice server update handler")
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    def parse_typing_start(self, data) -> None:
        raw = RawTypingEvent(data)

        member_data = data.get("member")
        if member_data:
            guild = self._get_guild(raw.guild_id)
            if guild is not None:
                raw.member = Member(data=member_data, guild=guild, state=self)
            else:
                raw.member = None
        else:
            raw.member = None
        self.dispatch("raw_typing", raw)

        channel, guild = self._get_guild_channel(data)
        if channel is not None:  # pyright: ignore[reportUnnecessaryComparison]
            user = raw.member or self._get_typing_user(channel, raw.user_id)  # type: ignore
            # will be messageable channel if we get here

            if user is not None:
                self.dispatch("typing", channel, user, raw.when)

    def _get_typing_user(
        self, channel: Optional[MessageableChannel], user_id: int
    ) -> Optional[Union[User, Member]]:
        if isinstance(channel, DMChannel):
            return channel.recipient or self.get_user(user_id)

        if isinstance(channel, (Thread, TextChannel)):
            return channel.guild.get_member(user_id)

        if isinstance(channel, GroupChannel):
            return utils.find(lambda x: x.id == user_id, channel.recipients)

        return self.get_user(user_id)

    def _get_reaction_user(
        self, channel: MessageableChannel, user_id: int
    ) -> Optional[Union[User, Member]]:
        if isinstance(channel, TextChannel):
            return channel.guild.get_member(user_id)
        return self.get_user(user_id)

    def get_reaction_emoji(self, data) -> Union[Emoji, PartialEmoji]:
        emoji_id = utils.get_as_snowflake(data, "id")

        if not emoji_id:
            return data["name"]

        try:
            return self._emojis[emoji_id]
        except KeyError:
            return PartialEmoji.with_state(
                self, animated=data.get("animated", False), id=emoji_id, name=data["name"]
            )

    def _upgrade_partial_emoji(self, emoji: PartialEmoji) -> Union[Emoji, PartialEmoji, str]:
        emoji_id = emoji.id
        if not emoji_id:
            return emoji.name
        try:
            return self._emojis[emoji_id]
        except KeyError:
            return emoji

    def _upgrade_partial_soundboard_sound(
        self, sound: PartialSoundboardSound
    ) -> Union[SoundboardSound, PartialSoundboardSound]:
        sound_id = sound.id

        try:
            return self._soundboard_sounds[sound_id]
        except KeyError:
            return sound

    def get_channel(self, id: Optional[int]) -> Optional[Union[Channel, Thread]]:
        if id is None:
            return None

        pm = self._get_private_channel(id)
        if pm is not None:
            return pm

        for guild in self.guilds:
            channel = guild._resolve_channel(id)
            if channel is not None:
                return channel

        return None

    def get_scheduled_event(self, id: int) -> Optional[ScheduledEvent]:
        for guild in self.guilds:
            if event := guild.get_scheduled_event(id):
                return event

        return None

    def create_message(
        self,
        *,
        channel: MessageableChannel,
        data: MessagePayload,
    ) -> Message:
        return Message(state=self, channel=channel, data=data)

    def create_scheduled_event(
        self, *, guild: Guild, data: ScheduledEventPayload
    ) -> ScheduledEvent:
        return ScheduledEvent(state=self, guild=guild, data=data)

    def parse_guild_scheduled_event_create(self, data) -> None:
        if guild := self._get_guild(int(data["guild_id"])):
            event = self.create_scheduled_event(guild=guild, data=data)
            guild._add_scheduled_event(event)
            self.dispatch("guild_scheduled_event_create", event)
        else:
            _log.debug(
                "GUILD_SCHEDULED_EVENT_CREATE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_guild_scheduled_event_update(self, data) -> None:
        if guild := self._get_guild(int(data["guild_id"])):
            if event := guild.get_scheduled_event(int(data["id"])):
                old = copy.copy(event)
                event._update(data)
                self.dispatch("guild_scheduled_event_update", old, event)
            else:
                _log.debug(
                    "GUILD_SCHEDULED_EVENT_UPDATE referencing unknown event ID: %s. Discarding.",
                    data["id"],
                )
        else:
            _log.debug(
                "GUILD_SCHEDULED_EVENT_UPDATE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_guild_scheduled_event_delete(self, data) -> None:
        if guild := self._get_guild(int(data["guild_id"])):
            if event := guild.get_scheduled_event(int(data["id"])):
                guild._remove_scheduled_event(event.id)
                self.dispatch("guild_scheduled_event_delete", event)
            else:
                _log.debug(
                    "GUILD_SCHEDULED_EVENT_DELETE referencing unknown event ID: %s. Discarding.",
                    data["id"],
                )
        else:
            _log.debug(
                "GUILD_SCHEDULED_EVENT_DELETE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_guild_scheduled_event_user_add(self, data) -> None:
        if guild := self._get_guild(int(data["guild_id"])):
            if event := guild.get_scheduled_event(int(data["guild_scheduled_event_id"])):
                u = ScheduledEventUser.from_id(
                    event=event, user_id=int(data["user_id"]), state=self
                )
                event._add_user(u)
                self.dispatch("guild_scheduled_event_user_add", event, u)
            else:
                _log.debug(
                    "GUILD_SCHEDULED_EVENT_USER_ADD referencing unknown"
                    " event ID: %s. Discarding.",
                    data["user_id"],
                )
        else:
            _log.debug(
                "GUILD_SCHEDULED_EVENT_USER_ADD referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_guild_scheduled_event_user_remove(self, data) -> None:
        if guild := self._get_guild(int(data["guild_id"])):
            if event := guild.get_scheduled_event(int(data["guild_scheduled_event_id"])):
                event._remove_user(int(data["user_id"]))
                self.dispatch(
                    "guild_scheduled_event_user_remove",
                    event,
                    ScheduledEventUser.from_id(
                        event=event, user_id=int(data["user_id"]), state=self
                    ),
                )
            else:
                _log.debug(
                    "GUILD_SCHEDULED_EVENT_USER_REMOVE referencing unknown"
                    " event ID: %s. Discarding.",
                    data["user_id"],
                )
        else:
            _log.debug(
                "GUILD_SCHEDULED_EVENT_USER_REMOVE referencing unknown"
                " guild ID: %s. Discarding.",
                data["guild_id"],
            )

    def parse_auto_moderation_rule_create(self, data) -> None:
        self.dispatch(
            "auto_moderation_rule_create",
            AutoModerationRule(data=data, state=self),
        )

    def parse_auto_moderation_rule_update(self, data) -> None:
        self.dispatch("auto_moderation_rule_update", AutoModerationRule(data=data, state=self))

    def parse_auto_moderation_rule_delete(self, data) -> None:
        self.dispatch("auto_moderation_rule_delete", AutoModerationRule(data=data, state=self))

    def parse_auto_moderation_action_execution(self, data) -> None:
        self.dispatch(
            "auto_moderation_action_execution", AutoModerationActionExecution(data=data, state=self)
        )

    def parse_guild_audit_log_entry_create(self, data) -> None:
        guild = self._get_guild(int(data["guild_id"]))
        user_id = None if data.get("user_id") is None else int(data["user_id"])
        user = self.get_user(user_id)
        users = {} if user_id is None or user is None else {user_id: user}

        if guild is not None:
            entry = AuditLogEntry(auto_moderation_rules={}, users=users, data=data, guild=guild)
            self.dispatch("guild_audit_log_entry_create", entry)
        else:
            _log.debug(
                "guild_audit_log_entry_create wasn't dispatched because the guild (%r) and/or user (%r) are None!",
                guild,
                user,
            )

    def parse_guild_soundboard_sound_create(self, data) -> None:
        # guild_id is always present

        if (guild := self._get_guild(int(data["guild_id"]))) == None:
            _log.debug(
                "GUILD_SOUNDBOARD_SOUND_CREATE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        sound = SoundboardSound(data=data, guild=guild, state=self)
        guild._add_soundboard_sound(sound)
        self.dispatch(
            "guild_soundboard_sound_create", SoundboardSound(data=data, guild=guild, state=self)
        )

    def parse_guild_soundboard_sound_update(self, data) -> None:
        if (guild := self._get_guild(int(data["guild_id"]))) == None:
            _log.debug(
                "GUILD_SOUNDBOARD_SOUND_UPDATE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        if sound := self._soundboard_sounds.get(data["sound_id"]):
            old_sound = copy.copy(sound)
            sound._update(data, guild)
            self.dispatch("guild_soundboard_sound_update", old_sound, sound)
        else:
            _log.debug(
                "GUILD_SOUNDBOARD_SOUND_UPDATE referencing unknown sound ID: %s. Discarding.",
                data["sound_id"],
            )
            # TODO: Should we store the sound here? We definitely could

    def parse_guild_soundboard_sound_delete(self, data) -> None:
        # Data fields are guild_id and sound_id
        if (guild := self._get_guild(int(data["guild_id"]))) == None:
            _log.debug(
                "GUILD_SOUNDBOARD_SOUND_DELETE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        if sound := self._soundboard_sounds.get(data["sound_id"]):
            guild._remove_soundboard_sound(sound.id)
            self.dispatch("guild_soundboard_sound_delete", sound)
        else:
            _log.debug(
                "GUILD_SOUNDBOARD_SOUND_DELETE referencing unknown sound ID: %s. Discarding.",
                data["sound_id"],
            )

    def parse_soundboard_sounds(self, data) -> None:
        # data: {soundboard_sounds: SoundboardSoundPayload[], guild_id: Snowflake}

        if (guild := self._get_guild(int(data["guild_id"]))) == None:
            _log.debug(
                "SOUNDBOARD_SOUNDS referencing unknown guild ID: %s. Discarding.", data["guild_id"]
            )
            return

        guild._soundboard_sounds = {
            sound["sound_id"]: SoundboardSound(data=sound, guild=guild, state=self)
            for sound in data["soundboard_sounds"]
        }

        sounds = list(guild._soundboard_sounds.values())

        for sound in sounds:
            self._soundboard_sounds[sound.id] = sound

        self.dispatch("soundboard_sounds", sounds)

    def parse_voice_channel_effect_send(self, data: VoiceChannelEffectSendPayload) -> None:
        self.dispatch("voice_channel_effect_send", VoiceChannelEffect(data=data, state=self))


class AutoShardedConnectionState(ConnectionState):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.shard_ids: Union[List[int], range] = []
        self.shards_launched: asyncio.Event = asyncio.Event()

    def _update_message_references(self) -> None:
        # self._messages won't be None when this is called
        for msg in self._messages:  # type: ignore
            if not msg.guild:
                continue

            new_guild = self._get_guild(msg.guild.id)
            if new_guild is not None and new_guild is not msg.guild:
                channel_id = msg.channel.id
                channel = new_guild._resolve_channel(channel_id) or Object(id=channel_id)
                # channel will either be a TextChannel, Thread or Object
                msg._rebind_cached_references(new_guild, channel)  # type: ignore

    async def chunker(
        self,
        guild_id: int,
        query: str = "",
        limit: int = 0,
        presences: bool = False,
        *,
        shard_id: Optional[int] = None,
        nonce: Optional[str] = None,
    ) -> None:
        ws = self._get_websocket(guild_id, shard_id=shard_id)
        await ws.request_chunks(
            guild_id, query=query, limit=limit, presences=presences, nonce=nonce
        )

    async def _delay_ready(self) -> None:
        await self.shards_launched.wait()
        processed = []
        max_concurrency = len(self.shard_ids) * 2
        current_bucket = []
        while True:
            # this snippet of code is basically waiting N seconds
            # until the last GUILD_CREATE was sent
            try:
                guild = await asyncio.wait_for(
                    self._ready_state.get(), timeout=self.guild_ready_timeout
                )
            except asyncio.TimeoutError:
                break
            else:
                if self._guild_needs_chunking(guild):
                    _log.debug(
                        "Guild ID %d requires chunking, will be done in the background.", guild.id
                    )
                    if len(current_bucket) >= max_concurrency:
                        try:
                            await utils.sane_wait_for(
                                current_bucket, timeout=max_concurrency * 70.0
                            )
                        except asyncio.TimeoutError:
                            fmt = "Shard ID %s failed to wait for chunks from a sub-bucket with length %d"
                            _log.warning(fmt, guild.shard_id, len(current_bucket))
                        finally:
                            current_bucket = []

                    # Chunk the guild in the background while we wait for GUILD_CREATE streaming
                    future = asyncio.ensure_future(self.chunk_guild(guild))
                    current_bucket.append(future)
                else:
                    future = self.loop.create_future()
                    future.set_result([])

                processed.append((guild, future))

        processed: list[tuple[Guild, Future]]
        key: Callable[[tuple[Guild, Future[list[Member]]]], int] = lambda g: g[0].shard_id
        guilds = sorted(processed, key=key)
        for shard_id, info in itertools.groupby(guilds, key=key):
            children: Tuple[Guild]
            futures: Tuple[Future]
            # zip with `*` should, and will, return 2 tuples since every element is 2 length
            # but pyright believes otherwise.
            children, futures = zip(*info)  # type: ignore
            # 110 reqs/minute w/ 1 req/guild plus some buffer
            timeout = 61 * (len(children) / 110)
            try:
                await utils.sane_wait_for(futures, timeout=timeout)
            except asyncio.TimeoutError:
                _log.warning(
                    "Shard ID %s failed to wait for chunks (timeout=%.2f) for %d guilds",
                    shard_id,
                    timeout,
                    len(guilds),
                )
            for guild in children:
                if guild.unavailable is False:
                    self.dispatch("guild_available", guild)
                else:
                    self.dispatch("guild_join", guild)

            self.dispatch("shard_ready", shard_id)

        # remove the state
        # AttributeError if already been deleted somehow
        with contextlib.suppress(AttributeError):
            del self._ready_state

        # regular users cannot shard so we won't worry about it here.

        # clear the current task
        self._ready_task = None

        # dispatch the event
        self.call_handlers("ready")
        self.dispatch("ready")

    def parse_ready(self, data) -> None:
        if not hasattr(self, "_ready_state"):
            self._ready_state = asyncio.Queue()

        self.user = user = ClientUser(state=self, data=data["user"])
        # self._users is a list of Users, we're setting a ClientUser
        self._users[user.id] = user  # type: ignore

        if self.application_id is None:
            try:
                application = data["application"]
            except KeyError:
                pass
            else:
                self.application_id = utils.get_as_snowflake(application, "id")
                self.application_flags = ApplicationFlags._from_value(application["flags"])

        for guild_data in data["guilds"]:
            self._add_guild_from_data(guild_data)

        if self._messages:
            self._update_message_references()

        self.dispatch("connect")
        self.dispatch("shard_connect", data["__shard_id__"])

        if self._ready_task is None:
            self._ready_task = asyncio.create_task(self._delay_ready())

    def parse_resumed(self, data) -> None:
        self.dispatch("resumed")
        self.dispatch("shard_resumed", data["__shard_id__"])
