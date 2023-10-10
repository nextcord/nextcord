# SPDX-License-Identifier: MIT

import enum
from typing import Any, Dict, NamedTuple, Optional, Type, TypeVar

__all__ = (
    "Enum",
    "IntEnum",
    "StrEnum",
    "UnknownEnumValue",
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
    "Locale",
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
    "AutoModerationEventType",
    "AutoModerationTriggerType",
    "KeywordPresetType",
    "AutoModerationActionType",
    "SortOrderType",
    "RoleConnectionMetadataType",
    "ForumLayoutType",
)


class UnknownEnumValue(NamedTuple):
    """Proxy for the underlying name and value of an attribute not known to the Enum."""

    name: str
    value: Any

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return self.value
        return self.name

    def __int__(self) -> int:
        if isinstance(self.value, int):
            return self.value
        raise TypeError(f"{self.name}.{self.value} cannot be converted to an int")

    def __repr__(self) -> str:
        return f"<{self.name}.{self.value!r}>"

    def __le__(self, other):
        try:
            return self.value <= other.value
        except AttributeError:
            return self.value <= other

    def __ge__(self, other):
        try:
            return self.value >= other.value
        except AttributeError:
            return self.value >= other

    def __lt__(self, other):
        try:
            return self.value < other.value
        except AttributeError:
            return self.value < other

    def __gt__(self, other):
        try:
            return self.value > other.value
        except AttributeError:
            return self.value > other

    def __eq__(self, other):
        try:
            return self.value == other.value
        except AttributeError:
            return self.value == other

    def __ne__(self, other):
        try:
            return self.value != other.value
        except AttributeError:
            return self.value != other

    def __hash__(self):
        return hash(self.value)


class Enum(enum.Enum):
    """An enum that supports trying for unknown values."""

    @classmethod
    def try_value(cls, value):
        try:
            return cls(value)
        except ValueError:
            return value


class IntEnum(int, Enum):
    """An enum that supports comparing and hashing as an int."""

    def __int__(self) -> int:
        return self.value


class StrEnum(str, Enum):  # noqa: SLOT000
    """An enum that supports comparing and hashing as a string."""

    def __str__(self) -> str:
        return self.value


class ChannelType(IntEnum):
    """Specifies the type of channel."""

    text = 0
    """A text channel"""
    private = 1
    """A private text channel. Also called a direct message."""
    voice = 2
    """A voice channel"""
    group = 3
    """A private group text channel."""
    category = 4
    """A category channel."""
    news = 5
    """A guild news channel."""
    news_thread = 10
    """A news thread."""
    public_thread = 11
    """A public thread."""
    private_thread = 12
    """A private thread."""
    stage_voice = 13
    """A guild stage voice channel."""
    guild_directory = 14
    """A channel containing the guilds in a
     `Student Hub <https://support.discord.com/hc/en-us/articles/4406046651927-Discord-Student-Hubs-FAQ>`_
    """
    forum = 15
    """A forum channel."""

    def __str__(self) -> str:
        return self.name


