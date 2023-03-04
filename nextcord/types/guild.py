# SPDX-License-Identifier: MIT

from typing import List, Literal, Optional, TypedDict

from typing_extensions import NotRequired

from .activity import PartialPresenceUpdate
from .channel import GuildChannel
from .emoji import Emoji
from .member import Member
from .role import Role
from .scheduled_events import ScheduledEvent
from .snowflake import Snowflake
from .sticker import GuildSticker
from .threads import Thread
from .user import User
from .voice import GuildVoiceState
from .welcome_screen import WelcomeScreen


class Ban(TypedDict):
    reason: Optional[str]
    user: User


class UnavailableGuild(TypedDict):
    id: Snowflake
    unavailable: NotRequired[bool]


DefaultMessageNotificationLevel = Literal[0, 1]
ExplicitContentFilterLevel = Literal[0, 1, 2]
MFALevel = Literal[0, 1]
VerificationLevel = Literal[0, 1, 2, 3, 4]
NSFWLevel = Literal[0, 1, 2, 3]
PremiumTier = Literal[0, 1, 2, 3]
GuildFeature = Literal[
    "AUTO_MODERATION",
    "ANIMATED_BANNER",
    "ANIMATED_ICON",
    "APPLICATION_COMMAND_PERMISSIONS_V2",
    "BANNER",
    "COMMUNITY",
    "DEVELOPER_SUPPORT_SERVER",
    "DISCOVERABLE",
    "FEATURABLE",
    "INVITES_DISABLED",
    "INVITE_SPLASH",
    "MEMBER_VERIFICATION_GATE_ENABLED",
    "MONETIZATION_ENABLED",
    "MORE_STICKERS",
    "NEWS",
    "PARTNERED",
    "PREVIEW_ENABLED",
    "ROLE_ICONS",
    "TICKETED_EVENTS_ENABLED",
    "VANITY_URL",
    "VERIFIED",
    "VIP_REGIONS",
    "WELCOME_SCREEN_ENABLED",
]


class _BaseGuildPreview(UnavailableGuild):
    name: str
    icon: Optional[str]
    splash: Optional[str]
    discovery_splash: Optional[str]
    emojis: List[Emoji]
    features: List[GuildFeature]
    description: Optional[str]


class _GuildPreviewUnique(TypedDict):
    approximate_member_count: int
    approximate_presence_count: int


class GuildPreview(_BaseGuildPreview, _GuildPreviewUnique):
    ...


class Guild(_BaseGuildPreview):
    owner_id: Snowflake
    region: str
    afk_channel_id: Optional[Snowflake]
    afk_timeout: int
    verification_level: VerificationLevel
    default_message_notifications: DefaultMessageNotificationLevel
    explicit_content_filter: ExplicitContentFilterLevel
    roles: List[Role]
    mfa_level: MFALevel
    nsfw_level: NSFWLevel
    application_id: Optional[Snowflake]
    system_channel_id: Optional[Snowflake]
    system_channel_flags: int
    rules_channel_id: Optional[Snowflake]
    vanity_url_code: Optional[str]
    banner: Optional[str]
    premium_tier: PremiumTier
    preferred_locale: str
    public_updates_channel_id: Optional[Snowflake]
    guild_scheduled_events: Optional[List[ScheduledEvent]]
    icon_hash: NotRequired[Optional[str]]
    owner: NotRequired[bool]
    permissions: NotRequired[str]
    widget_enabled: NotRequired[bool]
    widget_channel_id: NotRequired[Optional[Snowflake]]
    joined_at: NotRequired[Optional[str]]
    large: NotRequired[bool]
    member_count: NotRequired[int]
    voice_states: NotRequired[List[GuildVoiceState]]
    members: NotRequired[List[Member]]
    channels: NotRequired[List[GuildChannel]]
    presences: NotRequired[List[PartialPresenceUpdate]]
    threads: NotRequired[List[Thread]]
    max_presences: NotRequired[Optional[int]]
    max_members: NotRequired[int]
    premium_subscription_count: NotRequired[int]
    max_video_channel_users: NotRequired[int]
    stickers: NotRequired[List[GuildSticker]]


class InviteGuild(Guild, total=False):
    welcome_screen: WelcomeScreen


class GuildWithCounts(Guild, _GuildPreviewUnique):
    ...


class GuildPrune(TypedDict):
    pruned: Optional[int]


class ChannelPositionUpdate(TypedDict):
    id: Snowflake
    position: Optional[int]
    lock_permissions: Optional[bool]
    parent_id: Optional[Snowflake]


class RolePositionUpdate(TypedDict):
    id: Snowflake
    position: NotRequired[Optional[Snowflake]]
