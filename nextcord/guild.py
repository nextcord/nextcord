# SPDX-License-Identifier: MIT

from __future__ import annotations

import contextlib
import copy
import unicodedata
import warnings
from asyncio import Future
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Literal,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    overload,
)

from . import abc, utils
from .asset import Asset
from .auto_moderation import AutoModerationRule, AutoModerationTriggerMetadata
from .bans import BanEntry
from .channel import (
    CategoryChannel,
    ForumChannel,
    StageChannel,
    TextChannel,
    VoiceChannel,
    _guild_channel_factory,
    _threaded_guild_channel_factory,
)
from .colour import Colour
from .emoji import Emoji
from .entitlement import Entitlement
from .enums import (
    AuditLogAction,
    AutoModerationEventType,
    AutoModerationTriggerType,
    ChannelType,
    ContentFilter,
    EntitlementOwnerType,
    NotificationLevel,
    NSFWLevel,
    ScheduledEventEntityType,
    ScheduledEventPrivacyLevel,
    VerificationLevel,
    VideoQualityMode,
    VoiceRegion,
    try_enum,
)
from .errors import ClientException, InvalidArgument, InvalidData
from .flags import SystemChannelFlags
from .integrations import Integration, _integration_factory
from .invite import Invite
from .iterators import AuditLogIterator, BanIterator, MemberIterator, ScheduledEventIterator
from .member import Member, VoiceState
from .mixins import Hashable
from .object import Object
from .partial_emoji import PartialEmoji
from .permissions import PermissionOverwrite
from .role import Role
from .scheduled_events import EntityMetadata, ScheduledEvent
from .stage_instance import StageInstance
from .sticker import GuildSticker
from .threads import Thread, ThreadMember
from .user import User
from .widget import Widget

__all__ = ("Guild",)

MISSING = utils.MISSING

if TYPE_CHECKING:
    import datetime
    from typing import cast

    from .abc import Snowflake, SnowflakeTime
    from .application_command import BaseApplicationCommand
    from .auto_moderation import AutoModerationAction
    from .channel import ForumTag
    from .enums import ForumLayoutType, SortOrderType
    from .file import File
    from .message import Attachment
    from .permissions import Permissions
    from .state import ConnectionState
    from .template import Template
    from .types.auto_moderation import AutoModerationRuleCreate
    from .types.channel import GuildChannel as GuildChannelPayload
    from .types.guild import (
        Ban as BanPayload,
        Guild as GuildPayload,
        GuildFeature,
        MFALevel,
        RolePositionUpdate,
    )
    from .types.integration import IntegrationType
    from .types.interactions import ApplicationCommand as ApplicationCommandPayload
    from .types.scheduled_events import ScheduledEvent as ScheduledEventPayload
    from .types.snowflake import SnowflakeList
    from .types.sticker import CreateGuildSticker
    from .types.template import CreateTemplate
    from .types.threads import Thread as ThreadPayload
    from .types.voice import GuildVoiceState
    from .voice_client import VoiceProtocol
    from .webhook import Webhook

    VocalGuildChannel = Union[VoiceChannel, StageChannel]
    GuildChannel = Union[VoiceChannel, StageChannel, TextChannel, CategoryChannel, ForumChannel]
    ByCategoryItem = Tuple[Optional[CategoryChannel], List[GuildChannel]]


class _GuildLimit(NamedTuple):
    emoji: int
    stickers: int
    bitrate: float
    filesize: int