class MessageType(IntEnum):
    """Specifies the type of :class:`Message`. This is used to denote if a message
    is to be interpreted as a system message or a regular message.

    .. container:: operations

      .. describe:: x == y

          Checks if two messages are equal.
      .. describe:: x != y

          Checks if two messages are not equal.
    """

    default = 0
    """The default message type. This is the same as regular messages."""
    recipient_add = 1
    """The system message when a user is added to a group private message or a thread."""
    recipient_remove = 2
    """The system message when a user is removed from a group private message or a thread."""
    call = 3
    """The system message denoting call state, e.g. missed call, started call, etc."""
    channel_name_change = 4
    """The system message denoting that a channel's name has been changed."""
    channel_icon_change = 5
    """The system message denoting that a channel's icon has been changed."""
    pins_add = 6
    """The system message denoting that a pinned message has been added to a channel."""
    new_member = 7
    """The system message denoting that a new member has joined a Guild."""
    premium_guild_subscription = 8
    """The system message denoting that a member has "nitro boosted" a guild."""
    premium_guild_tier_1 = 9
    """The system message denoting that a member has "nitro boosted" a guild and it achieved level 1."""
    premium_guild_tier_2 = 10
    """The system message denoting that a member has "nitro boosted" a guild and it achieved level 2."""
    premium_guild_tier_3 = 11
    """The system message denoting that a member has "nitro boosted" a guild and it achieved level 3."""
    channel_follow_add = 12
    """The system message denoting that an announcement channel has been followed.

    .. versionadded:: 1.3
    """
    guild_stream = 13
    """The system message denoting that a member is streaming in the guild.

    .. versionadded:: 1.7
    """
    guild_discovery_disqualified = 14
    """The system message denoting that the guild is no longer eligible for Server Discovery.

    .. versionadded:: 1.7
    """
    guild_discovery_requalified = 15
    """The system message denoting that the guild has become eligible again for Server Discovery.

    .. versionadded:: 1.7
    """
    guild_discovery_grace_period_initial_warning = 16
    """The system message denoting that the guild has failed to meet the Server
        Discovery requirements for one week.

    .. versionadded:: 1.7
    """
    guild_discovery_grace_period_final_warning = 17
    """The system message denoting that the guild has failed to meet the Server
        Discovery requirements for 3 weeks in a row.

    .. versionadded:: 1.7
    """
    thread_created = 18
    """The system message denoting that a thread has been created. This is only
        sent if the thread has been created from an older message. The period of time
        required for a message to be considered old cannot be relied upon and is up to
        Discord.

    .. versionadded:: 2.0
    """
    reply = 19
    """The system message denoting that the author is replying to a message.

    .. versionadded:: 2.0
    """
    chat_input_command = 20
    """The system message denoting that a slash command was executed.

    .. versionadded:: 2.0
    """
    thread_starter_message = 21
    """The system message denoting the message in the thread that is the one that started the
        thread's conversation topic.

    .. versionadded:: 2.0
    """
    guild_invite_reminder = 22
    """The system message sent as a reminder to invite people to the guild.

    .. versionadded:: 2.0
    """
    context_menu_command = 23
    """The system message denoting that a context menu command was executed.

    .. versionadded:: 2.0
    """
    auto_moderation_action = 24
    """The system message denoting that an auto moderation action was executed.

    .. versionadded:: 2.1
    """
    stage_start = 27
    """The system message denoting that a stage channel has started.

    .. versionadded:: 2.6
    """
    stage_end = 28
    """The system message denoting that a stage channel has ended.

    .. versionadded:: 2.6
    """
    stage_speaker = 29
    """The system message denoting that a stage channel has a new speaker.

    .. versionadded:: 2.6
    """
    stage_topic = 31
    """The system message denoting that a stage channel has a new topic.

    .. versionadded:: 2.6
    """


class VoiceRegion(StrEnum):
    """Specifies the region a voice server belongs to."""

    us_west = "us-west"
    """The US West region."""
    us_east = "us-east"
    """The US East region."""
    us_south = "us-south"
    """The US South region."""
    us_central = "us-central"
    """The US Central region."""
    eu_west = "eu-west"
    """The Western Europe region."""
    eu_central = "eu-central"
    """The Central Europe region."""
    singapore = "singapore"
    """The Singapore region."""
    london = "london"
    """The London region."""
    sydney = "sydney"
    """The Sydney region."""
    amsterdam = "amsterdam"
    """The Amsterdam region."""
    frankfurt = "frankfurt"
    """The Frankfurt region."""
    brazil = "brazil"
    """The Brazil region."""
    hongkong = "hongkong"
    """The Hong Kong region."""
    russia = "russia"
    """The Russia region."""
    japan = "japan"
    """The Japan region."""
    southafrica = "southafrica"
    """The South Africa region."""
    south_korea = "south-korea"
    """The South Korea region."""
    india = "india"
    """The India region.

    .. versionadded:: 1.2
    """
    europe = "europe"
    """The Europe region.

    .. versionadded:: 1.3
    """
    dubai = "dubai"
    """The Dubai region.

    .. versionadded:: 1.3
    """
    vip_us_east = "vip-us-east"
    """The US East region for VIP guilds."""
    vip_us_west = "vip-us-west"
    """The US West region for VIP guilds."""
    vip_amsterdam = "vip-amsterdam"
    """The Amsterdam region for VIP guilds."""


class SpeakingState(IntEnum):
    none = 0
    voice = 1 << 0
    soundshare = 1 << 1
    priority = 1 << 2

    def __str__(self) -> str:
        return self.name


