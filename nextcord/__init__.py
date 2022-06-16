"""
Discord API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Discord API.

:copyright: (c) 2015-present Rapptz
:copyright: (c) 2021-present tag-epic
:license: MIT, see LICENSE for more details.

"""

__title__ = "nextcord"
__author__ = "tag-epic & Rapptz"
__license__ = "MIT"
__copyright__ = "Copyright 2015-present Rapptz & tag-epic"
__version__ = "2.0.0b4"

__path__ = __import__("pkgutil").extend_path(__path__, __name__)

import logging
from typing import Literal, NamedTuple

from . import abc, opus, ui, utils
from .activity import Activity, BaseActivity, CustomActivity, Game, Spotify, Streaming
from .appinfo import AppInfo, PartialAppInfo
from .application_command import (
    ApplicationCommand,
    ApplicationSubcommand,
    ClientCog,
    CommandOption,
    SlashOption,
    message_command,
    slash_command,
    user_command,
)
from .asset import Asset
from .audit_logs import AuditLogChanges, AuditLogDiff, AuditLogEntry
from .bans import BanEntry
from .channel import (
    CategoryChannel,
    DMChannel,
    GroupChannel,
    PartialMessageable,
    StageChannel,
    TextChannel,
    VoiceChannel,
)
from .client import Client
from .colour import Color, Colour
from .components import ActionRow, Button, Component, SelectMenu, SelectOption, TextInput
from .embeds import Embed
from .emoji import Emoji
from .enums import (
    ActivityType,
    ApplicationCommandOptionType,
    ApplicationCommandType,
    AuditLogAction,
    AuditLogActionCategory,
    ButtonStyle,
    ChannelType,
    ComponentType,
    ContentFilter,
    DefaultAvatar,
    Enum,
    ExpireBehavior,
    ExpireBehaviour,
    InteractionResponseType,
    InteractionType,
    InviteTarget,
    MessageType,
    NotificationLevel,
    NSFWLevel,
    ScheduledEventEntityType,
    ScheduledEventPrivacyLevel,
    ScheduledEventStatus,
    SpeakingState,
    StagePrivacyLevel,
    Status,
    StickerFormatType,
    StickerType,
    TeamMembershipState,
    TextInputStyle,
    UserFlags,
    VerificationLevel,
    VideoQualityMode,
    VoiceRegion,
    WebhookType,
)
from .errors import (
    ApplicationCheckFailure,
    ApplicationError,
    ApplicationInvokeError,
    ClientException,
    ConnectionClosed,
    DiscordException,
    DiscordServerError,
    Forbidden,
    GatewayNotFound,
    HTTPException,
    InteractionResponded,
    InvalidArgument,
    InvalidCommandType,
    InvalidData,
    LoginFailure,
    NoMoreItems,
    NotFound,
    PrivilegedIntentsRequired,
)
from .file import File
from .flags import (
    ApplicationFlags,
    Intents,
    MemberCacheFlags,
    MessageFlags,
    PublicUserFlags,
    SystemChannelFlags,
)
from .guild import Guild
from .health_check import incompatible_libraries
from .integrations import (
    BotIntegration,
    Integration,
    IntegrationAccount,
    IntegrationApplication,
    StreamIntegration,
)
from .interactions import (
    Interaction,
    InteractionMessage,
    InteractionResponse,
    PartialInteractionMessage,
)
from .invite import Invite, PartialInviteChannel, PartialInviteGuild
from .member import Member, VoiceState
from .mentions import AllowedMentions
from .message import Attachment, DeletedReferencedMessage, Message, MessageReference, PartialMessage
from .object import Object
from .partial_emoji import PartialEmoji
from .permissions import PermissionOverwrite, Permissions
from .player import (
    AudioSource,
    FFmpegAudio,
    FFmpegOpusAudio,
    FFmpegPCMAudio,
    PCMAudio,
    PCMVolumeTransformer,
)
from .raw_models import (
    RawBulkMessageDeleteEvent,
    RawIntegrationDeleteEvent,
    RawMemberRemoveEvent,
    RawMessageDeleteEvent,
    RawMessageUpdateEvent,
    RawReactionActionEvent,
    RawReactionClearEmojiEvent,
    RawReactionClearEvent,
    RawTypingEvent,
)
from .reaction import Reaction
from .role import Role, RoleTags
from .scheduled_events import EntityMetadata, ScheduledEvent, ScheduledEventUser
from .shard import AutoShardedClient, ShardInfo
from .stage_instance import StageInstance
from .sticker import GuildSticker, StandardSticker, Sticker, StickerItem, StickerPack
from .team import Team, TeamMember
from .template import Template
from .threads import Thread, ThreadMember
from .user import ClientUser, User
from .voice_client import VoiceClient, VoiceProtocol
from .webhook import (
    PartialWebhookChannel,
    PartialWebhookGuild,
    SyncWebhook,
    SyncWebhookMessage,
    Webhook,
    WebhookMessage,
)
from .widget import Widget, WidgetChannel, WidgetMember


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]
    serial: int