class Guild(Hashable):
    """Represents a Discord guild.

    This is referred to as a "server" in the official Discord UI.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    Attributes
    ----------
    name: :class:`str`
        The guild name.
    emojis: Tuple[:class:`Emoji`, ...]
        All emojis that the guild owns.
    stickers: Tuple[:class:`GuildSticker`, ...]
        All stickers that the guild owns.

        .. versionadded:: 2.0
    region: :class:`VoiceRegion`
        The region the guild belongs on. There is a chance that the region
        will be a :class:`str` if the value is not recognised by the enumerator.
    afk_timeout: :class:`int`
        The timeout to get sent to the AFK channel.
    afk_channel: Optional[:class:`VoiceChannel`]
        The channel that denotes the AFK channel. ``None`` if it doesn't exist.
    id: :class:`int`
        The guild's ID.
    owner_id: :class:`int`
        The guild owner's ID. Use :attr:`Guild.owner` instead.
    unavailable: :class:`bool`
        Indicates if the guild is unavailable. If this is ``True`` then the
        reliability of other attributes outside of :attr:`Guild.id` is slim and they might
        all be ``None``. It is best to not do anything with the guild if it is unavailable.

        Check the :func:`on_guild_unavailable` and :func:`on_guild_available` events.
    max_presences: Optional[:class:`int`]
        The maximum amount of presences for the guild.
    max_members: Optional[:class:`int`]
        The maximum amount of members for the guild.

        .. note::

            This attribute is only available via :meth:`.Client.fetch_guild`.
    max_video_channel_users: Optional[:class:`int`]
        The maximum amount of users in a video channel.

        .. versionadded:: 1.4
    description: Optional[:class:`str`]
        The guild's description.
    mfa_level: :class:`int`
        Indicates the guild's two factor authorisation level. If this value is 0 then
        the guild does not require 2FA for their administrative members. If the value is
        1 then they do.
    verification_level: :class:`VerificationLevel`
        The guild's verification level.
    explicit_content_filter: :class:`ContentFilter`
        The guild's explicit content filter.
    default_notifications: :class:`NotificationLevel`
        The guild's notification settings.
    features: List[:class:`str`]
        A list of features that the guild has. The features that a guild can have are
        subject to arbitrary change by Discord.

        They are currently as follows:

        - ``ANIMATED_BANNER``: Guild can upload an animated banner.
        - ``ANIMATED_ICON``: Guild can upload an animated icon.
        - ``AUTO_MODERATION``: Guild has set up auto moderation rules.
        - ``APPLICATION_COMMAND_PERMISSIONS_V2``: Guild is using the old permissions configuration behavior.
        - ``BANNER``: Guild can upload and use a banner. (i.e. :attr:`.banner`)
        - ``COMMUNITY``: Guild is a community server.
        - ``DEVELOPER_SUPPORT_SERVER``: Guild has been set as a support server on the App Directory.
        - ``DISCOVERABLE``: Guild shows up in Server Discovery.
        - ``FEATURABLE``: Guild is able to be featured in Server Discovery.
        - ``INVITES_DISABLED``: Guild has paused invites, preventing new users from joining.
        - ``INVITE_SPLASH``: Guild's invite page can have a special splash.
        - ``MEMBER_VERIFICATION_GATE_ENABLED``: Guild has Membership Screening enabled.
        - ``MONETIZATION_ENABLED``: Guild has enabled monetization.
        - ``MORE_STICKERS``: Guild has increased custom sticker slots.
        - ``NEWS``: Guild can create news channels.
        - ``PARTNERED``: Guild is a partnered server.
        - ``PREVIEW_ENABLED``: Guild can be viewed before being accepted via Membership Screening.
        - ``RAID_ALERTS_DISABLED``: Guild disabled alerts for join raids in the configured safety alerts channel.
        - ``ROLE_ICONS``: Guild is able to set role icons.
        - ``TICKETED_EVENTS_ENABLED``: Guild has enabled ticketed events.
        - ``VANITY_URL``: Guild can have a vanity invite URL (e.g. discord.gg/discord-api).
        - ``VERIFIED``: Guild is a verified server.
        - ``VIP_REGIONS``: Guild has VIP voice regions.
        - ``WELCOME_SCREEN_ENABLED``: Guild has enabled the welcome screen.

    premium_tier: :class:`int`
        The premium tier for this guild. Corresponds to "Boost Level" in the official UI.
        The number goes from 0 to 3 inclusive.
    premium_subscription_count: :class:`int`
        The number of "boosts" this guild currently has.
    preferred_locale: Optional[:class:`str`]
        The preferred locale for the guild. Used when filtering Server Discovery
        results to a specific language.
    nsfw_level: :class:`NSFWLevel`
        The guild's NSFW level.

        .. versionadded:: 2.0

    approximate_member_count: Optional[:class:`int`]
        The approximate number of members in the guild. This is ``None`` unless the guild is obtained
        using :meth:`Client.fetch_guild` with ``with_counts=True``.

        .. versionadded:: 2.0

    approximate_presence_count: Optional[:class:`int`]
        The approximate number of members currently active in the guild.
        This includes idle, dnd, online, and invisible members. Offline members are excluded.
        This is ``None`` unless the guild is obtained using :meth:`Client.fetch_guild`
        with ``with_counts=True``.

        .. versionadded:: 2.0

    max_stage_video_channel_users: Optional[:class:`int`]
        The maximum amount of users in a stage channel when video is being broadcasted.

        .. versionadded:: 2.6
    """

    __slots__ = (
        "afk_timeout",
        "afk_channel",
        "name",
        "id",
        "unavailable",
        "region",
        "owner_id",
        "mfa_level",
        "emojis",
        "stickers",
        "features",
        "verification_level",
        "explicit_content_filter",
        "default_notifications",
        "description",
        "max_presences",
        "max_members",
        "max_video_channel_users",
        "premium_tier",
        "premium_subscription_count",
        "preferred_locale",
        "nsfw_level",
        "_application_commands",
        "_members",
        "_channels",
        "_icon",
        "_banner",
        "_state",
        "_roles",
        "_member_count",
        "_large",
        "_splash",
        "_voice_states",
        "_system_channel_id",
        "_system_channel_flags",
        "_discovery_splash",
        "_rules_channel_id",
        "_public_updates_channel_id",
        "_stage_instances",
        "_threads",
        "_scheduled_events",
        "approximate_member_count",
        "approximate_presence_count",
        "_premium_progress_bar_enabled",
        "_safety_alerts_channel_id",
        "max_stage_video_channel_users",
    )

    _PREMIUM_GUILD_LIMITS: ClassVar[Dict[Optional[int], _GuildLimit]] = {
        None: _GuildLimit(emoji=50, stickers=5, bitrate=96e3, filesize=25 * 1024 * 1024),
        0: _GuildLimit(emoji=50, stickers=5, bitrate=96e3, filesize=25 * 1024 * 1024),
        1: _GuildLimit(emoji=100, stickers=15, bitrate=128e3, filesize=25 * 1024 * 1024),
        2: _GuildLimit(emoji=150, stickers=30, bitrate=256e3, filesize=50 * 1024 * 1024),
        3: _GuildLimit(emoji=250, stickers=60, bitrate=384e3, filesize=100 * 1024 * 1024),
    }

    def __init__(self, *, data: GuildPayload, state: ConnectionState) -> None:
        self._channels: Dict[int, GuildChannel] = {}
        self._members: Dict[int, Member] = {}
        self._scheduled_events: Dict[int, ScheduledEvent] = {}
        self._voice_states: Dict[int, VoiceState] = {}
        self._threads: Dict[int, Thread] = {}
        self._application_commands: Dict[int, BaseApplicationCommand] = {}
        self._state: ConnectionState = state
        self._from_data(data)

    def _add_channel(self, channel: GuildChannel, /) -> None:
        self._channels[channel.id] = channel

    def _remove_channel(self, channel: Snowflake, /) -> None:
        self._channels.pop(channel.id, None)

    def _voice_state_for(self, user_id: int, /) -> Optional[VoiceState]:
        return self._voice_states.get(user_id)

    def _add_member(self, member: Member, /) -> None:
        self._members[member.id] = member

    def _store_thread(self, payload: ThreadPayload, /) -> Thread:
        thread = Thread(guild=self, state=self._state, data=payload)
        self._threads[thread.id] = thread
        return thread

    def _remove_member(self, member: Snowflake, /) -> None:
        self._members.pop(member.id, None)

    def _add_thread(self, thread: Thread, /) -> None:
        self._threads[thread.id] = thread

    def _remove_thread(self, thread: Snowflake, /) -> None:
        self._threads.pop(thread.id, None)

    def _clear_threads(self) -> None:
        self._threads.clear()

    def _remove_threads_by_channel(self, channel_id: int) -> None:
        to_remove = [k for k, t in self._threads.items() if t.parent_id == channel_id]
        for k in to_remove:
            del self._threads[k]

    def _filter_threads(self, channel_ids: Set[int]) -> Dict[int, Thread]:
        to_remove: Dict[int, Thread] = {
            k: t for k, t in self._threads.items() if t.parent_id in channel_ids
        }
        for k in to_remove:
            del self._threads[k]
        return to_remove

    def _add_scheduled_event(self, event: ScheduledEvent) -> None:
        self._scheduled_events[event.id] = event

    def _remove_scheduled_event(self, event: int) -> None:
        self._scheduled_events.pop(event, None)

    def _store_scheduled_event(self, payload: ScheduledEventPayload) -> ScheduledEvent:
        event = ScheduledEvent(guild=self, state=self._state, data=payload)
        self._scheduled_events[event.id] = event
        return event

    def __str__(self) -> str:
        return self.name or ""

    def __repr__(self) -> str:
        attrs = (
            ("id", self.id),
            ("name", self.name),
            ("shard_id", self.shard_id),
            ("chunked", self.chunked),
            ("member_count", getattr(self, "_member_count", None)),
        )
        inner = " ".join("%s=%r" % t for t in attrs)
        return f"<Guild {inner}>"

    def _update_voice_state(
        self, data: GuildVoiceState, channel_id: int
    ) -> Tuple[Optional[Member], VoiceState, VoiceState]:
        user_id = int(data["user_id"])
        channel = self.get_channel(channel_id)
        try:
            # check if we should remove the voice state from cache
            if channel is None:
                after = self._voice_states.pop(user_id)
            else:
                after = self._voice_states[user_id]

            before = copy.copy(after)
            after._update(data, channel)  # type: ignore
        except KeyError:
            # if we're here then we're getting added into the cache
            after = VoiceState(data=data, channel=channel)  # type: ignore
            before = VoiceState(data=data, channel=None)  # type: ignore
            self._voice_states[user_id] = after

        member = self.get_member(user_id)
        if member is None:
            try:
                member = Member(data=data["member"], state=self._state, guild=self)
            except KeyError:
                member = None

        return member, before, after

    def _add_role(self, role: Role, /) -> None:
        # roles get added to the bottom (position 1, pos 0 is @everyone)
        # so since self.roles has the @everyone role, we can't increment
        # its position because it's stuck at position 0. Luckily x += False
        # is equivalent to adding 0. So we cast the position to a bool and
        # increment it.
        for r in self._roles.values():
            r.position += not r.is_default()

        self._roles[role.id] = role

    def _remove_role(self, role_id: int, /) -> Role:
        # this raises KeyError if it fails..
        role = self._roles.pop(role_id)

        # since it didn't, we can change the positions now
        # basically the same as above except we only decrement
        # the position if we're above the role we deleted.
        for r in self._roles.values():
            r.position -= r.position > role.position

        return role

    def _from_data(self, guild: GuildPayload) -> None:
        # according to Stan, this is always available even if the guild is unavailable
        # I don't have this guarantee when someone updates the guild.
        member_count = guild.get("member_count", None)
        if member_count is not None:
            self._member_count: int = member_count

        self.name: str = guild.get("name")
        self.region: VoiceRegion = try_enum(VoiceRegion, guild.get("region"))
        self.verification_level: VerificationLevel = try_enum(
            VerificationLevel, guild.get("verification_level")
        )
        self.default_notifications: NotificationLevel = try_enum(
            NotificationLevel, guild.get("default_message_notifications")
        )
        self.explicit_content_filter: ContentFilter = try_enum(
            ContentFilter, guild.get("explicit_content_filter", 0)
        )
        self.afk_timeout: int = guild.get("afk_timeout")
        self._icon: Optional[str] = guild.get("icon")
        self._banner: Optional[str] = guild.get("banner")
        self.unavailable: bool = guild.get("unavailable", False)
        self.id: int = int(guild["id"])
        self._roles: Dict[int, Role] = {}
        state = self._state  # speed up attribute access
        for r in guild.get("roles", []):
            role = Role(guild=self, data=r, state=state)
            self._roles[role.id] = role

        self.mfa_level: MFALevel = guild.get("mfa_level")
        self.emojis: Tuple[Emoji, ...] = tuple(
            (state.store_emoji(self, d) for d in guild.get("emojis", []))
        )
        self.stickers: Tuple[GuildSticker, ...] = tuple(
            (state.store_sticker(self, d) for d in guild.get("stickers", []))
        )
        self.features: List[GuildFeature] = guild.get("features", [])
        self._splash: Optional[str] = guild.get("splash")
        self._system_channel_id: Optional[int] = utils.get_as_snowflake(guild, "system_channel_id")
        self.description: Optional[str] = guild.get("description")
        self.max_presences: Optional[int] = guild.get("max_presences")
        self.max_members: Optional[int] = guild.get("max_members")
        self.max_video_channel_users: Optional[int] = guild.get("max_video_channel_users")
        self.max_stage_video_channel_users: Optional[int] = guild.get(
            "max_stage_video_channel_users"
        )
        self.premium_tier: int = guild.get("premium_tier", 0)
        self.premium_subscription_count: int = guild.get("premium_subscription_count") or 0
        self._system_channel_flags: int = guild.get("system_channel_flags", 0)
        self.preferred_locale: Optional[str] = guild.get("preferred_locale")
        self._discovery_splash: Optional[str] = guild.get("discovery_splash")
        self._rules_channel_id: Optional[int] = utils.get_as_snowflake(guild, "rules_channel_id")
        self._public_updates_channel_id: Optional[int] = utils.get_as_snowflake(
            guild, "public_updates_channel_id"
        )
        self.nsfw_level: NSFWLevel = try_enum(NSFWLevel, guild.get("nsfw_level", 0))
        self.approximate_presence_count = guild.get("approximate_presence_count")
        self.approximate_member_count = guild.get("approximate_member_count")

        self._stage_instances: Dict[int, StageInstance] = {}
        for s in guild.get("stage_instances", []):
            stage_instance = StageInstance(guild=self, data=s, state=state)
            self._stage_instances[stage_instance.id] = stage_instance

        cache_joined = self._state.member_cache_flags.joined
        self_id = self._state.self_id
        for mdata in guild.get("members", []):
            member = Member(data=mdata, guild=self, state=state)  # type: ignore
            if cache_joined or member.id == self_id:
                self._add_member(member)

        self._sync(guild)
        self._large: Optional[bool] = None if member_count is None else self._member_count >= 250

        self.owner_id: Optional[int] = utils.get_as_snowflake(guild, "owner_id")
        self.afk_channel: Optional[VocalGuildChannel] = self.get_channel(utils.get_as_snowflake(guild, "afk_channel_id"))  # type: ignore

        for obj in guild.get("voice_states", []):
            self._update_voice_state(obj, int(obj["channel_id"]))

        for event in guild.get("guild_scheduled_events") or []:
            self._store_scheduled_event(event)

        self._premium_progress_bar_enabled: Optional[bool] = guild.get(
            "premium_progress_bar_enabled"
        )

        self._safety_alerts_channel_id: Optional[int] = utils.get_as_snowflake(
            guild, "safety_alerts_channel_id"
        )

    # TODO: refactor/remove?
    def _sync(self, data: GuildPayload) -> None:
        with contextlib.suppress(KeyError):
            self._large = data["large"]

        empty_tuple = ()
        for presence in data.get("presences", []):
            user_id = int(presence["user"]["id"])
            member = self.get_member(user_id)
            if member is not None:
                member._presence_update(presence, empty_tuple)  # type: ignore

        if "channels" in data:
            channels = data["channels"]
            for c in channels:
                factory, _ = _guild_channel_factory(c["type"])
                if factory:
                    self._add_channel(factory(guild=self, data=c, state=self._state))  # type: ignore

        if "threads" in data:
            threads = data["threads"]
            for thread in threads:
                self._add_thread(Thread(guild=self, state=self._state, data=thread))

    @property
    def channels(self) -> List[GuildChannel]:
        """List[:class:`abc.GuildChannel`]: A list of channels that belong to this guild."""
        return list(self._channels.values())

    @property
    def threads(self) -> List[Thread]:
        """List[:class:`Thread`]: A list of threads that you have permission to view.

        .. versionadded:: 2.0
        """
        return list(self._threads.values())

    @property
    def large(self) -> bool:
        """:class:`bool`: Indicates if the guild is a 'large' guild.

        A large guild is defined as having more than ``large_threshold`` count
        members, which for this library is set to the maximum of 250.
        """
        if self._large is None:
            try:
                return self._member_count >= 250
            except AttributeError:
                return len(self._members) >= 250
        return self._large

    @property
    def invites_disabled(self) -> bool:
        """:class:`bool`: Indicates if the guild's invites are paused.

        .. versionadded:: 2.4
        """
        return "INVITES_DISABLED" in self.features

    @property
    def voice_channels(self) -> List[VoiceChannel]:
        """List[:class:`VoiceChannel`]: A list of voice channels that belong to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, VoiceChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def stage_channels(self) -> List[StageChannel]:
        """List[:class:`StageChannel`]: A list of stage channels that belong to this guild.

        .. versionadded:: 1.7

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, StageChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def me(self) -> Member:
        """:class:`Member`: Similar to :attr:`Client.user` except an instance of :class:`Member`.
        This is essentially used to get the member version of yourself.
        """
        self_id = self._state.user.id  # type: ignore
        # The self member is *always* cached
        return self.get_member(self_id)  # type: ignore

    @property
    def voice_client(self) -> Optional[VoiceProtocol]:
        """Optional[:class:`VoiceProtocol`]: Returns the :class:`VoiceProtocol` associated with this guild, if any."""
        return self._state._get_voice_client(self.id)

    @property
    def text_channels(self) -> List[TextChannel]:
        """List[:class:`TextChannel`]: A list of text channels that belong to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, TextChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def categories(self) -> List[CategoryChannel]:
        """List[:class:`CategoryChannel`]: A list of categories that belong to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, CategoryChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def forum_channels(self) -> List[ForumChannel]:
        """List[:class:`ForumChannel`]: A list of forum channels that belong to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, ForumChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def scheduled_events(self) -> List[ScheduledEvent]:
        """List[:class:`ScheduledEvent`]: A list of scheduled events in this guild.

        .. versionadded:: 2.0
        """
        return list(self._scheduled_events.values())

    @property
    def premium_progress_bar_enabled(self) -> Optional[bool]:
        """Optional[:class:`bool`:] Whether the premium boost progress bar is enabled.

        .. versionadded:: 2.6
        """
        return self._premium_progress_bar_enabled

    def by_category(self) -> List[ByCategoryItem]:
        """Returns every :class:`CategoryChannel` and their associated channels.

        These channels and categories are sorted in the official Discord UI order.

        If the channels do not have a category, then the first element of the tuple is
        ``None``.

        Returns
        -------
        List[Tuple[Optional[:class:`CategoryChannel`], List[:class:`abc.GuildChannel`]]]:
            The categories and their associated channels.
        """
        grouped: Dict[Optional[int], List[GuildChannel]] = {}
        for channel in self._channels.values():
            if isinstance(channel, CategoryChannel):
                grouped.setdefault(channel.id, [])
                continue

            try:
                grouped[channel.category_id].append(channel)
            except KeyError:
                grouped[channel.category_id] = [channel]

        def key(t: ByCategoryItem) -> Tuple[Tuple[int, int], List[GuildChannel]]:
            k, v = t
            return ((k.position, k.id) if k else (-1, -1), v)

        _get = self._channels.get
        as_list: List[ByCategoryItem] = [(_get(k), v) for k, v in grouped.items()]  # type: ignore
        as_list.sort(key=key)
        for _, channels in as_list:
            channels.sort(key=lambda c: (c._sorting_bucket, c.position, c.id))
        return as_list

    def _resolve_channel(self, id: Optional[int], /) -> Optional[Union[GuildChannel, Thread]]:
        if id is None:
            return None

        return self._channels.get(id) or self._threads.get(id)

    def get_channel_or_thread(self, channel_id: int, /) -> Optional[Union[Thread, GuildChannel]]:
        """Returns a channel or thread with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        channel_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[Union[:class:`Thread`, :class:`.abc.GuildChannel`]]
            The returned channel or thread or ``None`` if not found.
        """
        return self._channels.get(channel_id) or self._threads.get(channel_id)

    def get_channel(self, channel_id: int, /) -> Optional[GuildChannel]:
        """Returns a channel with the given ID.

        .. note::

            This does *not* search for threads.

        Parameters
        ----------
        channel_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.abc.GuildChannel`]
            The returned channel or ``None`` if not found.
        """
        return self._channels.get(channel_id)

    def get_thread(self, thread_id: int, /) -> Optional[Thread]:
        """Returns a thread with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        thread_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Thread`]
            The returned thread or ``None`` if not found.
        """
        return self._threads.get(thread_id)

    @property
    def system_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Returns the guild's channel used for system messages.

        If no channel is set, then this returns ``None``.
        """
        channel_id = self._system_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def system_channel_flags(self) -> SystemChannelFlags:
        """:class:`SystemChannelFlags`: Returns the guild's system channel settings."""
        return SystemChannelFlags._from_value(self._system_channel_flags)

    @property
    def rules_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Return's the guild's channel used for the rules.
        The guild must be a Community guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 1.3
        """
        channel_id = self._rules_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def public_updates_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Return's the guild's channel where admins and
        moderators of the guilds receive notices from Discord. The guild must be a
        Community guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 1.4
        """
        channel_id = self._public_updates_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def safety_alerts_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Returns the guild's channel where admins and
        moderators of the guild receive safety alerts from Discord. The guild must be a
        Community guild.

        If no channel is set then this returns ``None``.

        .. versionadded:: 2.6
        """
        channel_id = self._safety_alerts_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def emoji_limit(self) -> int:
        """:class:`int`: The maximum number of emoji slots this guild has."""
        more_emoji = 200 if "MORE_EMOJI" in self.features else 50
        return max(more_emoji, self._PREMIUM_GUILD_LIMITS[self.premium_tier].emoji)

    @property
    def sticker_limit(self) -> int:
        """:class:`int`: The maximum number of sticker slots this guild has.

        .. versionadded:: 2.0
        """
        more_stickers = 60 if "MORE_STICKERS" in self.features else 5
        return max(more_stickers, self._PREMIUM_GUILD_LIMITS[self.premium_tier].stickers)

    @property
    def bitrate_limit(self) -> float:
        """:class:`float`: The maximum bitrate for voice channels this guild can have."""
        vip_guild = (
            self._PREMIUM_GUILD_LIMITS[1].bitrate if "VIP_REGIONS" in self.features else 96e3
        )
        return max(vip_guild, self._PREMIUM_GUILD_LIMITS[self.premium_tier].bitrate)

    @property
    def filesize_limit(self) -> int:
        """:class:`int`: The maximum number of bytes files can have when uploaded to this guild."""
        return self._PREMIUM_GUILD_LIMITS[self.premium_tier].filesize

    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: A list of members that belong to this guild."""
        return list(self._members.values())

    @property
    def bots(self) -> List[Member]:
        """List[:class:`Member`]: A list of bots that belong to this guild.

        .. warning::

            Due to a Discord limitation, in order for this attribute to remain up-to-date and
            accurate, it requires :attr:`Intents.members` to be specified.

        .. versionadded:: 2.0"""
        return [m for m in self._members.values() if m.bot]

    @property
    def humans(self) -> List[Member]:
        """List[:class:`Member`]: A list of user accounts that belong to this guild.

        .. warning::

            Due to a Discord limitation, in order for this attribute to remain up-to-date and
            accurate, it requires :attr:`Intents.members` to be specified.

        .. versionadded:: 2.0"""
        return [m for m in self._members.values() if not m.bot]

    def get_member(self, user_id: int, /) -> Optional[Member]:
        """Returns a member with the given ID.

        Parameters
        ----------
        user_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Member`]
            The member or ``None`` if not found.
        """
        return self._members.get(user_id)

    @property
    def premium_subscribers(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who have "boosted" this guild."""
        return [member for member in self.members if member.premium_since is not None]

    @property
    def roles(self) -> List[Role]:
        """List[:class:`Role`]: Returns a :class:`list` of the guild's roles in hierarchy order.

        The first element of this list will be the lowest role in the
        hierarchy.
        """
        return sorted(self._roles.values())

    def get_role(self, role_id: int, /) -> Optional[Role]:
        """Returns a role with the given ID.

        Parameters
        ----------
        role_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Role`]
            The role or ``None`` if not found.
        """
        return self._roles.get(role_id)

    @property
    def default_role(self) -> Role:
        """:class:`Role`: Gets the @everyone role that all members have by default."""
        # The @everyone role is *always* given
        return self.get_role(self.id)  # type: ignore

    @property
    def premium_subscriber_role(self) -> Optional[Role]:
        """Optional[:class:`Role`]: Gets the premium subscriber role, AKA "boost" role, in this guild.

        .. versionadded:: 1.6
        """
        for role in self._roles.values():
            if role.is_premium_subscriber():
                return role
        return None

    @property
    def self_role(self) -> Optional[Role]:
        """Optional[:class:`Role`]: Gets the role associated with this client's user, if any.

        .. versionadded:: 1.6
        """
        self_id = self._state.self_id
        for role in self._roles.values():
            tags = role.tags
            if tags and tags.bot_id == self_id:
                return role
        return None

    @property
    def stage_instances(self) -> List[StageInstance]:
        """List[:class:`StageInstance`]: Returns a :class:`list` of the guild's stage instances that
        are currently running.

        .. versionadded:: 2.0
        """
        return list(self._stage_instances.values())

    def get_stage_instance(self, stage_instance_id: int, /) -> Optional[StageInstance]:
        """Returns a stage instance with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        stage_instance_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`StageInstance`]
            The stage instance or ``None`` if not found.
        """
        return self._stage_instances.get(stage_instance_id)

    @property
    def owner(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member that owns the guild."""
        return self.get_member(self.owner_id)  # type: ignore

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's icon asset, if available."""
        if self._icon is None:
            return None
        return Asset._from_guild_icon(self._state, self.id, self._icon)

    @property
    def banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's banner asset, if available."""
        if self._banner is None:
            return None
        return Asset._from_guild_image(self._state, self.id, self._banner, path="banners")

    @property
    def splash(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's invite splash asset, if available."""
        if self._splash is None:
            return None
        return Asset._from_guild_image(self._state, self.id, self._splash, path="splashes")

    @property
    def discovery_splash(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's discovery splash asset, if available."""
        if self._discovery_splash is None:
            return None
        return Asset._from_guild_image(
            self._state, self.id, self._discovery_splash, path="discovery-splashes"
        )

    @property
    def member_count(self) -> Optional[int]:
        """Optional[:class:`int`]: Returns the true member count, if available.

        .. warning::

            Due to a Discord limitation, in order for this attribute to remain up-to-date and
            accurate, it requires :attr:`Intents.members` to be specified.

        """
        return getattr(self, "_member_count", None)

    @property
    def chunked(self) -> bool:
        """:class:`bool`: Returns a boolean indicating if the guild is "chunked".

        A chunked guild means that :attr:`member_count` is equal to the
        number of members stored in the internal :attr:`members` cache.

        If this value returns ``False``, then you should request for
        offline members.
        """
        count = getattr(self, "_member_count", None)
        if count is None:
            return False
        return count == len(self._members)

    @property
    def shard_id(self) -> int:
        """:class:`int`: Returns the shard ID for this guild if applicable."""
        count = self._state.shard_count
        if count is None:
            return 0
        return (self.id >> 22) % count

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the guild's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def get_member_named(self, name: str, /) -> Optional[Member]:
        """Returns the first member found that matches the name provided.

        The name can have an optional discriminator argument, e.g. "Jake#0001"
        or "Jake" will both do the lookup. However the former will give a more
        precise result. Note that the discriminator must have all 4 digits
        for this to work.

        If a nickname is passed, then it is looked up via the nickname. Note
        however, that a nickname + discriminator combo will not lookup the nickname
        but rather the username + discriminator combo due to nickname + discriminator
        not being unique.

        If no member is found, ``None`` is returned.

        Parameters
        ----------
        name: :class:`str`
            The name of the member to lookup with an optional discriminator.

        Returns
        -------
        Optional[:class:`Member`]
            The member in this guild with the associated name. If not found
            then ``None`` is returned.
        """

        result = None
        members = self.members
        if len(name) > 5 and name[-5] == "#":
            # The 5 length is checking to see if #0000 is in the string,
            # as a#0000 has a length of 6, the minimum for a potential
            # discriminator lookup.
            potential_discriminator = name[-4:]

            # do the actual lookup and return if found
            # if it isn't found then we'll do a full name lookup below.
            result = utils.get(members, name=name[:-5], discriminator=potential_discriminator)
            if result is not None:
                return result

        def pred(m: Member) -> bool:
            return name in {m.nick, m.name}

        return utils.find(pred, members)

    def _create_channel(
        self,
        name: str,
        channel_type: ChannelType,
        overwrites: Dict[Union[Role, Member], PermissionOverwrite] = MISSING,
        category: Optional[Snowflake] = None,
        **options: Any,
    ):
        if overwrites is MISSING:
            overwrites = {}
        elif not isinstance(overwrites, dict):
            raise InvalidArgument("overwrites parameter expects a dict.")

        perms = []
        for target, perm in overwrites.items():
            if not isinstance(perm, PermissionOverwrite):
                raise InvalidArgument(
                    f"Expected PermissionOverwrite received {perm.__class__.__name__}"
                )

            allow, deny = perm.pair()
            payload = {"allow": allow.value, "deny": deny.value, "id": target.id}

            if isinstance(target, Role):
                payload["type"] = abc._Overwrites.ROLE
            else:
                payload["type"] = abc._Overwrites.MEMBER

            perms.append(payload)

        parent_id = category.id if category else None
        return self._state.http.create_channel(
            self.id,
            channel_type.value,
            name=name,
            parent_id=parent_id,
            permission_overwrites=perms,
            **options,
        )

    async def create_text_channel(
        self,
        name: str,
        *,
        reason: Optional[str] = None,
        category: Optional[CategoryChannel] = None,
        position: int = MISSING,
        topic: str = MISSING,
        slowmode_delay: int = MISSING,
        nsfw: bool = MISSING,
        overwrites: Dict[Union[Role, Member], PermissionOverwrite] = MISSING,
        default_thread_slowmode_delay: int = MISSING,
    ) -> TextChannel:
        """|coro|

        Creates a :class:`TextChannel` for the guild.

        Note that you need the :attr:`~Permissions.manage_channels` permission
        to create the channel.

        The ``overwrites`` parameter can be used to create a 'secret'
        channel upon creation. This parameter expects a :class:`dict` of
        overwrites with the target (either a :class:`Member` or a :class:`Role`)
        as the key and a :class:`PermissionOverwrite` as the value.

        .. note::

            Creating a channel of a specified position will not update the position of
            other channels to follow suit. A follow-up call to :meth:`~TextChannel.edit`
            will be required to update the position of the channel in the channel list.

        Examples
        --------

        Creating a basic channel:

        .. code-block:: python3

            channel = await guild.create_text_channel('cool-channel')

        Creating a "secret" channel:

        .. code-block:: python3

            overwrites = {
                guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
                guild.me: nextcord.PermissionOverwrite(read_messages=True)
            }

            channel = await guild.create_text_channel('secret', overwrites=overwrites)

        Parameters
        ----------
        name: :class:`str`
            The channel's name.
        overwrites: Dict[Union[:class:`Role`, :class:`Member`], :class:`PermissionOverwrite`]
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply upon creation of a channel.
            Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        topic: :class:`str`
            The new channel's topic.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
            The maximum value possible is ``21600``.
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`TextChannel`
            The channel that was just created.
        """

        options = {}
        if position is not MISSING:
            options["position"] = position

        if topic is not MISSING:
            options["topic"] = topic

        if slowmode_delay is not MISSING:
            options["rate_limit_per_user"] = slowmode_delay

        if nsfw is not MISSING:
            options["nsfw"] = nsfw

        if default_thread_slowmode_delay is not MISSING:
            options["default_thread_rate_limit_per_user"] = default_thread_slowmode_delay

        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.text,
            category=category,
            reason=reason,
            **options,
        )
        channel = TextChannel(state=self._state, guild=self, data=data)  # type: ignore
        # payload *should* contain all text channel info

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_voice_channel(
        self,
        name: str,
        *,
        reason: Optional[str] = None,
        category: Optional[CategoryChannel] = None,
        position: int = MISSING,
        bitrate: int = MISSING,
        user_limit: int = MISSING,
        rtc_region: Optional[VoiceRegion] = MISSING,
        video_quality_mode: VideoQualityMode = MISSING,
        overwrites: Dict[Union[Role, Member], PermissionOverwrite] = MISSING,
    ) -> VoiceChannel:
        """|coro|

        This is similar to :meth:`create_text_channel` except makes a :class:`VoiceChannel` instead.

        Parameters
        ----------
        name: :class:`str`
            The channel's name.
        overwrites: Dict[Union[:class:`Role`, :class:`Member`], :class:`PermissionOverwrite`]
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply upon creation of a channel.
            Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        bitrate: :class:`int`
            The channel's preferred audio bitrate in bits per second.
        user_limit: :class:`int`
            The channel's limit for number of members that can be in a voice channel.
        rtc_region: Optional[:class:`VoiceRegion`]
            The region for the voice channel's voice communication.
            A value of ``None`` indicates automatic voice region detection.

            .. versionadded:: 1.7
        video_quality_mode: :class:`VideoQualityMode`
            The camera video quality for the voice channel's participants.

            .. versionadded:: 2.0
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`VoiceChannel`
            The channel that was just created.
        """
        options = {}
        if position is not MISSING:
            options["position"] = position

        if bitrate is not MISSING:
            options["bitrate"] = bitrate

        if user_limit is not MISSING:
            options["user_limit"] = user_limit

        if rtc_region is not MISSING:
            options["rtc_region"] = None if rtc_region is None else str(rtc_region)

        if video_quality_mode is not MISSING:
            options["video_quality_mode"] = video_quality_mode.value

        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.voice,
            category=category,
            reason=reason,
            **options,
        )
        channel = VoiceChannel(state=self._state, guild=self, data=data)  # type: ignore
        # payload *should* contain all voice channel info

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_stage_channel(
        self,
        name: str,
        *,
        topic: str,
        position: int = MISSING,
        overwrites: Dict[Union[Role, Member], PermissionOverwrite] = MISSING,
        category: Optional[CategoryChannel] = None,
        bitrate: Optional[int] = None,
        user_limit: Optional[int] = None,
        nsfw: Optional[bool] = None,
        rtc_region: Optional[VoiceRegion] = MISSING,
        video_quality_mode: Optional[VideoQualityMode] = None,
        reason: Optional[str] = None,
    ) -> StageChannel:
        """|coro|

        This is similar to :meth:`create_text_channel` except makes a :class:`StageChannel` instead.

        .. versionadded:: 1.7

        Parameters
        ----------
        name: :class:`str`
            The channel's name.
        topic: :class:`str`
            The new channel's topic.
        overwrites: Dict[Union[:class:`Role`, :class:`Member`], :class:`PermissionOverwrite`]
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply upon creation of a channel.
            Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        bitrate: Optional[:class:`int`]
            The channel's preferred audio bitrate in bits per second.

            .. versionadded:: 2.6
        user_limit: :class:`int`
            The channel's limit for number of members that can be in a voice channel.

            .. versionadded:: 2.6
        rtc_region: Optional[:class:`VoiceRegion`]
            The region for the voice channel's voice communication.
            A value of ``None`` indicates automatic voice region detection.

            .. versionadded:: 2.6
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.

            .. versionadded:: 2.6
        video_quality_mode: :class:`VideoQualityMode`
            The camera video quality for the voice channel's participants.

            .. versionadded:: 2.6
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`StageChannel`
            The channel that was just created.
        """

        options: Dict[str, Any] = {
            "topic": topic,
        }
        if position is not MISSING:
            options["position"] = position

        if bitrate is not None:
            options["bitrate"] = bitrate

        if user_limit is not None:
            options["user_limit"] = user_limit

        if rtc_region is not MISSING:
            options["rtc_region"] = None if rtc_region is None else str(rtc_region)

        if nsfw is not None:
            options["nsfw"] = nsfw

        if video_quality_mode is not None:
            options["video_quality_mode"] = video_quality_mode.value

        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.stage_voice,
            category=category,
            reason=reason,
            **options,
        )
        channel = StageChannel(state=self._state, guild=self, data=data)  # type: ignore
        # payload *should* contain all stage channel info

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_category(
        self,
        name: str,
        *,
        overwrites: Dict[Union[Role, Member], PermissionOverwrite] = MISSING,
        reason: Optional[str] = None,
        position: int = MISSING,
    ) -> CategoryChannel:
        """|coro|

        Same as :meth:`create_text_channel` except makes a :class:`CategoryChannel` instead.

        .. note::

            The ``category`` parameter is not supported in this function since categories
            cannot have categories.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`CategoryChannel`
            The channel that was just created.
        """
        options: Dict[str, Any] = {}
        if position is not MISSING:
            options["position"] = position

        data = await self._create_channel(
            name, overwrites=overwrites, channel_type=ChannelType.category, reason=reason, **options
        )
        channel = CategoryChannel(state=self._state, guild=self, data=data)  # type: ignore
        # payload *should* contain all category channel info

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_forum_channel(
        self,
        name: str,
        *,
        topic: str,
        position: int = MISSING,
        overwrites: Dict[Union[Role, Member], PermissionOverwrite] = MISSING,
        category: Optional[CategoryChannel] = None,
        default_thread_slowmode_delay: int = MISSING,
        default_reaction: Optional[Union[Emoji, PartialEmoji, str]] = MISSING,
        available_tags: List[ForumTag] = MISSING,
        reason: Optional[str] = None,
        default_sort_order: SortOrderType = MISSING,
        default_forum_layout: Optional[ForumLayoutType] = None,
    ) -> ForumChannel:
        """|coro|

        This is similar to :meth:`create_text_channel` except makes a :class:`ForumChannel` instead.

        .. versionadded:: 2.1

        .. versionchanged:: 2.5

            Added the ``default_forum_layout`` parameter.

        Parameters
        ----------
        name: :class:`str`
            The channel's name.
        topic: :class:`str`
            The new channel's topic.
        overwrites: Dict[Union[:class:`Role`, :class:`Member`], :class:`PermissionOverwrite`]
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply upon creation of a channel.
            Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.
        default_sort_order: Optional[:class:`SortOrderType`]
            The default sort order used to sort posts in this channel.

            .. versionadded:: 2.3
        default_thread_slowmode_delay: :class:`int`
            The default slowmode delay for threads created in this channel.
            Must be between ``0`` and ``21600``.

            .. versionadded:: 2.4
        default_reaction: Optional[Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`]]
            The default reaction for threads created in this channel.

            .. versionadded:: 2.4
        available_tags: List[:class:`ForumTag`]
            The available tags for threads created in this channel.

            .. versionadded:: 2.4
        default_forum_layout: Optional[:class:`ForumLayoutType`]
            The default layout type used to display posts in this forum.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`ForumChannel`
            The channel that was just created.
        """

        options: Dict[str, Any] = {
            "topic": topic,
        }
        if position is not MISSING:
            options["position"] = position

        if default_sort_order is not MISSING:
            options["default_sort_order"] = default_sort_order.value

        if default_thread_slowmode_delay is not MISSING:
            options["default_thread_rate_limit_per_user"] = default_thread_slowmode_delay

        if available_tags is not MISSING:
            options["available_tags"] = [tag.payload for tag in available_tags]

        if default_reaction is not MISSING:
            if isinstance(default_reaction, str):
                default_reaction = PartialEmoji.from_str(default_reaction)

            if default_reaction is None:
                options["default_reaction_emoji"] = None
            else:
                options["default_reaction_emoji"] = (
                    {
                        "emoji_id": default_reaction.id,
                    }
                    if default_reaction.id is not None
                    else {
                        "emoji_name": default_reaction.name,
                    }
                )

        if default_forum_layout is not None:
            options["default_forum_layout"] = default_forum_layout.value

        data = await self._create_channel(
            name,
            overwrites=overwrites,
            channel_type=ChannelType.forum,
            category=category,
            reason=reason,
            **options,
        )
        channel = ForumChannel(state=self._state, guild=self, data=data)  # type: ignore
        # payload *should* contain all forum channel info

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    create_category_channel = create_category

    async def leave(self) -> None:
        """|coro|

        Leaves the guild.

        .. note::

            You cannot leave the guild that you own, you must delete it instead
            via :meth:`delete`.

        Raises
        ------
        HTTPException
            Leaving the guild failed.
        """
        await self._state.http.leave_guild(self.id)

    async def delete(self) -> None:
        """|coro|

        Deletes the guild. You must be the guild owner to delete the
        guild.

        Raises
        ------
        HTTPException
            Deleting the guild failed.
        Forbidden
            You do not have permissions to delete the guild.
        """

        await self._state.http.delete_guild(self.id)

    async def edit(
        self,
        *,
        reason: Optional[str] = MISSING,
        name: str = MISSING,
        description: Optional[str] = MISSING,
        icon: Optional[Union[bytes, Asset, Attachment, File]] = MISSING,
        banner: Optional[Union[bytes, Asset, Attachment, File]] = MISSING,
        splash: Optional[Union[bytes, Asset, Attachment, File]] = MISSING,
        discovery_splash: Optional[Union[bytes, Asset, Attachment, File]] = MISSING,
        community: bool = MISSING,
        region: Optional[Union[str, VoiceRegion]] = MISSING,
        afk_channel: Optional[VoiceChannel] = MISSING,
        owner: Snowflake = MISSING,
        afk_timeout: int = MISSING,
        default_notifications: NotificationLevel = MISSING,
        verification_level: VerificationLevel = MISSING,
        explicit_content_filter: ContentFilter = MISSING,
        vanity_code: str = MISSING,
        system_channel: Optional[TextChannel] = MISSING,
        system_channel_flags: SystemChannelFlags = MISSING,
        preferred_locale: str = MISSING,
        rules_channel: Optional[TextChannel] = MISSING,
        public_updates_channel: Optional[TextChannel] = MISSING,
        invites_disabled: bool = MISSING,
        premium_progress_bar_enabled: bool = MISSING,
    ) -> Guild:
        r"""|coro|

        Edits the guild.

        You must have the :attr:`~Permissions.manage_guild` permission
        to edit the guild.

        .. versionchanged:: 1.4
            The ``rules_channel`` and ``public_updates_channel`` keyword-only parameters were added.

        .. versionchanged:: 2.0
            The ``discovery_splash`` and ``community`` keyword-only parameters were added.

        .. versionchanged:: 2.0
            The newly updated guild is returned.

        .. versionchanged:: 2.1
            The ``icon``, ``banner``, ``splash``, ``discovery_splash``
            parameters now accept :class:`File`, :class:`Attachment`, and :class:`Asset`.

        .. versionchanged:: 2.4
            The ``invites_disabled`` parameter has been added.

        .. versionchanged:: 2.6
            The ``premium_progress_bar_enabled`` parameter has been added.

        Parameters
        ----------
        name: :class:`str`
            The new name of the guild.
        description: Optional[:class:`str`]
            The new description of the guild. Could be ``None`` for no description.
            This is only available to guilds that contain ``PUBLIC`` in :attr:`Guild.features`.
        icon: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the icon. Only PNG/JPEG is supported. GIF is only available to guilds that contain
            ``ANIMATED_ICON`` in :attr:`Guild.features`. Could be ``None`` to denote removal of the icon.
        banner: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the banner. Could be ``None`` to denote removal of the banner.
            This is only available to guilds that contain ``BANNER`` in :attr:`Guild.features`.
        splash: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the invite splash. Only PNG/JPEG supported. Could be ``None`` to denote removing the
            splash. This is only available to guilds that contain ``INVITE_SPLASH`` in :attr:`Guild.features`.
        discovery_splash: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the discovery splash. Only PNG/JPEG supported. Could be ``None`` to denote removing the
            splash. This is only available to guilds that contain ``DISCOVERABLE`` in :attr:`Guild.features`.
        community: :class:`bool`
            Whether the guild should be a Community guild. If set to ``True``\, both ``rules_channel``
            and ``public_updates_channel`` parameters are required.
        region: Union[:class:`str`, :class:`VoiceRegion`]
            The new region for the guild's voice communication.
        afk_channel: Optional[:class:`VoiceChannel`]
            The new channel that is the AFK channel. Could be ``None`` for no AFK channel.
        afk_timeout: :class:`int`
            The number of seconds until someone is moved to the AFK channel.
        owner: :class:`Member`
            The new owner of the guild to transfer ownership to. Note that you must
            be owner of the guild to do this.
        verification_level: :class:`VerificationLevel`
            The new verification level for the guild.
        default_notifications: :class:`NotificationLevel`
            The new default notification level for the guild.
        explicit_content_filter: :class:`ContentFilter`
            The new explicit content filter for the guild.
        vanity_code: :class:`str`
            The new vanity code for the guild.
        system_channel: Optional[:class:`TextChannel`]
            The new channel that is used for the system channel. Could be ``None`` for no system channel.
        system_channel_flags: :class:`SystemChannelFlags`
            The new system channel settings to use with the new system channel.
        preferred_locale: :class:`str`
            The new preferred locale for the guild. Used as the primary language in the guild.
            If set, this must be an ISO 639 code, e.g. ``en-US`` or ``ja`` or ``zh-CN``.
        rules_channel: Optional[:class:`TextChannel`]
            The new channel that is used for rules. This is only available to
            guilds that contain ``PUBLIC`` in :attr:`Guild.features`. Could be ``None`` for no rules
            channel.
        public_updates_channel: Optional[:class:`TextChannel`]
            The new channel that is used for public updates from Discord. This is only available to
            guilds that contain ``PUBLIC`` in :attr:`Guild.features`. Could be ``None`` for no
            public updates channel.
        invites_disabled: :class:`bool`
            Whether the invites should be paused for the guild.
            This will prevent new users from joining said guild.
        premium_progress_bar_enabled: :class:`bool`
            Whether the premium guild boost progress bar is enabled.
        reason: Optional[:class:`str`]
            The reason for editing this guild. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the guild.
        HTTPException
            Editing the guild failed.
        InvalidArgument
            The image format passed in to ``icon`` is invalid. It must be
            PNG or JPG. This is also raised if you are not the owner of the
            guild and request an ownership transfer.

        Returns
        -------
        :class:`Guild`
            The newly updated guild. Note that this has the same limitations as
            mentioned in :meth:`Client.fetch_guild` and may not have full data.
        """

        http = self._state.http

        if vanity_code is not MISSING:
            await http.change_vanity_code(self.id, vanity_code, reason=reason)

        fields: Dict[str, Any] = {}
        if name is not MISSING:
            fields["name"] = name

        if description is not MISSING:
            fields["description"] = description

        if preferred_locale is not MISSING:
            fields["preferred_locale"] = preferred_locale

        if afk_timeout is not MISSING:
            fields["afk_timeout"] = afk_timeout

        if icon is not MISSING:
            fields["icon"] = await utils.obj_to_base64_data(icon)

        if banner is not MISSING:
            fields["banner"] = await utils.obj_to_base64_data(banner)

        if splash is not MISSING:
            fields["splash"] = await utils.obj_to_base64_data(splash)

        if discovery_splash is not MISSING:
            fields["discovery_splash"] = await utils.obj_to_base64_data(discovery_splash)

        if default_notifications is not MISSING:
            if not isinstance(default_notifications, NotificationLevel):
                raise InvalidArgument(
                    "default_notifications field must be of type NotificationLevel"
                )
            fields["default_message_notifications"] = default_notifications.value

        if afk_channel is not MISSING:
            if afk_channel is None:
                fields["afk_channel_id"] = afk_channel
            else:
                fields["afk_channel_id"] = afk_channel.id

        if system_channel is not MISSING:
            if system_channel is None:
                fields["system_channel_id"] = system_channel
            else:
                fields["system_channel_id"] = system_channel.id

        if rules_channel is not MISSING:
            if rules_channel is None:
                fields["rules_channel_id"] = rules_channel
            else:
                fields["rules_channel_id"] = rules_channel.id

        if public_updates_channel is not MISSING:
            if public_updates_channel is None:
                fields["public_updates_channel_id"] = public_updates_channel
            else:
                fields["public_updates_channel_id"] = public_updates_channel.id

        if owner is not MISSING:
            if self.owner_id != self._state.self_id:
                raise InvalidArgument("To transfer ownership you must be the owner of the guild.")

            fields["owner_id"] = owner.id

        if region is not MISSING:
            fields["region"] = str(region)

        if verification_level is not MISSING:
            if not isinstance(verification_level, VerificationLevel):
                raise InvalidArgument("verification_level field must be of type VerificationLevel")

            fields["verification_level"] = verification_level.value

        if explicit_content_filter is not MISSING:
            if not isinstance(explicit_content_filter, ContentFilter):
                raise InvalidArgument("explicit_content_filter field must be of type ContentFilter")

            fields["explicit_content_filter"] = explicit_content_filter.value

        if system_channel_flags is not MISSING:
            if not isinstance(system_channel_flags, SystemChannelFlags):
                raise InvalidArgument(
                    "system_channel_flags field must be of type SystemChannelFlags"
                )

            fields["system_channel_flags"] = system_channel_flags.value

        if premium_progress_bar_enabled is not MISSING:
            fields["premium_progress_bar_enabled"] = premium_progress_bar_enabled

        if community is not MISSING:
            features = []
            if community:
                if "rules_channel_id" in fields and "public_updates_channel_id" in fields:
                    features.append("COMMUNITY")
                else:
                    raise InvalidArgument(
                        "community field requires both rules_channel and public_updates_channel fields to be provided"
                    )

            fields["features"] = features

        if invites_disabled is not MISSING:
            features = self.features.copy()

            if invites_disabled:
                features.append("INVITES_DISABLED")
            elif "INVITES_DISABLED" in features:
                features.remove("INVITES_DISABLED")

            fields["features"] = features

        data = await http.edit_guild(self.id, reason=reason, **fields)
        return Guild(data=data, state=self._state)

    async def fetch_channels(self) -> Sequence[GuildChannel]:
        """|coro|

        Retrieves all :class:`abc.GuildChannel` that the guild has.

        .. note::

            This method is an API call. For general usage, consider :attr:`channels` instead.

        .. versionadded:: 1.2

        Raises
        ------
        InvalidData
            An unknown channel type was received from Discord.
        HTTPException
            Retrieving the channels failed.

        Returns
        -------
        Sequence[:class:`abc.GuildChannel`]
            All channels in the guild.
        """
        data = await self._state.http.get_all_guild_channels(self.id)

        def convert(d):
            factory, _ = _guild_channel_factory(d["type"])
            if factory is None:
                raise InvalidData("Unknown channel type {type} for channel ID {id}.".format_map(d))

            return factory(guild=self, state=self._state, data=d)

        return [convert(d) for d in data]

    async def active_threads(self) -> List[Thread]:
        """|coro|

        Returns a list of active :class:`Thread` that the client can access.

        This includes both private and public threads.

        .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            The request to get the active threads failed.

        Returns
        -------
        List[:class:`Thread`]
            The active threads
        """
        data = await self._state.http.get_active_threads(self.id)
        threads = [Thread(guild=self, state=self._state, data=d) for d in data.get("threads", [])]
        thread_lookup: Dict[int, Thread] = {thread.id: thread for thread in threads}
        for member in data.get("members", []):
            thread = thread_lookup.get(int(member["id"]))
            if thread is not None:
                thread._add_member(ThreadMember(parent=thread, data=member))

        return threads

    # TODO: Remove Optional typing here when async iterators are refactored
    def fetch_members(
        self, *, limit: Optional[int] = 1000, after: Optional[SnowflakeTime] = None
    ) -> MemberIterator:
        """Retrieves an :class:`.AsyncIterator` that enables receiving the guild's members. In order to use this,
        :meth:`Intents.members` must be enabled.

        .. note::

            This method is an API call. For general usage, consider :attr:`members` instead.

        .. versionadded:: 1.3

        All parameters are optional.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of members to retrieve. Defaults to 1000.
            Pass ``None`` to fetch all members. Note that this is potentially slow.
        after: Optional[Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve members after this date or object.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.

        Raises
        ------
        ClientException
            The members intent is not enabled.
        HTTPException
            Getting the members failed.

        Yields
        ------
        :class:`.Member`
            The member with the member data parsed.

        Examples
        --------

        Usage ::

            async for member in guild.fetch_members(limit=150):
                print(member.name)

        Flattening into a list ::

            members = await guild.fetch_members(limit=150).flatten()
            # members is now a list of Member...
        """

        if not self._state._intents.members:
            raise ClientException("Intents.members must be enabled to use this.")

        return MemberIterator(self, limit=limit, after=after)

    async def fetch_member(self, member_id: int, /) -> Member:
        """|coro|

        Retrieves a :class:`Member` from a guild ID, and a member ID.

        .. note::

            This method is an API call. If you have :attr:`Intents.members` and member cache enabled, consider :meth:`get_member` instead.

        Parameters
        ----------
        member_id: :class:`int`
            The member's ID to fetch from.

        Raises
        ------
        Forbidden
            You do not have access to the guild.
        HTTPException
            Fetching the member failed.

        Returns
        -------
        :class:`Member`
            The member from the member ID.
        """
        data = await self._state.http.get_member(self.id, member_id)
        return Member(data=data, state=self._state, guild=self)

    async def fetch_ban(self, user: Snowflake) -> BanEntry:
        """|coro|

        Retrieves the :class:`BanEntry` for a user.

        You must have the :attr:`~Permissions.ban_members` permission
        to get this information.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
            The user to get ban information from.

        Raises
        ------
        Forbidden
            You do not have proper permissions to get the information.
        NotFound
            This user is not banned.
        HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        :class:`BanEntry`
            The :class:`BanEntry` object for the specified user.
        """
        data: BanPayload = await self._state.http.get_ban(user.id, self.id)
        return BanEntry(user=User(state=self._state, data=data["user"]), reason=data["reason"])

    async def fetch_channel(self, channel_id: int, /) -> Union[GuildChannel, Thread]:
        """|coro|

        Retrieves a :class:`.abc.GuildChannel` or :class:`.Thread` with the specified ID.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_channel_or_thread` instead.

        .. versionadded:: 2.0

        Raises
        ------
        :exc:`.InvalidData`
            An unknown channel type was received from Discord
            or the guild the channel belongs to is not the same
            as the one in this object points to.
        :exc:`.HTTPException`
            Retrieving the channel failed.
        :exc:`.NotFound`
            Invalid Channel ID.
        :exc:`.Forbidden`
            You do not have permission to fetch this channel.

        Returns
        -------
        Union[:class:`.abc.GuildChannel`, :class:`.Thread`]
            The channel from the ID.
        """
        data = await self._state.http.get_channel(channel_id)

        factory, ch_type = _threaded_guild_channel_factory(data["type"])
        if factory is None:
            raise InvalidData("Unknown channel type {type} for channel ID {id}.".format_map(data))

        if ch_type in (ChannelType.group, ChannelType.private):
            raise InvalidData("Channel ID resolved to a private channel")

        if TYPE_CHECKING:
            data = cast(GuildChannelPayload, data)

        guild_id = int(data["guild_id"])
        if self.id != guild_id:
            raise InvalidData("Guild ID resolved to a different guild")

        channel: GuildChannel = factory(guild=self, state=self._state, data=data)  # type: ignore
        return channel

    def bans(
        self,
        *,
        limit: Optional[int] = 1000,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
    ) -> BanIterator:
        """Returns an :class:`~nextcord.AsyncIterator` that enables receiving the destination's bans.

        You must have the :attr:`~Permissions.ban_members` permission to get this information.

        .. versionchanged:: 2.0
            Due to a breaking change in Discord's API, this now returns an :class:`~nextcord.AsyncIterator` instead of a :class:`list`.

        Examples
        --------

        Usage ::

            counter = 0
            async for ban in guild.bans(limit=200):
                if not ban.user.bot:
                    counter += 1

        Flattening into a list: ::

            bans = await guild.bans(limit=123).flatten()
            # bans is now a list of BanEntry...

        All parameters are optional.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of bans to retrieve.
            If ``None``, it retrieves every ban in the guild. Note, however,
            that this would make a slow operation.
            Defaults to 1000.
        before: Optional[:class:`~nextcord.abc.Snowflake`]
            Retrieve bans before this user.
        after: Optional[:class:`~nextcord.abc.Snowflake`]
            Retrieve bans after this user.

        Raises
        ------
        ~nextcord.Forbidden
            You do not have permissions to get the bans.
        ~nextcord.HTTPException
            An error occurred while fetching the bans.

        Yields
        ------
        :class:`~nextcord.BanEntry`
            The ban with the ban data parsed.
        """

        return BanIterator(self, limit=limit, before=before, after=after)

    async def prune_members(
        self,
        *,
        days: int,
        compute_prune_count: bool = True,
        roles: List[Snowflake] = MISSING,
        reason: Optional[str] = None,
    ) -> Optional[int]:
        r"""|coro|

        Prunes the guild from its inactive members.

        The inactive members are denoted if they have not logged on in
        ``days`` number of days and they have no roles.

        You must have the :attr:`~Permissions.kick_members` permission
        to use this.

        To check how many members you would prune without actually pruning,
        see the :meth:`estimate_pruned_members` function.

        To prune members that have specific roles see the ``roles`` parameter.

        .. versionchanged:: 1.4
            The ``roles`` keyword-only parameter was added.

        Parameters
        ----------
        days: :class:`int`
            The number of days before counting as inactive.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.
        compute_prune_count: :class:`bool`
            Whether to compute the prune count. This defaults to ``True``
            which makes it prone to timeouts in very large guilds. In order
            to prevent timeouts, you must set this to ``False``. If this is
            set to ``False``\, then this function will always return ``None``.
        roles: List[:class:`abc.Snowflake`]
            A list of :class:`abc.Snowflake` that represent roles to include in the pruning process. If a member
            has a role that is not specified, they'll be excluded.

        Raises
        ------
        Forbidden
            You do not have permissions to prune members.
        HTTPException
            An error occurred while pruning members.
        InvalidArgument
            An integer was not passed for ``days``.

        Returns
        -------
        Optional[:class:`int`]
            The number of members pruned. If ``compute_prune_count`` is ``False``
            then this returns ``None``.
        """

        if not isinstance(days, int):
            raise InvalidArgument(
                f"Expected int for ``days``, received {days.__class__.__name__} instead."
            )

        role_ids = [str(role.id) for role in roles] if roles else []

        data = await self._state.http.prune_members(
            self.id, days, compute_prune_count=compute_prune_count, roles=role_ids, reason=reason
        )
        return data["pruned"]

    async def templates(self) -> List[Template]:
        """|coro|

        Gets the list of templates from this guild.

        Requires :attr:`~.Permissions.manage_guild` permissions.

        .. versionadded:: 1.7

        Raises
        ------
        Forbidden
            You don't have permissions to get the templates.

        Returns
        -------
        List[:class:`Template`]
            The templates for this guild.
        """
        from .template import Template

        data = await self._state.http.guild_templates(self.id)
        return [Template(data=d, state=self._state) for d in data]

    async def webhooks(self) -> List[Webhook]:
        """|coro|

        Gets the list of webhooks from this guild.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        Raises
        ------
        Forbidden
            You don't have permissions to get the webhooks.

        Returns
        -------
        List[:class:`Webhook`]
            The webhooks for this guild.
        """

        from .webhook import Webhook

        data = await self._state.http.guild_webhooks(self.id)
        return [Webhook.from_state(d, state=self._state) for d in data]

    async def estimate_pruned_members(
        self, *, days: int, roles: List[Snowflake] = MISSING
    ) -> Optional[int]:
        """|coro|

        Similar to :meth:`prune_members` except instead of actually
        pruning members, it returns how many members it would prune
        from the guild had it been called.

        Parameters
        ----------
        days: :class:`int`
            The number of days before counting as inactive.
        roles: List[:class:`abc.Snowflake`]
            A list of :class:`abc.Snowflake` that represent roles to include in the estimate. If a member
            has a role that is not specified, they'll be excluded.

            .. versionadded:: 1.7

        Raises
        ------
        Forbidden
            You do not have permissions to prune members.
        HTTPException
            An error occurred while fetching the prune members estimate.
        InvalidArgument
            An integer was not passed for ``days``.

        Returns
        -------
        :class:`int`
            The number of members estimated to be pruned.
        """

        if not isinstance(days, int):
            raise InvalidArgument(
                f"Expected int for ``days``, received {days.__class__.__name__} instead."
            )

        role_ids = [str(role.id) for role in roles] if roles else []

        data = await self._state.http.estimate_pruned_members(self.id, days, role_ids)
        return data["pruned"]

    async def invites(self) -> List[Invite]:
        """|coro|

        Returns a list of all active instant invites from the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to get
        this information.

        Raises
        ------
        Forbidden
            You do not have proper permissions to get the information.
        HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        List[:class:`Invite`]
            The list of invites that are currently active.


        .. note::

            This method does not include the Guild's vanity URL.
            To get the vanity URL :class:`Invite`, refer to :meth:`Guild.vanity_invite`.
        """

        data = await self._state.http.invites_from(self.id)
        result = []
        for invite in data:
            channel = self.get_channel(int(invite["channel"]["id"]))
            result.append(Invite(state=self._state, data=invite, guild=self, channel=channel))

        return result

    async def create_template(self, *, name: str, description: str = MISSING) -> Template:
        """|coro|

        Creates a template for the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.7

        Parameters
        ----------
        name: :class:`str`
            The name of the template.
        description: :class:`str`
            The description of the template.
        """
        from .template import Template

        payload: CreateTemplate = {"name": name, "icon": None}

        if description:
            payload["description"] = description

        data = await self._state.http.create_template(self.id, payload)

        return Template(state=self._state, data=data)

    async def create_integration(self, *, type: IntegrationType, id: int) -> None:
        """|coro|

        Attaches an integration to the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.4

        Parameters
        ----------
        type: :class:`str`
            The integration type (e.g. Twitch).
        id: :class:`int`
            The integration ID.

        Raises
        ------
        Forbidden
            You do not have permission to create the integration.
        HTTPException
            The account could not be found.
        """
        await self._state.http.create_integration(self.id, type, id)

    async def integrations(self) -> List[Integration]:
        """|coro|

        Returns a list of all integrations attached to the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.4

        Raises
        ------
        Forbidden
            You do not have permission to create the integration.
        HTTPException
            Fetching the integrations failed.

        Returns
        -------
        List[:class:`Integration`]
            The list of integrations that are attached to the guild.
        """
        data = await self._state.http.get_all_integrations(self.id)

        def convert(d):
            factory, _ = _integration_factory(d["type"])
            return factory(guild=self, data=d)

        return [convert(d) for d in data]

    async def fetch_stickers(self) -> List[GuildSticker]:
        r"""|coro|

        Retrieves a list of all :class:`Sticker`\s for the guild.

        .. versionadded:: 2.0

        .. note::

            This method is an API call. For general usage, consider :attr:`stickers` instead.

        Raises
        ------
        HTTPException
            An error occurred fetching the stickers.

        Returns
        -------
        List[:class:`GuildSticker`]
            The retrieved stickers.
        """
        data = await self._state.http.get_all_guild_stickers(self.id)
        return [GuildSticker(state=self._state, data=d) for d in data]

    async def fetch_sticker(self, sticker_id: int, /) -> GuildSticker:
        """|coro|

        Retrieves a custom :class:`Sticker` from the guild.

        .. versionadded:: 2.0

        .. note::

            This method is an API call.
            For general usage, consider iterating over :attr:`stickers` instead.

        Parameters
        ----------
        sticker_id: :class:`int`
            The sticker's ID.

        Raises
        ------
        NotFound
            The sticker requested could not be found.
        HTTPException
            An error occurred fetching the sticker.

        Returns
        -------
        :class:`GuildSticker`
            The retrieved sticker.
        """
        data = await self._state.http.get_guild_sticker(self.id, sticker_id)
        return GuildSticker(state=self._state, data=data)

    async def create_sticker(
        self,
        *,
        name: str,
        description: Optional[str] = None,
        emoji: str,
        file: File,
        reason: Optional[str] = None,
    ) -> GuildSticker:
        """|coro|

        Creates a :class:`Sticker` for the guild.

        You must have :attr:`~Permissions.manage_emojis_and_stickers` permission to
        do this.

        .. versionadded:: 2.0

        Parameters
        ----------
        name: :class:`str`
            The sticker name. Must be at least 2 characters.
        description: Optional[:class:`str`]
            The sticker's description. Can be ``None``.
        emoji: :class:`str`
            The name of a unicode emoji that represents the sticker's expression.
        file: :class:`File`
            The file of the sticker to upload.
        reason: :class:`str`
            The reason for creating this sticker. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You are not allowed to create stickers.
        HTTPException
            An error occurred creating a sticker.

        Returns
        -------
        :class:`GuildSticker`
            The created sticker.
        """
        if description is None:
            description = ""

        try:
            emoji = unicodedata.name(emoji)
        except TypeError:
            pass
        else:
            emoji = emoji.replace(" ", "_")
        payload: CreateGuildSticker = {
            "name": name,
            "description": description,
            "tags": emoji,
        }

        data = await self._state.http.create_guild_sticker(self.id, payload, file, reason=reason)
        return self._state.store_sticker(self, data)

    async def delete_sticker(self, sticker: Snowflake, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the custom :class:`Sticker` from the guild.

        You must have :attr:`~Permissions.manage_emojis_and_stickers` permission to
        do this.

        .. versionadded:: 2.0

        Parameters
        ----------
        sticker: :class:`abc.Snowflake`
            The sticker you are deleting.
        reason: Optional[:class:`str`]
            The reason for deleting this sticker. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You are not allowed to delete stickers.
        HTTPException
            An error occurred deleting the sticker.
        """
        await self._state.http.delete_guild_sticker(self.id, sticker.id, reason)

    async def fetch_emojis(self) -> List[Emoji]:
        r"""|coro|

        Retrieves all custom :class:`Emoji`\s from the guild.

        .. note::

            This method is an API call. For general usage, consider :attr:`emojis` instead.

        Raises
        ------
        HTTPException
            An error occurred fetching the emojis.

        Returns
        -------
        List[:class:`Emoji`]
            The retrieved emojis.
        """
        data = await self._state.http.get_all_custom_emojis(self.id)
        return [Emoji(guild=self, state=self._state, data=d) for d in data]

    async def fetch_emoji(self, emoji_id: int, /) -> Emoji:
        """|coro|

        Retrieves a custom :class:`Emoji` from the guild.

        .. note::

            This method is an API call.
            For general usage, consider iterating over :attr:`emojis` instead.

        Parameters
        ----------
        emoji_id: :class:`int`
            The emoji's ID.

        Raises
        ------
        NotFound
            The emoji requested could not be found.
        HTTPException
            An error occurred fetching the emoji.

        Returns
        -------
        :class:`Emoji`
            The retrieved emoji.
        """
        data = await self._state.http.get_custom_emoji(self.id, emoji_id)
        return Emoji(guild=self, state=self._state, data=data)

    async def create_custom_emoji(
        self,
        *,
        name: str,
        image: Union[bytes, Asset, Attachment, File],
        roles: List[Role] = MISSING,
        reason: Optional[str] = None,
    ) -> Emoji:
        r"""|coro|

        Creates a custom :class:`Emoji` for the guild.

        There is currently a limit of 50 static and animated emojis respectively per guild,
        unless the guild has the ``MORE_EMOJI`` feature which extends the limit to 200.

        You must have the :attr:`~Permissions.manage_emojis` permission to
        do this.

        .. versionchanged:: 2.1
            The ``image`` parameter now accepts :class:`File`, :class:`Attachment`, and :class:`Asset`.

        Parameters
        ----------
        name: :class:`str`
            The emoji name. Must be at least 2 characters.
        image: Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]
            The :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the image data to use. Only JPG, PNG and GIF images are supported.
        roles: List[:class:`Role`]
            A :class:`list` of :class:`Role`\s that can use this emoji. Leave empty to make it available to everyone.
        reason: Optional[:class:`str`]
            The reason for creating this emoji. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You are not allowed to create emojis.
        HTTPException
            An error occurred creating an emoji.

        Returns
        -------
        :class:`Emoji`
            The created emoji.
        """
        img_base64 = await utils.obj_to_base64_data(image)

        role_ids: SnowflakeList
        role_ids = [role.id for role in roles] if roles else []

        data = await self._state.http.create_custom_emoji(
            self.id, name, img_base64, roles=role_ids, reason=reason
        )
        return self._state.store_emoji(self, data)

    async def delete_emoji(self, emoji: Snowflake, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the custom :class:`Emoji` from the guild.

        You must have :attr:`~Permissions.manage_emojis` permission to
        do this.

        Parameters
        ----------
        emoji: :class:`abc.Snowflake`
            The emoji you are deleting.
        reason: Optional[:class:`str`]
            The reason for deleting this emoji. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You are not allowed to delete emojis.
        HTTPException
            An error occurred deleting the emoji.
        """

        await self._state.http.delete_custom_emoji(self.id, emoji.id, reason=reason)

    async def fetch_roles(self, *, cache: bool = False) -> List[Role]:
        """|coro|

        Retrieves all :class:`Role` that the guild has.

        .. note::

            This method is an API call. For general usage, consider :attr:`roles` instead.

        Parameters
        ----------
        cache: bool
            Whether or not to also update this guilds
            role cache. Defaults to ``False``.

        Raises
        ------
        HTTPException
            Retrieving the roles failed.

        Returns
        -------
        List[:class:`Role`]
            All roles in the guild.
        """
        data = await self._state.http.get_roles(self.id)
        roles = [Role(guild=self, state=self._state, data=d) for d in data]
        if cache:
            self._roles: Dict[int, Role] = {}
            for role in roles:
                self._roles[role.id] = role

        return roles

    @overload
    async def create_role(
        self,
        *,
        reason: Optional[str] = ...,
        name: str = ...,
        permissions: Permissions = ...,
        colour: Union[Colour, int] = ...,
        hoist: bool = ...,
        mentionable: bool = ...,
        icon: Optional[Union[str, bytes, Asset, Attachment, File]] = ...,
    ) -> Role:
        ...

    @overload
    async def create_role(
        self,
        *,
        reason: Optional[str] = ...,
        name: str = ...,
        permissions: Permissions = ...,
        color: Union[Colour, int] = ...,
        hoist: bool = ...,
        mentionable: bool = ...,
        icon: Optional[Union[str, bytes, Asset, Attachment, File]] = ...,
    ) -> Role:
        ...

    async def create_role(
        self,
        *,
        name: str = MISSING,
        permissions: Permissions = MISSING,
        color: Union[Colour, int] = MISSING,
        colour: Union[Colour, int] = MISSING,
        hoist: bool = MISSING,
        mentionable: bool = MISSING,
        icon: Optional[Union[str, bytes, Asset, Attachment, File]] = MISSING,
        reason: Optional[str] = None,
    ) -> Role:
        """|coro|

        Creates a :class:`Role` for the guild.

        All fields are optional.

        You must have the :attr:`~Permissions.manage_roles` permission to
        do this.

        .. versionchanged:: 1.6
            Can now pass ``int`` to ``colour`` keyword-only parameter.

        .. versionchanged:: 2.1
            The ``icon`` parameter now accepts :class:`File`, :class:`Attachment`, and :class:`Asset`.

        Parameters
        ----------
        name: :class:`str`
            The role name. Defaults to 'new role'.
        permissions: :class:`Permissions`
            The permissions to have. Defaults to no permissions.
        colour: Union[:class:`Colour`, :class:`int`]
            The colour for the role. Defaults to :meth:`Colour.default`.
            This is aliased to ``color`` as well.
        hoist: :class:`bool`
            Indicates if the role should be shown separately in the member list.
            Defaults to ``False``.
        mentionable: :class:`bool`
            Indicates if the role should be mentionable by others.
            Defaults to ``False``.
        icon: Optional[Union[:class:`str`, :class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            The icon of the role. Supports unicode emojis and images
        reason: Optional[:class:`str`]
            The reason for creating this role. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have permissions to create the role.
        HTTPException
            Creating the role failed.
        InvalidArgument
            An invalid keyword argument was given.

        Returns
        -------
        :class:`Role`
            The newly created role.
        """
        fields: Dict[str, Any] = {}
        if permissions is not MISSING:
            fields["permissions"] = str(permissions.value)
        else:
            fields["permissions"] = "0"

        actual_colour = colour or color or Colour.default()
        if isinstance(actual_colour, int):
            fields["color"] = actual_colour
        else:
            fields["color"] = actual_colour.value

        if hoist is not MISSING:
            fields["hoist"] = hoist

        if mentionable is not MISSING:
            fields["mentionable"] = mentionable

        if name is not MISSING:
            fields["name"] = name

        if icon is not MISSING:
            if isinstance(icon, str):
                fields["unicode_emoji"] = icon
            else:
                fields["icon"] = await utils.obj_to_base64_data(icon)

        data = await self._state.http.create_role(self.id, reason=reason, **fields)
        return Role(guild=self, data=data, state=self._state)

    async def edit_role_positions(
        self, positions: Dict[Snowflake, int], *, reason: Optional[str] = None
    ) -> List[Role]:
        """|coro|

        Bulk edits a list of :class:`Role` in the guild.

        You must have the :attr:`~Permissions.manage_roles` permission to
        do this.

        .. versionadded:: 1.4

        Example:

        .. code-block:: python3

            positions = {
                bots_role: 1, # penultimate role
                tester_role: 2,
                admin_role: 6
            }

            await guild.edit_role_positions(positions=positions)

        Parameters
        ----------
        positions
            A :class:`dict` of :class:`Role` to :class:`int` to change the positions
            of each given role.
        reason: Optional[:class:`str`]
            The reason for editing the role positions. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have permissions to move the roles.
        HTTPException
            Moving the roles failed.
        InvalidArgument
            An invalid keyword argument was given.

        Returns
        -------
        List[:class:`Role`]
            A list of all the roles in the guild.
        """
        if not isinstance(positions, dict):
            raise InvalidArgument("positions parameter expects a dict.")

        role_positions: List[RolePositionUpdate] = []
        for role, position in positions.items():
            payload: RolePositionUpdate = {"id": role.id, "position": position}

            role_positions.append(payload)

        data = await self._state.http.move_role_position(self.id, role_positions, reason=reason)
        roles: List[Role] = []
        for d in data:
            role = Role(guild=self, data=d, state=self._state)
            roles.append(role)
            self._roles[role.id] = role

        return roles

    async def kick(self, user: Snowflake, *, reason: Optional[str] = None) -> None:
        """|coro|

        Kicks a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.kick_members` permission to
        do this.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
            The user to kick from their guild.
        reason: Optional[:class:`str`]
            The reason the user got kicked.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to kick.
        HTTPException
            Kicking failed.
        """
        await self._state.http.kick(user.id, self.id, reason=reason)

    async def ban(
        self,
        user: Snowflake,
        *,
        reason: Optional[str] = None,
        delete_message_seconds: Optional[int] = None,
        delete_message_days: Optional[Literal[0, 1, 2, 3, 4, 5, 6, 7]] = None,
    ) -> None:
        """|coro|

        Bans a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.ban_members` permission to
        do this.

        For backwards compatibility reasons, by default one day worth of messages will be deleted.

        .. warning::
            delete_message_days is deprecated and will be removed in a future version.
            Use delete_message_seconds instead.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
            The user to ban from their guild.
        delete_message_seconds: Optional[:class:`int`]
            The number of seconds worth of messages to delete from the user
            in the guild. The minimum is 0 and the maximum is 604800 (7 days).

            .. versionadded:: 2.3
        delete_message_days: Optional[:class:`int`]
            The number of days worth of messages to delete from the user
            in the guild. The minimum is 0 and the maximum is 7.

            .. deprecated:: 2.3
        reason: Optional[:class:`str`]
            The reason the user got banned.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to ban.
        HTTPException
            Banning failed.
        """
        if delete_message_days is not None and delete_message_seconds is not None:
            raise InvalidArgument(
                "Cannot pass both delete_message_days and delete_message_seconds."
            )
        if delete_message_days is not None:
            warnings.warn(
                DeprecationWarning(
                    "delete_message_days is deprecated, use delete_message_seconds instead.",
                ),
                stacklevel=2,
            )
            delete_message_seconds = delete_message_days * 24 * 60 * 60
        elif delete_message_seconds is None:
            # Default to one day
            delete_message_seconds = 24 * 60 * 60

        await self._state.http.ban(user.id, self.id, delete_message_seconds, reason=reason)

    async def unban(self, user: Snowflake, *, reason: Optional[str] = None) -> None:
        """|coro|

        Unbans a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.ban_members` permission to
        do this.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
            The user to unban.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to unban.
        HTTPException
            Unbanning failed.
        """
        await self._state.http.unban(user.id, self.id, reason=reason)

    async def vanity_invite(self) -> Optional[Invite]:
        """|coro|

        Returns the guild's special vanity invite.

        The guild must have ``VANITY_URL`` in :attr:`~Guild.features`.

        You must have the :attr:`~Permissions.manage_guild` permission to use
        this as well.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to get this.
        HTTPException
            Retrieving the vanity invite failed.

        Returns
        -------
        Optional[:class:`Invite`]
            The special vanity invite. If ``None`` then the guild does not
            have a vanity invite set.
        """

        # we start with { code: abc }
        payload = await self._state.http.get_vanity_code(self.id)
        if not payload["code"]:
            return None

        # get the vanity URL channel since default channels aren't
        # reliable or a thing anymore
        data = await self._state.http.get_invite(payload["code"])

        channel = self.get_channel(int(data["channel"]["id"]))
        payload["revoked"] = False
        payload["temporary"] = False
        payload["max_uses"] = 0
        payload["max_age"] = 0
        payload["uses"] = payload.get("uses", 0)
        return Invite(state=self._state, data=payload, guild=self, channel=channel)

    # TODO: use MISSING when async iterators get refactored
    def audit_logs(
        self,
        *,
        limit: Optional[int] = 100,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = None,
        user: Optional[Snowflake] = None,
        action: Optional[AuditLogAction] = None,
    ) -> AuditLogIterator:
        """Returns an :class:`AsyncIterator` that enables receiving the guild's audit logs.

        You must have the :attr:`~Permissions.view_audit_log` permission to use this.

        Examples
        --------

        Getting the first 100 entries: ::

            async for entry in guild.audit_logs(limit=100):
                print(f'{entry.user} did {entry.action} to {entry.target}')

        Getting entries for a specific action: ::

            async for entry in guild.audit_logs(action=nextcord.AuditLogAction.ban):
                print(f'{entry.user} banned {entry.target}')

        Getting entries made by a specific user: ::

            entries = await guild.audit_logs(limit=None, user=guild.me).flatten()
            await channel.send(f'I made {len(entries)} moderation actions.')

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of entries to retrieve. If ``None`` retrieve all entries.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve entries before this date or entry.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve entries after this date or entry.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        oldest_first: Optional[:class:`bool`]
            If set to ``True``, return entries in oldest->newest order. Defaults to ``True`` if
            ``after`` is specified, otherwise ``False``.
        user: Optional[:class:`abc.Snowflake`]
            The moderator to filter entries from.
        action: Optional[:class:`AuditLogAction`]
            The action to filter with.

        Raises
        ------
        Forbidden
            You are not allowed to fetch audit logs
        HTTPException
            An error occurred while fetching the audit logs.

        Yields
        ------
        :class:`AuditLogEntry`
            The audit log entry.
        """
        user_id = user.id if user is not None else None

        return AuditLogIterator(
            self,
            before=before,
            after=after,
            limit=limit,
            oldest_first=oldest_first,
            user_id=user_id,
            action_type=action,
        )

    async def widget(self) -> Widget:
        """|coro|

        Returns the widget of the guild.

        .. note::

            The guild must have the widget enabled to get this information.

        Raises
        ------
        Forbidden
            The widget for this guild is disabled.
        HTTPException
            Retrieving the widget failed.

        Returns
        -------
        :class:`Widget`
            The guild's widget.
        """
        data = await self._state.http.get_widget(self.id)

        return Widget(state=self._state, data=data)

    async def edit_widget(
        self, *, enabled: bool = MISSING, channel: Optional[Snowflake] = MISSING
    ) -> None:
        """|coro|

        Edits the widget of the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        use this

        .. versionadded:: 2.0

        Parameters
        ----------
        enabled: :class:`bool`
            Whether to enable the widget for the guild.
        channel: Optional[:class:`~nextcord.abc.Snowflake`]
            The new widget channel. ``None`` removes the widget channel.

        Raises
        ------
        Forbidden
            You do not have permission to edit the widget.
        HTTPException
            Editing the widget failed.
        """
        payload = {}
        if channel is not MISSING:
            payload["channel_id"] = None if channel is None else channel.id
        if enabled is not MISSING:
            payload["enabled"] = enabled

        await self._state.http.edit_widget(self.id, payload=payload)

    async def chunk(self, *, cache: bool = True) -> Optional[List[Member]]:
        """|coro|

        Requests all members that belong to this guild. In order to use this,
        :meth:`Intents.members` must be enabled.

        This is a websocket operation and can be slow.

        .. versionadded:: 1.5

        Parameters
        ----------
        cache: :class:`bool`
            Whether to cache the members as well.

        Raises
        ------
        ClientException
            The members intent is not enabled.

        Returns
        -------
        Optional[List[:class:`Member`]]
             Returns a list of all the members in the guild.
        """

        if not self._state._intents.members:
            raise ClientException("Intents.members must be enabled to use this.")

        if not self._state.is_guild_evicted(self):
            members = await self._state.chunk_guild(self, cache=cache)
            if isinstance(members, Future):
                members = await members

            return members
        return None

    async def query_members(
        self,
        query: Optional[str] = None,
        *,
        limit: int = 5,
        user_ids: Optional[List[int]] = None,
        presences: bool = False,
        cache: bool = True,
    ) -> List[Member]:
        """|coro|

        Request members that belong to this guild whose username starts with
        the query given.

        This is a websocket operation and can be slow.

        .. versionadded:: 1.3

        Parameters
        ----------
        query: Optional[:class:`str`]
            The string that the username's start with.
        limit: :class:`int`
            The maximum number of members to send back. This must be
            a number between 5 and 100.
        presences: :class:`bool`
            Whether to request for presences to be provided. This defaults
            to ``False``.

            .. versionadded:: 1.6

        cache: :class:`bool`
            Whether to cache the members internally. This makes operations
            such as :meth:`get_member` work for those that matched.
        user_ids: Optional[List[:class:`int`]]
            List of user IDs to search for. If the user ID is not in the guild then it won't be returned.

            .. versionadded:: 1.4


        Raises
        ------
        asyncio.TimeoutError
            The query timed out waiting for the members.
        ValueError
            Invalid parameters were passed to the function
        ClientException
            The presences intent is not enabled.

        Returns
        -------
        List[:class:`Member`]
            The list of members that have matched the query.
        """

        if presences and not self._state._intents.presences:
            raise ClientException("Intents.presences must be enabled to use this.")

        if not query:
            if query == "":
                raise ValueError("Cannot pass empty query string.")

            if user_ids is None:
                raise ValueError("Must pass either query or user_ids")

        if user_ids is not None and query is not None:
            raise ValueError("Cannot pass both query and user_ids")

        if user_ids is not None and not user_ids:
            raise ValueError("user_ids must contain at least 1 value")

        limit = min(100, limit or 5)
        return await self._state.query_members(
            self, query=query, limit=limit, user_ids=user_ids, presences=presences, cache=cache
        )

    async def change_voice_state(
        self,
        *,
        channel: Optional[VocalGuildChannel],
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        """|coro|

        Changes client's voice state in the guild.

        .. versionadded:: 1.4

        Parameters
        ----------
        channel: Optional[:class:`VoiceChannel`]
            Channel the client wants to join. Use ``None`` to disconnect.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.
        """
        ws = self._state._get_websocket(self.id)
        channel_id = channel.id if channel else None
        await ws.voice_state(self.id, channel_id, self_mute, self_deaf)

    def fetch_scheduled_events(self, *, with_users: bool = False) -> ScheduledEventIterator:
        """Retrieves an :class:`.AsyncIterator` that enables receiving scheduled
        events on this guild

        .. note::

            This method is an API call. For general usage, consider
            :attr:`scheduled_events` instead.

        .. versionadded:: 2.0

        Parameters
        ----------
        with_users: Optional[:class:`bool`]
            If the event should be received with :attr:`ScheduledEvent.users`
            This defaults to ``False`` - the events' :attr:`~ScheduledEvent.users`
            will be empty.

        Raises
        ------
        HTTPException
            Getting the events failed.

        Yields
        ------
        :class:`.ScheduledEvent`
            The event with users if applicable

        Examples
        --------

        Usage ::

            async for event in guild.fetch_scheduled_events():
                print(event.name)

        Flattening into a list ::

            events = await guild.fetch_scheduled_events().flatten()
            # events is now a list of ScheduledEvent...
        """
        return ScheduledEventIterator(self, with_users=with_users)

    def get_scheduled_event(self, event_id: int) -> Optional[ScheduledEvent]:
        """Get a scheduled event from cache by id.

        .. note::

            This may not return the updated users, use
            :meth:`~Guild.fetch_scheduled_event` if that is desired.

        Parameters
        ----------
        event_id : int
            The scheduled event id to fetch.

        Returns
        -------
        Optional[ScheduledEvent]
            The event object, if found.
        """
        return self._scheduled_events.get(event_id)

    async def fetch_scheduled_event(
        self, event_id: int, *, with_users: bool = False
    ) -> ScheduledEvent:
        """|coro|

        Fetch a scheduled event object.

        .. note::

            This is an api call, if updated users is not needed,
            consisder :meth:`~Guild.get_scheduled_event`

        Parameters
        ----------
        event_id: :class:`int`
            The event id to fetch
        with_users: :class:`bool`
            If the users should be received and cached too, by default False

        Returns
        -------
        :class:`ScheduledEvent`
            The received event object
        """
        event_payload = await self._state.http.get_event(
            self.id, event_id, with_user_count=with_users
        )

        return self._store_scheduled_event(event_payload)

    async def create_scheduled_event(
        self,
        *,
        name: str,
        entity_type: ScheduledEventEntityType,
        start_time: datetime.datetime,
        channel: abc.GuildChannel = MISSING,
        metadata: EntityMetadata = MISSING,
        privacy_level: ScheduledEventPrivacyLevel = ScheduledEventPrivacyLevel.guild_only,
        end_time: datetime.datetime = MISSING,
        description: str = MISSING,
        image: Optional[Union[bytes, Asset, Attachment, File]] = None,
        reason: Optional[str] = None,
    ) -> ScheduledEvent:
        """|coro|

        Create a new scheduled event object.

        .. versionchanged:: 2.1
            The ``image`` parameter now accepts :class:`File`, :class:`Attachment`, and :class:`Asset`.

        Parameters
        ----------
        channel: :class:`abc.GuildChannel`
            The channel the event will happen in, if any
        metadata: :class:`EntityMetadata`
            The metadata for the event
        name: :class:`str`
            The name of the event
        privacy_level: :class:`ScheduledEventPrivacyLevel`
            The privacy level for the event
        start_time: :class:`py:datetime.datetime`
            The scheduled start time
        end_time: :class:`py:datetime.datetime`
            The scheduled end time
        description: :class:`str`
            The description for the event
        entity_type: :class:`ScheduledEventEntityType`
            The type of event
        image: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the cover image.
        reason: Optional[:class:`str`]
            The reason for creating this scheduled event. Shows up in the audit logs.

        Returns
        -------
        :class:`ScheduledEvent`
            The created event object.
        """
        payload: Dict[str, Any] = {
            "name": name,
            "entity_type": entity_type.value,
            "scheduled_start_time": start_time.isoformat(),
        }
        if channel is not MISSING:
            payload["channel_id"] = channel.id
        if metadata is not MISSING:
            payload["entity_metadata"] = metadata.__dict__
        if privacy_level is not MISSING:
            payload["privacy_level"] = privacy_level.value
        if end_time is not MISSING:
            payload["scheduled_end_time"] = end_time.isoformat()
        if description is not MISSING:
            payload["description"] = description
        if image is not None:
            payload["image"] = await utils.obj_to_base64_data(image)

        data = await self._state.http.create_event(self.id, reason=reason, **payload)
        return self._store_scheduled_event(data)

    def get_application_commands(self, rollout: bool = False):
        """Gets all application commands registered for this guild.

        Parameters
        ----------
        rollout: :class:`bool`

        Returns
        -------

        """
        return self._state.get_guild_application_commands(guild_id=self.id, rollout=rollout)

    def add_application_command(
        self, app_cmd: BaseApplicationCommand, overwrite: bool = False, use_rollout: bool = False
    ) -> None:
        app_cmd.add_guild_rollout(self.id)
        self._state.add_application_command(app_cmd, overwrite=overwrite, use_rollout=use_rollout)

    async def deploy_application_commands(
        self,
        data: Optional[List[ApplicationCommandPayload]] = None,
        associate_known: bool = True,
        delete_unknown: bool = True,
        update_known: bool = True,
    ) -> None:
        await self._state.discover_application_commands(
            data=data,
            guild_id=self.id,
            associate_known=associate_known,
            delete_unknown=delete_unknown,
            update_known=update_known,
        )

    async def sync_application_commands(
        self,
        data: Optional[List[ApplicationCommandPayload]] = None,
        *,
        associate_known: bool = True,
        delete_unknown: bool = True,
        update_known: bool = True,
        register_new: bool = True,
    ) -> None:
        """|coro|
        Syncs the locally added application commands with this Guild.

        Parameters
        ----------
        data: Optional[List[:class:`dict`]]
            Data to use when comparing local application commands to what Discord has. Should be a list of application
            command data from Discord. If left as ``None``, it will be fetched if needed. Defaults to ``None``.
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
        # All this does is passthrough to connection state. All documentation updates should also be updated
        # there, and vice versa.
        await self._state.sync_application_commands(
            data=data,
            guild_id=self.id,
            associate_known=associate_known,
            delete_unknown=delete_unknown,
            update_known=update_known,
            register_new=register_new,
        )

    async def rollout_application_commands(
        self,
        associate_known: bool = True,
        delete_unknown: bool = True,
        update_known: bool = True,
        register_new: bool = True,
    ) -> None:
        """|coro|
        Rolls out application commands to the guild, associating, deleting, updating, and/or newly
        registering as needed.

        Parameters
        ----------
        associate_known: :class:`bool`
            Whether commands on Discord that match a locally added command should be associated with each other.
            Defaults to ``True``
        delete_unknown
        update_known
        register_new
        """
        warnings.warn(
            ".rollout_application_commands is deprecated, use .sync_application_commands and set "
            "kwargs in it instead.",
            stacklevel=2,
            category=FutureWarning,
        )
        if self._state.application_id is None:
            raise NotImplementedError("Could not get the current application id")

        guild_payload = await self._state.http.get_guild_commands(
            self._state.application_id, self.id
        )
        await self.deploy_application_commands(
            data=guild_payload,
            associate_known=associate_known,
            delete_unknown=delete_unknown,
            update_known=update_known,
        )
        if register_new:
            await self.register_new_application_commands(data=guild_payload)

    async def delete_unknown_application_commands(
        self, data: Optional[List[ApplicationCommandPayload]] = None
    ) -> None:
        await self._state.delete_unknown_application_commands(data=data, guild_id=self.id)

    async def associate_application_commands(
        self, data: Optional[List[ApplicationCommandPayload]] = None
    ) -> None:
        await self._state.associate_application_commands(data=data, guild_id=self.id)

    async def update_application_commands(
        self, data: Optional[List[ApplicationCommandPayload]] = None
    ) -> None:
        await self._state.update_application_commands(data=data, guild_id=self.id)

    async def register_new_application_commands(
        self, data: Optional[List[ApplicationCommandPayload]] = None
    ) -> None:
        await self._state.register_new_application_commands(data=data, guild_id=self.id)

    async def register_application_commands(self, *commands: BaseApplicationCommand) -> None:
        for command in commands:
            await self._state.register_application_command(command, guild_id=self.id)

    async def delete_application_commands(self, *commands: BaseApplicationCommand) -> None:
        for command in commands:
            await self._state.delete_application_command(command, guild_id=self.id)

    async def auto_moderation_rules(self) -> List[AutoModerationRule]:
        """|coro|

        Get the list of auto moderation rules from this guild.

        Requires the :attr:`~Permissions.manage_guild` permission.

        .. versionadded:: 2.1

        Raises
        ------
        Forbidden
            You do not have permission to fetch the auto moderation rules.

        Returns
        -------
        List[:class:`AutoModerationRule`]
            The auto moderation rules of this guild.
        """

        data = await self._state.http.list_guild_auto_moderation_rules(self.id)
        return [AutoModerationRule(data=d, state=self._state) for d in data]

    async def fetch_auto_moderation_rule(self, rule_id: int, /) -> AutoModerationRule:
        """|coro|

        Retrieves a :class:`AutoModerationRule` from this guild by its ID

        Requires the :attr:`~Permissions.manage_guild` permission.

        .. versionadded:: 2.1

        Parameters
        ----------
        rule_id: :class:`int`
            The ID of the auto moderation rule to fetch.

        Raises
        ------
        NotFound
            The requested rule could not be found.
        Forbidden
            You do not have permission to fetch auto moderation rules.
        HTTPException
            Fetching the rule failed.

        Returns
        -------
        :class:`AutoModerationRule`
            The found auto moderation rule.
        """

        data = await self._state.http.get_auto_moderation_rule(self.id, rule_id)
        return AutoModerationRule(data=data, state=self._state)

    async def create_auto_moderation_rule(
        self,
        *,
        name: str,
        event_type: AutoModerationEventType,
        trigger_type: AutoModerationTriggerType,
        actions: List[AutoModerationAction],
        trigger_metadata: Optional[AutoModerationTriggerMetadata] = None,
        enabled: Optional[bool] = None,
        exempt_roles: Optional[List[Snowflake]] = None,
        exempt_channels: Optional[List[Snowflake]] = None,
        reason: Optional[str] = None,
    ) -> AutoModerationRule:
        """|coro|

        Create a new auto moderation rule.

        Requires the :attr:`~Permissions.manage_guild` permission.

        .. versionadded:: 2.1

        Parameters
        ----------
        name: :class:`str`
            The name to use for this rule.
        event_type: :class:`AutoModerationEventType`
            The type of event conteto listen to for this rule.
        actions: List[:class:`AutoModerationAction`]
            The actions to execute when this rule is triggered.
        trigger_type: :class:`AutoModerationTriggerType`
            The type of content that triggers this rule.
        trigger_metadata: Optional[:class:`AutoModerationTriggerMetadata`]
            The additional data to use to determine if this rule has been triggered.
        enabled: Optional[:class:`bool`]
            If this rule should be enabled.
        exempt_roles: Optional[List[:class:`abc.Snowflake`]]
            Roles that should be exempt from this rule.
        exempt_channels: Optional[List[:class:`abc.Snowflake`]]
            Channels that should be exempt from this rule.
        reason: Optional[:class:`str`]
            The reason for creating this rule. Shows in the audit log.

        Raises
        ------
        Forbidden
            You do not have permission to create auto moderation rules.
        HTTPException
            Creating the rule failed.
        InvalidArgument
            An invalid type was passed for an argument.

        Returns
        -------
        :class:`AutoModerationRule`
            The newly created auto moderation rule.
        """

        if not isinstance(event_type, AutoModerationEventType):
            raise InvalidArgument("event_type must be of type AutoModerationEventType")

        if not isinstance(trigger_type, AutoModerationTriggerType):
            raise InvalidArgument("trigger_type must be of type AutoModerationTriggerType")

        payload: AutoModerationRuleCreate = {
            "name": str(name),
            "event_type": event_type.value,
            "trigger_type": trigger_type.value,
            "actions": [action.payload for action in actions],
        }

        if trigger_metadata is not None:
            if not isinstance(trigger_metadata, AutoModerationTriggerMetadata):
                raise InvalidArgument(
                    "trigger_metadata must be of type AutoModerationTriggerMetadata"
                )

            payload["trigger_metadata"] = trigger_metadata.payload

        if enabled is not None:
            payload["enabled"] = enabled

        if exempt_roles is not None:
            payload["exempt_roles"] = [str(role.id) for role in exempt_roles]

        if exempt_channels is not None:
            payload["exempt_channels"] = [str(channel.id) for channel in exempt_channels]

        data = await self._state.http.create_auto_moderation_rule(
            self.id, data=payload, reason=reason
        )
        return AutoModerationRule(data=data, state=self._state)

    async def create_test_entitlement(self, sku_id: int) -> None:
        """|coro|

        Creates a test entitlement for the guild.
        This makes Discord behave as if the guild has purchased the SKU.

        .. versionadded:: 3.0

        Parameters
        ----------
        sku_id: :class:`int`
            The ID of the SKU to create a test entitlement for.

        Raises
        ------
        :exc:`.HTTPException`
            Creating the test entitlement failed.
        :exc:`TypeError`
            The client's application ID is not available.
        """
        if not self._state.application_id:
            raise TypeError("Couldn't get the clients application_id.")
        await self._state.http.create_test_entitlement(
            application_id=self._state.application_id,
            sku_id=sku_id,
            owner_id=self.id,
            owner_type=EntitlementOwnerType.guild_subscription.value,
        )

    async def entitlements(
        self,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        limit: Optional[int] = None,
        exclude_ended: bool = False,
    ) -> List[Entitlement]:
        """|coro|

        Fetches the entitlements for the guild.

        .. versionadded:: 3.0

        Parameters
        ----------
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve entitlements before this date or entitlement.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
            Defaults to ``None``.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve entitlements after this date or entitlement.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
            Defaults to ``None``.
        limit: Optional[:class:`int`]
            The number of entitlements to retrieve. If ``None`` retrieve all entitlements.
            Defaults to ``None``.
        exclude_ended: :class:`bool`
            Whether to exclude ended entitlements.
            Defaults to ``False``.

        Raises
        ------
        :exc:`.HTTPException`
            Fetching the entitlements failed.
        :exc:`TypeError`
            The client's application ID is not available.

        Returns
        -------
        List[:class:`Entitlement`]
            The guild's entitlements.
        """
        if not self._state.application_id:
            raise TypeError("Couldn't get the clients application_id.")

        if isinstance(before, datetime.datetime):
            before = Object(id=utils.time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=utils.time_snowflake(after, high=True))

        data = await self._state.http.list_entitlements(
            application_id=self._state.application_id,
            before=before.id if before else None,
            after=after.id if after else None,
            limit=limit,
            guild_id=self.id,
            exclude_ended=exclude_ended,
        )
        return [Entitlement(payload=d) for d in data]

    def parse_mentions(self, text: str) -> List[Union[Member, User]]:
        """Parses user mentions in a string and returns a list of :class:`Member` objects.
        If the member is not in the guild, a :class:`User` object is returned for that member instead.

        .. note::

            This does not include role or channel mentions. See :meth:`~Guild.parse_role_mentions`
            for :class:`Role` objects and :meth:`~Guild.parse_channel_mentions` for
            :class:`~abc.GuildChannel` objects.

        .. note::

            Only members or users found in the cache will be returned. To get the IDs of all users
            mentioned, use :func:`~utils.parse_raw_mentions` instead.

        .. versionadded:: 2.2

        Parameters
        ----------
        text: :class:`str`
            String to parse mentions in.

        Returns
        -------
        List[Union[:class:`Member`, :class:`User`]]
            List of :class:`Member` or :class:`User` objects that were mentioned in the string.
        """
        get_member_or_user: Callable[
            [int], Optional[Union[Member, User]]
        ] = lambda id: self.get_member(id) or self._state.get_user(id)
        it = filter(None, map(get_member_or_user, utils.parse_raw_mentions(text)))
        return utils.unique(it)

    def parse_role_mentions(self, text: str) -> List[Role]:
        """Parses role mentions in a string and returns a list of :class:`Role` objects.

        .. note::

            Only cached roles found in the :class:`Guild` will be returned. To get the IDs
            of all roles mentioned, use :func:`~utils.parse_raw_role_mentions` instead.

        .. versionadded:: 2.2

        Parameters
        ----------
        text: :class:`str`
            String to parse mentions in.

        Returns
        -------
        List[:class:`Role`]
            List of :class:`Role` objects that were mentioned in the string.
        """
        it = filter(None, map(self.get_role, utils.parse_raw_role_mentions(text)))
        return utils.unique(it)

    def parse_channel_mentions(self, text: str) -> List[abc.GuildChannel]:
        """Parses channel mentions in a string and returns a list of :class:`~abc.GuildChannel` objects.

        .. note::

            Only cached channels found in the :class:`Guild` will be returned. To get the IDs of all
            channels mentioned, use :func:`~utils.parse_raw_channel_mentions` instead.

        .. versionadded:: 2.2

        Parameters
        ----------
        text: :class:`str`
            String to parse mentions in.

        Returns
        -------
        List[:class:`~abc.GuildChannel`]
            List of :class:`~abc.GuildChannel` objects that were mentioned in the string.
        """
        it = filter(None, map(self.get_channel, utils.parse_raw_channel_mentions(text)))
        return utils.unique(it)