class VerificationLevel(IntEnum):
    """Specifies a :class:`Guild`\'s verification level, which is the criteria in
    which a member must meet before being able to send messages to the guild.

    .. container:: operations

        .. versionadded:: 2.0

        .. describe:: x == y

            Checks if two verification levels are equal.
        .. describe:: x != y

            Checks if two verification levels are not equal.
        .. describe:: x > y

            Checks if a verification level is higher than another.
        .. describe:: x < y

            Checks if a verification level is lower than another.
        .. describe:: x >= y

            Checks if a verification level is higher or equal to another.
        .. describe:: x <= y

            Checks if a verification level is lower or equal to another.
    """

    none = 0
    """No citeria set."""
    low = 1
    """Member must have a verified email on their Discord account."""
    medium = 2
    """Member must have a verified email and be registered on Discord for longer than five minutes."""
    high = 3
    """Member must have a verified email, be registered on Discord for longer than five minutes,
    and be a member of the guild for longer than ten minutes.
    """
    highest = 4
    """Member must have a verified phone on their Discord account."""

    def __str__(self) -> str:
        return self.name


class ContentFilter(IntEnum):
    """Specifies a :class:`Guild`\'s explicit content filter, which is the machine
    learning algorithms that Discord uses to detect if an image contains
    pornography or otherwise explicit content.

    .. container:: operations

        .. versionadded:: 2.0

        .. describe:: x == y

            Checks if two content filter levels are equal.
        .. describe:: x != y

            Checks if two content filter levels are not equal.
        .. describe:: x > y

            Checks if a content filter level is higher than another.
        .. describe:: x < y

            Checks if a content filter level is lower than another.
        .. describe:: x >= y

            Checks if a content filter level is higher or equal to another.
        .. describe:: x <= y

            Checks if a content filter level is lower or equal to another.
    """

    disabled = 0
    """The guild does not have the content filter enabled."""
    no_role = 1
    """The guild has the content filter enabled for members without a role."""
    all_members = 2
    """The guild has the content filter enabled for every member."""

    def __str__(self) -> str:
        return self.name


class Status(StrEnum):
    """Specifies a :class:`Member` 's status."""

    online = "online"
    """The member is online."""
    offline = "offline"
    """The member is offline."""
    idle = "idle"
    """The member is idle."""
    dnd = "dnd"
    """The member is "Do Not Disturb."""
    do_not_disturb = "dnd"
    """An alias for :attr:`Status.dnd`."""
    invisible = "invisible"
    """The member is "invisible". In reality, this is only used in sending
    a presence a la :meth:`Client.change_presence`. When you receive a
    user's presence this will be :attr:`offline` instead.
    """


class DefaultAvatar(IntEnum):
    """Represents the default avatar of a Discord :class:`User`."""

    blurple = 0
    """Represents the default avatar with the color blurple.
    See also :attr:`Colour.blurple`
    """
    grey = 1
    """Represents the default avatar with the color grey.
    See also :attr:`Colour.greyple`
    """
    gray = 1
    """An alias for :attr:`DefaultAvatar.grey`."""
    green = 2
    """Represents the default avatar with the color green.
    See also :attr:`Colour.green`
    """
    orange = 3
    """Represents the default avatar with the color orange.
    See also :attr:`Colour.orange`
    """
    red = 4
    """Represents the default avatar with the color red.
    See also :attr:`Colour.red`
    """
    fuchsia = 5
    """Represents the default avatar with the color fuchsia.
    See also :attr:`Colour.fuchsia`

    .. versionadded:: 2.6
    """
    pink = 5
    """An alias for :attr:`DefaultAvatar.fuchsia`.

    .. versionadded:: 2.6
    """

    def __str__(self) -> str:
        return self.name


class NotificationLevel(IntEnum):
    """Specifies whether a :class:`Guild` has notifications on for all
     messages or mentions only by default.

    .. container:: operations

        .. versionadded:: 2.0

        .. describe:: x == y

            Checks if two notification levels are equal.
        .. describe:: x != y

            Checks if two notification levels are not equal.
        .. describe:: x > y

            Checks if a notification level is higher than another.
        .. describe:: x < y

            Checks if a notification level is lower than another.
        .. describe:: x >= y

            Checks if a notification level is higher or equal to another.
        .. describe:: x <= y

            Checks if a notification level is lower or equal to another.
    """

    all_messages = 0
    """Members receive notifications for every message regardless of them being mentioned."""
    only_mentions = 1
    """Members receive notifications for messages they are mentioned in."""