version_info: VersionInfo = VersionInfo(major=2, minor=0, micro=0, releaselevel="beta", serial=4)

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = (
    "__title__",
    "__author__",
    "__license__",
    "__copyright__",
    "__version__",
    "__path__",
    "VersionInfo",
    "version_info",
    "Client",
    "AppInfo",
    "PartialAppInfo",
    "BanEntry",
    "User",
    "ClientUser",
    "Emoji",
    "PartialEmoji",
    "BaseActivity",
    "Activity",
    "Streaming",
    "Game",
    "Spotify",
    "CustomActivity",
    "TextChannel",
    "VoiceChannel",
    "StageChannel",
    "DMChannel",
    "CategoryChannel",
    "GroupChannel",
    "PartialMessageable",
    "Guild",
    "SystemChannelFlags",
    "MessageFlags",
    "PublicUserFlags",
    "Intents",
    "MemberCacheFlags",
    "ApplicationFlags",
    "VoiceState",
    "Member",
    "Attachment",
    "Message",
    "PartialMessage",
    "MessageReference",
    "DeletedReferencedMessage",
    "Asset",
    "DiscordException",
    "InvalidCommandType",
    "ClientException",
    "NoMoreItems",
    "GatewayNotFound",
    "HTTPException",
    "Forbidden",
    "NotFound",
    "DiscordServerError",
    "InvalidData",
    "InvalidArgument",
    "LoginFailure",
    "ConnectionClosed",
    "PrivilegedIntentsRequired",
    "InteractionResponded",
    "ApplicationError",
    "ApplicationInvokeError",
    "ApplicationCheckFailure",
    "Permissions",
    "PermissionOverwrite",
    "RoleTags",
    "Role",
    "File",
    "Colour",
    "Color",
    "IntegrationAccount",
    "IntegrationApplication",
    "Integration",
    "StreamIntegration",
    "BotIntegration",
    "PartialInviteChannel",
    "PartialInviteGuild",
    "Invite",
    "Template",
    "WidgetChannel",
    "WidgetMember",
    "Widget",
    "Object",
    "Reaction",
    "utils",
    "opus",
    "abc",
    "ui",
    "Enum",
    "ChannelType",
    "MessageType",
    "VoiceRegion",
    "SpeakingState",
    "VerificationLevel",
    "ContentFilter",
    "Status",
    "DefaultAvatar",
    "AuditLogAction",
    "AuditLogActionCategory",
    "UserFlags",
    "ActivityType",
    "NotificationLevel",
    "TeamMembershipState",
    "WebhookType",
    "ExpireBehaviour",
    "ExpireBehavior",
    "StickerType",
    "StickerFormatType",
    "InviteTarget",
    "VideoQualityMode",
    "ComponentType",
    "ButtonStyle",
    "TextInputStyle",
    "StagePrivacyLevel",
    "InteractionType",
    "InteractionResponseType",
    "ApplicationCommandType",
    "ApplicationCommandOptionType",
    "NSFWLevel",
    "ScheduledEventEntityType",
    "ScheduledEventPrivacyLevel",
    "ScheduledEventStatus",
    "Embed",
    "AllowedMentions",
    "AutoShardedClient",
    "ShardInfo",
    "AudioSource",
    "PCMAudio",
    "FFmpegAudio",
    "FFmpegPCMAudio",
    "FFmpegOpusAudio",
    "PCMVolumeTransformer",
    "Webhook",
    "WebhookMessage",
    "PartialWebhookChannel",
    "PartialWebhookGuild",
    "SyncWebhook",
    "SyncWebhookMessage",
    "VoiceProtocol",
    "VoiceClient",
    "AuditLogDiff",
    "AuditLogChanges",
    "AuditLogEntry",
    "RawMessageDeleteEvent",
    "RawBulkMessageDeleteEvent",
    "RawMessageUpdateEvent",
    "RawReactionActionEvent",
    "RawReactionClearEvent",
    "RawReactionClearEmojiEvent",
    "RawIntegrationDeleteEvent",
    "RawTypingEvent",
    "RawMemberRemoveEvent",
    "Team",
    "TeamMember",
    "StickerPack",
    "StickerItem",
    "Sticker",
    "StandardSticker",
    "GuildSticker",
    "StageInstance",
    "Interaction",
    "InteractionMessage",
    "InteractionResponse",
    "PartialInteractionMessage",
    "Component",
    "ActionRow",
    "Button",
    "SelectMenu",
    "SelectOption",
    "TextInput",
    "Thread",
    "ThreadMember",
    "incompatible_libraries",
    "EntityMetadata",
    "ScheduledEventUser",
    "ScheduledEvent",
    "ApplicationCommand",
    "ApplicationSubcommand",
    "ClientCog",
    "CommandOption",
    "message_command",
    "SlashOption",
    "slash_command",
    "user_command",
)
