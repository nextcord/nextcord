"""
Discord API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Discord API.

:copyright: (c) 2015-present Rapptz
:copyright: (c) 2021-present tag-epic
:license: MIT, see LICENSE for more details.

"""

__title__ = 'nextcord'
__author__ = 'tag-epic & Rapptz'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015-present Rapptz & tag-epic'
__version__ = '2.0.0a10'

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

import logging
from typing import NamedTuple, Literal

from .client import Client
from .appinfo import (
    AppInfo,
    PartialAppInfo,
)
from .bans import BanEntry
from .user import (
    User,
    ClientUser,
)
from .emoji import Emoji
from .partial_emoji import PartialEmoji
from .activity import (
    BaseActivity,
    Activity,
    Streaming,
    Game,
    Spotify,
    CustomActivity,
)
from .channel import (
    TextChannel,
    VoiceChannel,
    StageChannel,
    DMChannel,
    CategoryChannel,
    GroupChannel,
    PartialMessageable,
)
from .guild import Guild
from .flags import (
    SystemChannelFlags,
    MessageFlags,
    PublicUserFlags,
    Intents,
    MemberCacheFlags,
    ApplicationFlags,
)
from .member import (
    VoiceState,
    Member,
)
from .message import (
    Attachment,
    Message,
    PartialMessage,
    MessageReference,
    DeletedReferencedMessage,
)
from .asset import Asset
from .errors import (
    DiscordException,
    InvalidCommandType,
    ClientException,
    NoMoreItems,
    GatewayNotFound,
    HTTPException,
    Forbidden,
    NotFound,
    DiscordServerError,
    InvalidData,
    InvalidArgument,
    LoginFailure,
    ConnectionClosed,
    PrivilegedIntentsRequired,
    InteractionResponded,
    ApplicationError,
    ApplicationInvokeError,
    ApplicationCheckFailure,
)
from .permissions import (
    Permissions,
    PermissionOverwrite,
)
from .role import (
    RoleTags,
    Role,
)
from .file import File
from .colour import (
    Colour,
    Color,
)
from .integrations import (
    IntegrationAccount,
    IntegrationApplication,
    Integration,
    StreamIntegration,
    BotIntegration,
)
from .invite import (
    PartialInviteChannel,
    PartialInviteGuild,
    Invite,
)
from .template import Template
from .widget import (
    WidgetChannel,
    WidgetMember,
    Widget,
)
from .object import Object
from .reaction import Reaction
from . import utils, opus, abc, ui
from .enums import (
    Enum,
    ChannelType,
    MessageType,
    VoiceRegion,
    SpeakingState,
    VerificationLevel,
    ContentFilter,
    Status,
    DefaultAvatar,
    AuditLogAction,
    AuditLogActionCategory,
    UserFlags,
    ActivityType,
    NotificationLevel,
    TeamMembershipState,
    WebhookType,
    ExpireBehaviour,
    ExpireBehavior,
    StickerType,
    StickerFormatType,
    InviteTarget,
    VideoQualityMode,
    ComponentType,
    ButtonStyle,
    TextInputStyle,
    StagePrivacyLevel,
    InteractionType,
    InteractionResponseType,
    ApplicationCommandType,
    ApplicationCommandOptionType,
    NSFWLevel,
    ScheduledEventEntityType,
    ScheduledEventPrivacyLevel,
    ScheduledEventStatus,
)
from .embeds import Embed
from .mentions import AllowedMentions
from .shard import (
    AutoShardedClient,
    ShardInfo,
)
from .player import (
    AudioSource,
    PCMAudio,
    FFmpegAudio,
    FFmpegPCMAudio,
    FFmpegOpusAudio,
    PCMVolumeTransformer,
)
from .webhook import (
    Webhook, WebhookMessage, PartialWebhookChannel, PartialWebhookGuild,
    SyncWebhook, SyncWebhookMessage
)
from .voice_client import (
    VoiceProtocol,
    VoiceClient,
)
from .audit_logs import (
    AuditLogDiff,
    AuditLogChanges,
    AuditLogEntry,
)
from .raw_models import (
    RawMessageDeleteEvent,
    RawBulkMessageDeleteEvent,
    RawMessageUpdateEvent,
    RawReactionActionEvent,
    RawReactionClearEvent,
    RawReactionClearEmojiEvent,
    RawIntegrationDeleteEvent,
    RawTypingEvent,
    RawMemberRemoveEvent,
)
from .team import (
    Team,
    TeamMember,
)
from .sticker import (
    StickerPack,
    StickerItem,
    Sticker,
    StandardSticker,
    GuildSticker,
)
from .stage_instance import StageInstance
from .interactions import (
    Interaction,
    InteractionMessage,
    InteractionResponse,
    PartialInteractionMessage,
)
from .components import (
    Component,
    ActionRow,
    Button,
    SelectMenu,
    SelectOption,
    TextInput,
)
from .threads import (
    Thread,
    ThreadMember,
)
from .health_check import incompatible_libraries
from .scheduled_events import (
    EntityMetadata,
    ScheduledEventUser,
    ScheduledEvent
)
from .application_command import (
    ApplicationCommand,
    ApplicationSubcommand,
    ClientCog,
    CommandOption,
    message_command,
    SlashOption,
    slash_command,
    user_command,
)


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]
    serial: int