class AuditLogActionCategory(IntEnum):
    """Represents the category that the :class:`AuditLogAction` belongs to.

    This can be retrieved via :attr:`AuditLogEntry.category`.
    """

    create = 1
    """The action is the creation of something."""
    delete = 2
    """The action is the deletion of something."""
    update = 3
    """The action is the update of something."""


class AuditLogAction(IntEnum):
    # fmt: off
    guild_update                                = 1
    channel_create                              = 10
    channel_update                              = 11
    channel_delete                              = 12
    overwrite_create                            = 13
    overwrite_update                            = 14
    overwrite_delete                            = 15
    kick                                        = 20
    member_prune                                = 21
    ban                                         = 22
    unban                                       = 23
    member_update                               = 24
    member_role_update                          = 25
    member_move                                 = 26
    member_disconnect                           = 27
    bot_add                                     = 28
    role_create                                 = 30
    role_update                                 = 31
    role_delete                                 = 32
    invite_create                               = 40
    invite_update                               = 41
    invite_delete                               = 42
    webhook_create                              = 50
    webhook_update                              = 51
    webhook_delete                              = 52
    emoji_create                                = 60
    emoji_update                                = 61
    emoji_delete                                = 62
    message_delete                              = 72
    message_bulk_delete                         = 73
    message_pin                                 = 74
    message_unpin                               = 75
    integration_create                          = 80
    integration_update                          = 81
    integration_delete                          = 82
    stage_instance_create                       = 83
    stage_instance_update                       = 84
    stage_instance_delete                       = 85
    sticker_create                              = 90
    sticker_update                              = 91
    sticker_delete                              = 92
    scheduled_event_create                      = 100
    scheduled_event_update                      = 101
    scheduled_event_delete                      = 102
    thread_create                               = 110
    thread_update                               = 111
    thread_delete                               = 112
    auto_moderation_rule_create                 = 140
    auto_moderation_rule_update                 = 141
    auto_moderation_rule_delete                 = 142
    auto_moderation_block_message               = 143
    auto_moderation_flag_to_channel             = 144
    auto_moderation_user_communication_disabled = 145
    # fmt: on

    @property
    def category(self) -> Optional[AuditLogActionCategory]:
        # fmt: off
        lookup: Dict[AuditLogAction, Optional[AuditLogActionCategory]] = {
            AuditLogAction.guild_update:                                AuditLogActionCategory.update,
            AuditLogAction.channel_create:                              AuditLogActionCategory.create,
            AuditLogAction.channel_update:                              AuditLogActionCategory.update,
            AuditLogAction.channel_delete:                              AuditLogActionCategory.delete,
            AuditLogAction.overwrite_create:                            AuditLogActionCategory.create,
            AuditLogAction.overwrite_update:                            AuditLogActionCategory.update,
            AuditLogAction.overwrite_delete:                            AuditLogActionCategory.delete,
            AuditLogAction.kick:                                        None,
            AuditLogAction.member_prune:                                None,
            AuditLogAction.ban:                                         None,
            AuditLogAction.unban:                                       None,
            AuditLogAction.member_update:                               AuditLogActionCategory.update,
            AuditLogAction.member_role_update:                          AuditLogActionCategory.update,
            AuditLogAction.member_move:                                 None,
            AuditLogAction.member_disconnect:                           None,
            AuditLogAction.bot_add:                                     None,
            AuditLogAction.role_create:                                 AuditLogActionCategory.create,
            AuditLogAction.role_update:                                 AuditLogActionCategory.update,
            AuditLogAction.role_delete:                                 AuditLogActionCategory.delete,
            AuditLogAction.invite_create:                               AuditLogActionCategory.create,
            AuditLogAction.invite_update:                               AuditLogActionCategory.update,
            AuditLogAction.invite_delete:                               AuditLogActionCategory.delete,
            AuditLogAction.webhook_create:                              AuditLogActionCategory.create,
            AuditLogAction.webhook_update:                              AuditLogActionCategory.update,
            AuditLogAction.webhook_delete:                              AuditLogActionCategory.delete,
            AuditLogAction.emoji_create:                                AuditLogActionCategory.create,
            AuditLogAction.emoji_update:                                AuditLogActionCategory.update,
            AuditLogAction.emoji_delete:                                AuditLogActionCategory.delete,
            AuditLogAction.message_delete:                              AuditLogActionCategory.delete,
            AuditLogAction.message_bulk_delete:                         AuditLogActionCategory.delete,
            AuditLogAction.message_pin:                                 None,
            AuditLogAction.message_unpin:                               None,
            AuditLogAction.integration_create:                          AuditLogActionCategory.create,
            AuditLogAction.integration_update:                          AuditLogActionCategory.update,
            AuditLogAction.integration_delete:                          AuditLogActionCategory.delete,
            AuditLogAction.stage_instance_create:                       AuditLogActionCategory.create,
            AuditLogAction.stage_instance_update:                       AuditLogActionCategory.update,
            AuditLogAction.stage_instance_delete:                       AuditLogActionCategory.delete,
            AuditLogAction.sticker_create:                              AuditLogActionCategory.create,
            AuditLogAction.sticker_update:                              AuditLogActionCategory.update,
            AuditLogAction.sticker_delete:                              AuditLogActionCategory.delete,
            AuditLogAction.scheduled_event_create:                      AuditLogActionCategory.create,
            AuditLogAction.scheduled_event_update:                      AuditLogActionCategory.update,
            AuditLogAction.scheduled_event_delete:                      AuditLogActionCategory.delete,
            AuditLogAction.thread_create:                               AuditLogActionCategory.create,
            AuditLogAction.thread_update:                               AuditLogActionCategory.update,
            AuditLogAction.thread_delete:                               AuditLogActionCategory.delete,
            AuditLogAction.auto_moderation_rule_create:                 AuditLogActionCategory.create,
            AuditLogAction.auto_moderation_rule_update:                 AuditLogActionCategory.update,
            AuditLogAction.auto_moderation_rule_delete:                 AuditLogActionCategory.delete,
            AuditLogAction.auto_moderation_block_message:               None,
            AuditLogAction.auto_moderation_flag_to_channel:             None,
            AuditLogAction.auto_moderation_user_communication_disabled: None,
        }
        # fmt: on
        return lookup[self]

    @property
    def target_type(self) -> Optional[str]:
        v = self.value
        if v == -1:  # pyright: ignore[reportUnnecessaryComparison]
            return "all"
        if v < 10:
            return "guild"
        if v < 20:
            return "channel"
        if v < 30:
            return "user"
        if v < 40:
            return "role"
        if v < 50:
            return "invite"
        if v < 60:
            return "webhook"
        if v < 70:
            return "emoji"
        if v == 73:
            return "channel"
        if v < 80:
            return "message"
        if v < 83:
            return "integration"
        if v < 90:
            return "stage_instance"
        if v < 93:
            return "sticker"
        if v < 103:
            return "event"
        if v < 113:
            return "thread"
        if v < 122:
            return "application_command_or_integration"
        if v < 140:
            return None
        if v == 143:
            return "user"
        if v < 143:
            return "auto_moderation_rule"
        return None


