"""
The MIT License (MIT)
Copyright (c) 2021-present tag-epic
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

Module to allow for backwards compatibility for existing code and extensions
"""

from nextcord import (
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

__title__ = 'nextcord'
__author__ = 'tag-epic & Rapptz'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015-present Rapptz & tag-epic'
__version__ = '2.0.0a10'

__path__ = __import__('pkgutil').extend_path(__path__, __name__)