version_info: VersionInfo = VersionInfo(major=2, minor=0, micro=0, releaselevel='alpha', serial=0)

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = (
    __title__,
    __author__,
    __license__,
    __copyright__,
    __version__,
    __path__,
    VersionInfo,
    version_info,
    Client,
    AppInfo,
    PartialAppInfo,
    BanEntry,
    User,
    ClientUser,
    Emoji,
    PartialEmoji,
    BaseActivity,
    Activity,
    Streaming,
    Game,
    Spotify,
    CustomActivity,
    TextChannel,
    VoiceChannel,
    StageChannel,
    DMChannel,
    CategoryChannel,
    GroupChannel,
    PartialMessageable,
    Guild,
    SystemChannelFlags,
    MessageFlags,
    PublicUserFlags,
    Intents,
    MemberCacheFlags,
    ApplicationFlags,
    VoiceState,
    Member,
    Attachment,
    Message,
    PartialMessage,
    MessageReference,
    DeletedReferencedMessage,
    Asset,
    DiscordException,
    InvalidCommandType,
    ClientException,
    NoMoreItems,
    GatewayNotFound,
    HTTPException,
    Forbidden,
    NotFound,
    DiscordServerError,
    InvalidData,
    InvalidArgument,
    LoginFailure,
    ConnectionClosed,
    PrivilegedIntentsRequired,
    InteractionResponded,
    ApplicationError,
    ApplicationInvokeError,
    ApplicationCheckFailure,
    Permissions,
    PermissionOverwrite,
    RoleTags,
    Role,
    File,
    Colour,
    Color,
    IntegrationAccount,
    IntegrationApplication,
    Integration,
    StreamIntegration,
    BotIntegration,
    PartialInviteChannel,
    PartialInviteGuild,
    Invite,
    Template,
    WidgetChannel,
    WidgetMember,
    Widget,
    Object,
    Reaction,
    utils,
    opus,
    abc,
    ui,
    Enum,
    ChannelType,
    MessageType,
    VoiceRegion,
    SpeakingState,
    VerificationLevel,
    ContentFilter,
    Status,
    DefaultAvatar,
    AuditLogAction,
    AuditLogActionCategory,
    UserFlags,
    ActivityType,
    NotificationLevel,
    TeamMembershipState,
    WebhookType,
    ExpireBehaviour,
    ExpireBehavior,
    StickerType,
    StickerFormatType,
    InviteTarget,
    VideoQualityMode,
    ComponentType,
    ButtonStyle,
    TextInputStyle,
    StagePrivacyLevel,
    InteractionType,
    InteractionResponseType,
    ApplicationCommandType,
    ApplicationCommandOptionType,
    NSFWLevel,
    ScheduledEventEntityType,
    ScheduledEventPrivacyLevel,
    ScheduledEventStatus,
    Embed,
    AllowedMentions,
    AutoShardedClient,
    ShardInfo,
    AudioSource,
    PCMAudio,
    FFmpegAudio,
    FFmpegPCMAudio,
    FFmpegOpusAudio,
    PCMVolumeTransformer,
    Webhook,
    WebhookMessage,
    PartialWebhookChannel,
    PartialWebhookGuild,
    SyncWebhook,
    SyncWebhookMessage,
    VoiceProtocol,
    VoiceClient,
    AuditLogDiff,
    AuditLogChanges,
    AuditLogEntry,
    RawMessageDeleteEvent,
    RawBulkMessageDeleteEvent,
    RawMessageUpdateEvent,
    RawReactionActionEvent,
    RawReactionClearEvent,
    RawReactionClearEmojiEvent,
    RawIntegrationDeleteEvent,
    RawTypingEvent,
    RawMemberRemoveEvent,
    Team,
    TeamMember,
    StickerPack,
    StickerItem,
    Sticker,
    StandardSticker,
    GuildSticker,
    StageInstance,
    Interaction,
    InteractionMessage,
    InteractionResponse,
    PartialInteractionMessage,
    Component,
    ActionRow,
    Button,
    SelectMenu,
    SelectOption,
    TextInput,
    Thread,
    ThreadMember,
    incompatible_libraries,
    EntityMetadata,
    ScheduledEventUser,
    ScheduledEvent,
    ApplicationCommand,
    ApplicationSubcommand,
    ClientCog,
    CommandOption,
    message_command,
    SlashOption,
    slash_command,
    user_command,
)