class UserFlags(IntEnum):
    """Represents Discord User flags."""

    staff = 1 << 0
    """The user is a Discord Employee."""
    partner = 1 << 1
    """The user is a Discord Partner."""
    hypesquad = 1 << 2
    """The user is a HypeSquad Events member."""
    bug_hunter = 1 << 3
    """The user is a Bug Hunter."""
    mfa_sms = 1 << 4
    """The user has SMS recovery for Multi Factor Authentication enabled."""
    premium_promo_dismissed = 1 << 5
    """The user has dismissed the Discord Nitro promotion."""
    hypesquad_bravery = 1 << 6
    """The user is a HypeSquad Bravery member."""
    hypesquad_brilliance = 1 << 7
    """The user is a HypeSquad Brilliance member."""
    hypesquad_balance = 1 << 8
    """The user is a HypeSquad Balance member."""
    early_supporter = 1 << 9
    """The user is an Early Supporter."""
    team_user = 1 << 10
    """The user is a Team User."""
    system = 1 << 12
    """The user is a system user (i.e. represents Discord officially)."""
    has_unread_urgent_messages = 1 << 13
    """The user has an unread system message."""
    bug_hunter_level_2 = 1 << 14
    """The user is a Bug Hunter Level 2."""
    verified_bot = 1 << 16
    """The user is a Verified Bot."""
    verified_bot_developer = 1 << 17
    """The user is am Early Verified Bot Developer."""
    discord_certified_moderator = 1 << 18
    """The user is a Discord Certified Moderator."""
    bot_http_interactions = 1 << 19
    """The user is a bot that uses only HTTP interactions and is shown in the
     online member list.

    .. versionadded:: 2.4
    """
    known_spammer = 1 << 20
    """The user is a Known Spammer."""
    active_developer = 1 << 22
    """The user is an Active Developer.

    .. versionadded:: 2.4
    """


