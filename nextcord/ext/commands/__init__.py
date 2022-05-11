"""
nextcord.ext.commands
~~~~~~~~~~~~~~~~~~~~~

An extension module to facilitate creation of bot commands.

:copyright: (c) 2015-present Rapptz
:copyright: (c) 2021-present tag-epic
:license: MIT, see LICENSE for more details.
"""


from .bot import AutoShardedBot, Bot, when_mentioned, when_mentioned_or
from .cog import Cog, CogMeta
from .context import Context
from .converter import (CategoryChannelConverter, ColorConverter,
                        ColourConverter, Converter, EmojiConverter,
                        GameConverter, Greedy, GuildChannelConverter,
                        GuildConverter, GuildStickerConverter, IDConverter,
                        InviteConverter, MemberConverter, MessageConverter,
                        ObjectConverter, PartialEmojiConverter,
                        PartialMessageConverter, RoleConverter,
                        ScheduledEventConverter, StageChannelConverter,
                        TextChannelConverter, ThreadConverter, UserConverter,
                        VoiceChannelConverter, clean_content, run_converters)
from .cooldowns import (BucketType, Cooldown, CooldownMapping,
                        DynamicCooldownMapping, MaxConcurrency)
from .core import (Command, Group, GroupMixin, after_invoke, before_invoke,
                   bot_has_any_role, bot_has_guild_permissions,
                   bot_has_permissions, bot_has_role, check, check_any,
                   command, cooldown, dm_only, dynamic_cooldown, group,
                   guild_only, has_any_role, has_guild_permissions,
                   has_permissions, has_role, is_nsfw, is_owner,
                   max_concurrency)
from .errors import (ArgumentParsingError, BadArgument, BadBoolArgument,
                     BadColorArgument, BadColourArgument, BadFlagArgument,
                     BadInviteArgument, BadLiteralArgument, BadUnionArgument,
                     BotMissingAnyRole, BotMissingPermissions, BotMissingRole,
                     ChannelNotFound, ChannelNotReadable, CheckAnyFailure,
                     CheckFailure, CommandError, CommandInvokeError,
                     CommandNotFound, CommandOnCooldown,
                     CommandRegistrationError, ConversionError,
                     DisabledCommand, EmojiNotFound, ExpectedClosingQuoteError,
                     ExtensionAlreadyLoaded, ExtensionError, ExtensionFailed,
                     ExtensionNotFound, ExtensionNotLoaded, FlagError,
                     GuildNotFound, GuildStickerNotFound,
                     InvalidEndOfQuotedStringError, InvalidSetupArguments,
                     MaxConcurrencyReached, MemberNotFound, MessageNotFound,
                     MissingAnyRole, MissingFlagArgument, MissingPermissions,
                     MissingRequiredArgument, MissingRequiredFlag, MissingRole,
                     NoEntryPointError, NoPrivateMessage, NotOwner,
                     NSFWChannelRequired, ObjectNotFound,
                     PartialEmojiConversionFailure, PrivateMessageOnly,
                     RoleNotFound, ScheduledEventNotFound, ThreadNotFound,
                     TooManyArguments, TooManyFlags, UnexpectedQuoteError,
                     UserInputError, UserNotFound)
from .flags import Flag, FlagConverter, flag
from .help import (DefaultHelpCommand, HelpCommand, MinimalHelpCommand,
                   Paginator)
