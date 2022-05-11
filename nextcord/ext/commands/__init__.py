"""
nextcord.ext.commands
~~~~~~~~~~~~~~~~~~~~~

An extension module to facilitate creation of bot commands.

:copyright: (c) 2015-present Rapptz
:copyright: (c) 2021-present tag-epic
:license: MIT, see LICENSE for more details.
"""


from .bot import (
    when_mentioned,
    when_mentioned_or,
    Bot,
    AutoShardedBot,
)
from .context import Context
from .core import (
    Command,
    Group,
    GroupMixin,
    command,
    group,
    has_role,
    has_permissions,
    has_any_role,
    check,
    check_any,
    before_invoke,
    after_invoke,
    bot_has_role,
    bot_has_permissions,
    bot_has_any_role,
    cooldown,
    dynamic_cooldown,
    max_concurrency,
    dm_only,
    guild_only,
    is_owner,
    is_nsfw,
    has_guild_permissions,
    bot_has_guild_permissions,
)
from .errors import (
    CommandError,
    MissingRequiredArgument,
    BadArgument,
    PrivateMessageOnly,
    NoPrivateMessage,
    CheckFailure,
    CheckAnyFailure,
    CommandNotFound,
    DisabledCommand,
    CommandInvokeError,
    TooManyArguments,
    UserInputError,
    CommandOnCooldown,
    MaxConcurrencyReached,
    NotOwner,
    MessageNotFound,
    ObjectNotFound,
    MemberNotFound,
    GuildNotFound,
    UserNotFound,
    ChannelNotFound,
    ThreadNotFound,
    ChannelNotReadable,
    BadColourArgument,
    BadColorArgument,
    RoleNotFound,
    BadInviteArgument,
    EmojiNotFound,
    GuildStickerNotFound,
    PartialEmojiConversionFailure,
    BadBoolArgument,
    MissingRole,
    BotMissingRole,
    MissingAnyRole,
    BotMissingAnyRole,
    MissingPermissions,
    BotMissingPermissions,
    NSFWChannelRequired,
    ConversionError,
    BadUnionArgument,
    BadLiteralArgument,
    ArgumentParsingError,
    UnexpectedQuoteError,
    InvalidEndOfQuotedStringError,
    ExpectedClosingQuoteError,
    ExtensionError,
    ExtensionAlreadyLoaded,
    ExtensionNotLoaded,
    NoEntryPointError,
    InvalidSetupArguments,
    ExtensionFailed,
    ExtensionNotFound,
    CommandRegistrationError,
    FlagError,
    BadFlagArgument,
    MissingFlagArgument,
    TooManyFlags,
    MissingRequiredFlag,
    ScheduledEventNotFound
)
from .help import (
    Paginator,
    HelpCommand,
    DefaultHelpCommand,
    MinimalHelpCommand,
)
from .converter import (
    Converter,
    ObjectConverter,
    MemberConverter,
    UserConverter,
    MessageConverter,
    PartialMessageConverter,
    TextChannelConverter,
    InviteConverter,
    GuildConverter,
    RoleConverter,
    GameConverter,
    ColourConverter,
    ColorConverter,
    VoiceChannelConverter,
    StageChannelConverter,
    EmojiConverter,
    PartialEmojiConverter,
    CategoryChannelConverter,
    IDConverter,
    ThreadConverter,
    GuildChannelConverter,
    GuildStickerConverter,
    ScheduledEventConverter,
    clean_content,
    Greedy,
    run_converters,
)
from .cooldowns import (
    BucketType,
    Cooldown,
    CooldownMapping,
    DynamicCooldownMapping,
    MaxConcurrency,
)
from .cog import (
    CogMeta,
    Cog,
)
from .flags import (
    Flag,
    flag,
    FlagConverter,
)