class ActivityType(IntEnum):
    """Specifies the type of :class:`Activity`. This is used to check how to
    interpret the activity itself.
    """

    unknown = -1
    """An unknown activity type. This should generally not happen."""
    playing = 0
    """A "Playing" activity type."""
    streaming = 1
    """A "Streaming" activity type."""
    listening = 2
    """A "Listening" activity type."""
    watching = 3
    """A "Watching" activity type."""
    custom = 4
    """A "Custom" activity type."""
    competing = 5
    """A "Competing" activity type.

    .. versionadded:: 1.5
    """


class TeamMembershipState(IntEnum):
    """Represents the membership state of a team member retrieved
     through :func:`Client.application_info`.

    .. versionadded:: 1.3
    """

    invited = 1
    """Represents an invited member."""
    accepted = 2
    """Represents a member currently in the team."""


class WebhookType(IntEnum):
    """Represents the type of webhook that can be received.

    .. versionadded:: 1.3
    """

    incoming = 1
    """Represents a webhook that can post messages to channels with a token."""
    channel_follower = 2
    """Represents a webhook that is internally managed by Discord, used for following channels."""
    application = 3
    """Represents a webhook that is used for interactions or applications.

    .. versionadded:: 2.0
    """


class ExpireBehaviour(IntEnum):
    """Represents the behaviour the :class:`Integration` should perform
    when a user's subscription has finished.

    There is an alias for this called ``ExpireBehavior``.

    .. versionadded:: 1.4
    """

    remove_role = 0
    """This will remove the :attr:`StreamIntegration.role` from the user
     when their subscription is finished.
    """
    kick = 1
    """This will kick the user when their subscription is finished."""


ExpireBehavior = ExpireBehaviour


class StickerType(IntEnum):
    """Represents the type of sticker.

    .. versionadded:: 2.0
    """

    standard = 1
    """Represents a standard sticker."""
    guild = 2
    """Represents a custom sticker created in a guild."""


class StickerFormatType(IntEnum):
    """Represents the type of sticker images.

    .. versionadded:: 1.6
    """

    png = 1
    """Represents a sticker with a png image."""
    apng = 2
    """Represents a sticker with an apng image."""
    lottie = 3
    """Represents a sticker with a lottie image."""
    gif = 4
    """Represents a sticker with a GIF image.

    .. versionadded:: 2.4
    """

    @property
    def file_extension(self) -> str:
        lookup: Dict[StickerFormatType, str] = {
            StickerFormatType.png: "png",
            StickerFormatType.apng: "png",
            StickerFormatType.lottie: "json",
            StickerFormatType.gif: "gif",
        }
        return lookup[self]


class InviteTarget(IntEnum):
    """Represents the invite type for voice channel invites.

    .. versionadded:: 2.0
    """

    unknown = 0
    """The invite doesn't target anyone or anything."""
    stream = 1
    """A stream invite that targets a user."""
    embedded_application = 2
    """A stream invite that targets an embedded application."""


class InteractionType(IntEnum):
    """Specifies the type of :class:`Interaction`.

    .. versionadded:: 2.0
    """

    ping = 1
    """Represents Discord pinging to see if the interaction response server is alive."""
    application_command = 2
    """Represents a slash command or context menu interaction."""
    component = 3
    """Represents a component based interaction, i.e. using the Discord Bot UI Kit."""
    application_command_autocomplete = 4
    """Represents a slash command autocomplete interaction."""
    modal_submit = 5
    """Represents a modal submit interaction."""


class InteractionResponseType(IntEnum):
    """Specifies the response type for the interaction.

    .. versionadded:: 2.0
    """

    pong = 1
    """Pongs the interaction when given a ping.

    See also :meth:`InteractionResponse.pong`
    """
    channel_message = 4  # (with source)
    """Respond to the interaction with a message.

    See also :meth:`InteractionResponse.send_message`
    """
    deferred_channel_message = 5  # (with source)
    """Responds to the interaction with a message at a later time.

    See also :meth:`InteractionResponse.defer`
    """
    deferred_message_update = 6  # for components
    """Acknowledges the component interaction with a promise that
     the message will update later (though there is no need to
     actually update the message).

    See also :meth:`InteractionResponse.defer`
    """
    message_update = 7  # for components
    """Responds to the interaction by editing the message.

    See also :meth:`InteractionResponse.edit_message`
    """
    application_command_autocomplete_result = 8
    modal = 9


class ApplicationCommandType(IntEnum):
    chat_input = 1
    user = 2
    message = 3


class ApplicationCommandOptionType(IntEnum):
    sub_command = 1
    sub_command_group = 2
    string = 3
    integer = 4
    boolean = 5
    user = 6
    channel = 7
    role = 8
    mentionable = 9
    number = 10  # A double, AKA floating point.
    attachment = 11


class Locale(StrEnum):
    da = "da"
    """Danish | Dansk"""
    de = "de"
    """German | Deutsch"""
    en_GB = "en-GB"
    """English, UK | English, UK"""
    en_US = "en-US"
    """English, US | English, US"""
    es_ES = "es-ES"
    """Spanish | Español"""
    fr = "fr"
    """French | Français"""
    hr = "hr"
    """Croatian | Hrvatski"""
    id = "id"
    """Indonesian | Bahasa Indonesia

    .. versionadded:: 2.4
    """
    it = "it"
    """Italian | Italiano"""
    lt = "lt"
    """Lithuanian | Lietuviškai"""
    hu = "hu"
    """Hungarian | Magyar"""
    nl = "nl"
    """Dutch | Nederlands"""
    no = "no"
    """Norwegian | Norsk"""
    pl = "pl"
    """Polish | Polski"""
    pt_BR = "pt-BR"
    """Portuguese, Brazilian | Português do Brasil"""
    ro = "ro"
    """Romanian, Romania | Română"""
    fi = "fi"
    """Finnish | Suomi"""
    sv_SE = "sv-SE"
    """Swedish | Svenska"""
    vi = "vi"
    """Vietnamese | Tiếng Việt"""
    tr = "tr"
    """Turkish | Türkçe"""
    cs = "cs"
    """Czech | Čeština"""
    el = "el"
    """Greek | Ελληνικά"""
    bg = "bg"
    """Bulgarian | български"""
    ru = "ru"
    """Russian | Pусский"""  # noqa: RUF001
    uk = "uk"
    """Ukrainian | Українська"""
    hi = "hi"
    """Hindi | हिन्दी"""
    th = "th"
    """Thai	| ไทย"""
    zh_CN = "zh-CN"
    """Chinese, China | 中文"""
    ja = "ja"
    """Japanese | 日本語"""
    zh_TW = "zh-TW"
    """Chinese, Taiwan | 繁體中文"""
    ko = "ko"
    """Korean | 한국어"""


class VideoQualityMode(IntEnum):
    """Represents the camera video quality mode for voice channel participants.

    .. versionadded:: 2.0
    """

    auto = 1
    """Represents auto camera video quality."""
    full = 2
    """Represents full camera video quality."""


class ComponentType(IntEnum):
    """Represents the component type of a component.

    .. versionadded:: 2.0
    """

    action_row = 1
    """Represents the group component which holds different components in a row."""
    button = 2
    """Represents a button component."""
    select = 3
    """Represents a select string component."""
    string_select = 3
    """An alias for :attr:`ComponentType.select`.

    .. versionadded:: 2.3
    """
    text_input = 4
    """Represents a text input component."""
    user_select = 5
    """Represents a user select component.

    .. versionadded:: 2.3
    """
    role_select = 6
    """Represents a role select component.

    .. versionadded:: 2.3
    """
    mentionable_select = 7
    """Represents a mentionable select component.

    .. versionadded:: 2.3
    """
    channel_select = 8
    """Represents a channel select component.

    .. versionadded:: 2.3
    """


class ButtonStyle(IntEnum):
    """Represents the style of the button component.

    .. versionadded:: 2.0
    """

    primary = 1
    """Represents a blurple button for the primary action."""
    secondary = 2
    """Represents a grey button for secondary actions."""
    success = 3
    """Represents a green button for success actions."""
    danger = 4
    """Represents a red button for dangerous actions."""
    link = 5
    """Represents a link button."""

    # Aliases
    blurple = 1
    """An alias for :attr:`ButtonStyle.primary`."""
    grey = 2
    """An alias for :attr:`ButtonStyle.secondary`."""
    gray = 2
    """An alias for :attr:`ButtonStyle.secondary`."""
    green = 3
    """An alias for :attr:`ButtonStyle.success`."""
    red = 4
    """An alias for :attr:`ButtonStyle.danger`."""
    url = 5
    """An alias for :attr:`ButtonStyle.link`."""


class TextInputStyle(IntEnum):
    """Represent the style of a text input component.

    .. versionadded:: 2.0
    """

    short = 1
    """Represent a single line input."""
    paragraph = 2
    """Represent a multi line input."""


class StagePrivacyLevel(IntEnum):
    """Represents a stage instance's privacy level.

    .. versionadded:: 2.0
    """

    public = 1
    """The stage instance can be joined by external users."""
    closed = 2
    """The stage instance can only be joined by members of the guild."""
    guild_only = 2
    """An alias for :attr:`StagePrivacyLevel.closed`."""


class NSFWLevel(IntEnum):
    """Represents the NSFW level of a guild.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two NSFW levels are equal.
        .. describe:: x != y

            Checks if two NSFW levels are not equal.
        .. describe:: x > y

            Checks if a NSFW level is higher than another.
        .. describe:: x < y

            Checks if a NSFW level is lower than another.
        .. describe:: x >= y

            Checks if a NSFW level is higher or equal to another.
        .. describe:: x <= y

            Checks if a NSFW level is lower or equal to another.
    """

    default = 0
    """The guild has not been categorised yet."""
    explicit = 1
    """The guild contains NSFW content."""
    safe = 2
    """The guild does not contain any NSFW content."""
    age_restricted = 3
    """The guild may contain NSFW content."""


class ScheduledEventEntityType(IntEnum):
    """Represents the type of an entity on a scheduled event."""

    stage_instance = 1
    """The event is for a stage"""
    voice = 2
    """The event is for a voice channel."""
    external = 3
    """The event is happening elsewhere."""


class ScheduledEventPrivacyLevel(IntEnum):
    """Represents the privacy level of scheduled event."""

    guild_only = 2
    """The scheduled event is only visible to members of the guild."""


class ScheduledEventStatus(IntEnum):
    scheduled = 1
    active = 2
    completed = 3
    canceled = 4
    cancelled = 4


class AutoModerationEventType(IntEnum):
    message_send = 1


class AutoModerationTriggerType(IntEnum):
    keyword = 1
    spam = 3
    keyword_preset = 4
    mention_spam = 5


class KeywordPresetType(IntEnum):
    profanity = 1
    sexual_content = 2
    slurs = 3


class AutoModerationActionType(IntEnum):
    block_message = 1
    send_alert_message = 2
    timeout = 3


class SortOrderType(IntEnum):
    latest_activity = 0
    creation_date = 1


class RoleConnectionMetadataType(IntEnum):
    integer_less_than_or_equal = 1
    integer_greater_than_or_equal = 2
    integer_equal = 3
    integer_not_equal = 4
    datetime_less_than_or_equal = 5
    datetime_greater_than_or_equal = 6
    boolean_equal = 7
    boolean_not_equal = 8


class ForumLayoutType(IntEnum):
    not_set = 0
    list = 1
    gallery = 2


T = TypeVar("T")


def try_enum(cls: Type[T], val: Any) -> T:
    """A function that tries to turn the value into enum ``cls``.

    If it fails it returns a proxy invalid value instead.
    """

    try:
        return cls(val)
    except ValueError:
        return UnknownEnumValue(name=f"unknown_{val}", value=val)  # type: ignore
