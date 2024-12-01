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
    "InviteType",
    "IntegrationType",
    "InteractionContextType",
    "MessageReferenceType",
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


class StrEnum(str, Enum):
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
    r"""Represents the type of action being done for a :class:`AuditLogEntry`\,
    which is retrievable via :meth:`nextcord.Guild.audit_logs`.
    """

    guild_update = 1
    """The guild has updated. Things that trigger this include:

    - Changing the guild vanity URL
    - Changing the guild invite splash
    - Changing the guild AFK channel or timeout
    - Changing the guild voice server region
    - Changing the guild icon, banner, or discovery splash
    - Changing the guild moderation settings
    - Changing things related to the guild widget

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Guild`.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.afk_channel`
    - :attr:`~nextcord.AuditLogDiff.system_channel`
    - :attr:`~nextcord.AuditLogDiff.afk_timeout`
    - :attr:`~nextcord.AuditLogDiff.default_message_notifications`
    - :attr:`~nextcord.AuditLogDiff.explicit_content_filter`
    - :attr:`~nextcord.AuditLogDiff.mfa_level`
    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.owner`
    - :attr:`~nextcord.AuditLogDiff.splash`
    - :attr:`~nextcord.AuditLogDiff.discovery_splash`
    - :attr:`~nextcord.AuditLogDiff.icon`
    - :attr:`~nextcord.AuditLogDiff.banner`
    - :attr:`~nextcord.AuditLogDiff.vanity_url_code`
    """
    channel_create = 10
    """A new channel was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    either a :class:`abc.GuildChannel` or :class:`Object` with an ID.

    A more filled out object in the :class:`Object` case can be found
    by using :attr:`~AuditLogEntry.after`.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.type`
    - :attr:`~nextcord.AuditLogDiff.overwrites`
    """
    channel_update = 11
    """A channel was updated. Things that trigger this include:

    - The channel name or topic was changed
    - The channel bitrate was changed

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`abc.GuildChannel` or :class:`Object` with an ID.

    A more filled out object in the :class:`Object` case can be found
    by using :attr:`~AuditLogEntry.after` or :attr:`~AuditLogEntry.before`.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.type`
    - :attr:`~nextcord.AuditLogDiff.position`
    - :attr:`~nextcord.AuditLogDiff.overwrites`
    - :attr:`~nextcord.AuditLogDiff.topic`
    - :attr:`~nextcord.AuditLogDiff.bitrate`
    - :attr:`~nextcord.AuditLogDiff.rtc_region`
    - :attr:`~nextcord.AuditLogDiff.video_quality_mode`
    - :attr:`~nextcord.AuditLogDiff.default_auto_archive_duration`
    """
    channel_delete = 12
    """A channel was deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    an :class:`Object` with an ID.

    A more filled out object can be found by using the
    :attr:`~AuditLogEntry.before` object.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.type`
    - :attr:`~nextcord.AuditLogDiff.overwrites`
    """
    overwrite_create = 13
    """A channel permission overwrite was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`abc.GuildChannel` or :class:`Object` with an ID.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    either a :class:`Role` or :class:`Member`. If the object is not found
    then it is a :class:`Object` with an ID being filled, a name, and a
    ``type`` attribute set to either ``'role'`` or ``'member'`` to help
    dictate what type of ID it is.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.deny`
    - :attr:`~nextcord.AuditLogDiff.allow`
    - :attr:`~nextcord.AuditLogDiff.id`
    - :attr:`~nextcord.AuditLogDiff.type`
    """
    overwrite_update = 14
    """A channel permission overwrite was changed, this is typically
    when the permission values change.

    See :attr:`overwrite_create` for more information on how the
    :attr:`~AuditLogEntry.target` and :attr:`~AuditLogEntry.extra` fields
    are set.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.deny`
    - :attr:`~nextcord.AuditLogDiff.allow`
    - :attr:`~nextcord.AuditLogDiff.id`
    - :attr:`~nextcord.AuditLogDiff.type`
    """
    overwrite_delete = 15
    """A channel permission overwrite was deleted.

    See :attr:`overwrite_create` for more information on how the
    :attr:`~AuditLogEntry.target` and :attr:`~AuditLogEntry.extra` fields
    are set.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.deny`
    - :attr:`~nextcord.AuditLogDiff.allow`
    - :attr:`~nextcord.AuditLogDiff.id`
    - :attr:`~nextcord.AuditLogDiff.type`
    """
    kick = 20
    """A member was kicked.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`User` who got kicked.

    When this is the action, :attr:`~AuditLogEntry.changes` is empty.
    """
    member_prune = 21
    """A member prune was triggered.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    set to ``None``.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    set to an unspecified proxy object with two attributes:

    - ``delete_members_days``: An integer specifying how far the prune was.
    - ``members_removed``: An integer specifying how many members were removed.

    When this is the action, :attr:`~AuditLogEntry.changes` is empty.
    """
    ban = 22
    """A member was banned.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`User` who got banned.

    When this is the action, :attr:`~AuditLogEntry.changes` is empty.
    """
    unban = 23
    """A member was unbanned.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`User` who got unbanned.

    When this is the action, :attr:`~AuditLogEntry.changes` is empty.
    """
    member_update = 24
    """A member has updated. This triggers in the following situations:

    - A nickname was changed
    - They were server muted or deafened (or it was undo'd)

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Member` or :class:`User` who got updated.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.nick`
    - :attr:`~nextcord.AuditLogDiff.mute`
    - :attr:`~nextcord.AuditLogDiff.deaf`
    """
    member_role_update = 25
    """A member's role has been updated. This triggers when a member
    either gains a role or loses a role.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Member` or :class:`User` who got the role.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.roles`
    """
    member_move = 26
    """A member's voice channel has been updated. This triggers when a
    member is moved to a different voice channel.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    set to an unspecified proxy object with two attributes:

    - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the members were moved.
    - ``count``: An integer specifying how many members were moved.

    .. versionadded:: 1.3
    """
    member_disconnect = 27
    """A member's voice state has changed. This triggers when a
    member is force disconnected from voice.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    set to an unspecified proxy object with one attribute:

    - ``count``: An integer specifying how many members were disconnected.

    .. versionadded:: 1.3
    """
    bot_add = 28
    """A bot was added to the guild.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Member` or :class:`User` which was added to the guild.

    .. versionadded:: 1.3
    """
    role_create = 30
    """A new role was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Role` or a :class:`Object` with the ID.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.colour`
    - :attr:`~nextcord.AuditLogDiff.mentionable`
    - :attr:`~nextcord.AuditLogDiff.hoist`
    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.permissions`
    """
    role_update = 31
    """A role was updated. This triggers in the following situations:

    - The name has changed
    - The permissions have changed
    - The colour has changed
    - Its hoist/mentionable state has changed

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Role` or a :class:`Object` with the ID.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.colour`
    - :attr:`~nextcord.AuditLogDiff.mentionable`
    - :attr:`~nextcord.AuditLogDiff.hoist`
    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.permissions`
    """
    role_delete = 32
    """A role was deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Role` or a :class:`Object` with the ID.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.colour`
    - :attr:`~nextcord.AuditLogDiff.mentionable`
    - :attr:`~nextcord.AuditLogDiff.hoist`
    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.permissions`
    """
    invite_create = 40
    """An invite was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Invite` that was created.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.max_age`
    - :attr:`~nextcord.AuditLogDiff.code`
    - :attr:`~nextcord.AuditLogDiff.temporary`
    - :attr:`~nextcord.AuditLogDiff.inviter`
    - :attr:`~nextcord.AuditLogDiff.channel`
    - :attr:`~nextcord.AuditLogDiff.uses`
    - :attr:`~nextcord.AuditLogDiff.max_uses`
    """
    invite_update = 41
    """An invite was updated.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Invite` that was updated.
    """
    invite_delete = 42
    """An invite was deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Invite` that was deleted.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.max_age`
    - :attr:`~nextcord.AuditLogDiff.code`
    - :attr:`~nextcord.AuditLogDiff.temporary`
    - :attr:`~nextcord.AuditLogDiff.inviter`
    - :attr:`~nextcord.AuditLogDiff.channel`
    - :attr:`~nextcord.AuditLogDiff.uses`
    - :attr:`~nextcord.AuditLogDiff.max_uses`
    """
    webhook_create = 50
    """A webhook was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Object` with the webhook ID.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.channel`
    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.type` (always set to ``1`` if so)
    """
    webhook_update = 51
    """A webhook was updated. This trigger in the following situations:

    - The webhook name changed
    - The webhook channel changed

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Object` with the webhook ID.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.channel`
    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.avatar`
    """
    webhook_delete = 52
    """A webhook was deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Object` with the webhook ID.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.channel`
    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.type` (always set to ``1`` if so)
    """
    emoji_create = 60
    """An emoji was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Emoji` or :class:`Object` with the emoji ID.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    """
    emoji_update = 61
    """An emoji was updated. This triggers when the name has changed.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Emoji` or :class:`Object` with the emoji ID.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    """
    emoji_delete = 62
    """An emoji was deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Object` with the emoji ID.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    """
    message_delete = 72
    """A message was deleted by a moderator. Note that this
    only triggers if the message was deleted by someone other than the author.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Member` or :class:`User` who had their message deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    set to an unspecified proxy object with two attributes:

    - ``count``: An integer specifying how many messages were deleted.
    - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the message got deleted.
    """
    message_bulk_delete = 73
    """Messages were bulk deleted by a moderator.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`TextChannel` or :class:`Object` with the ID of the channel that was purged.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    set to an unspecified proxy object with one attribute:

    - ``count``: An integer specifying how many messages were deleted.

    .. versionadded:: 1.3
    """
    message_pin = 74
    """A message was pinned in a channel.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Member` or :class:`User` who had their message pinned.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    set to an unspecified proxy object with two attributes:

    - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the message was pinned.
    - ``message_id``: the ID of the message which was pinned.

    .. versionadded:: 1.3
    """
    message_unpin = 75
    """A message was unpinned in a channel.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Member` or :class:`User` who had their message unpinned.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    set to an unspecified proxy object with two attributes:

    - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the message was unpinned.
    - ``message_id``: the ID of the message which was unpinned.

    .. versionadded:: 1.3
    """
    integration_create = 80
    """A guild integration was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Object` with the integration ID of the integration which was created.

    .. versionadded:: 1.3
    """
    integration_update = 81
    """A guild integration was updated.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Object` with the integration ID of the integration which was updated.

    .. versionadded:: 1.3
    """
    integration_delete = 82
    """A guild integration was deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Object` with the integration ID of the integration which was deleted.

    .. versionadded:: 1.3
    """
    stage_instance_create = 83
    """A stage instance was started.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`StageInstance` or :class:`Object` with the ID of the stage
    instance which was created.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.topic`
    - :attr:`~nextcord.AuditLogDiff.privacy_level`

    .. versionadded:: 2.0
    """
    stage_instance_update = 84
    """A stage instance was updated.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`StageInstance` or :class:`Object` with the ID of the stage
    instance which was updated.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.topic`
    - :attr:`~nextcord.AuditLogDiff.privacy_level`

    .. versionadded:: 2.0
    """
    stage_instance_delete = 85
    """A stage instance was ended.

    .. versionadded:: 2.0
    """
    sticker_create = 90
    """A sticker was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`GuildSticker` or :class:`Object` with the ID of the sticker
    which was updated.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.emoji`
    - :attr:`~nextcord.AuditLogDiff.type`
    - :attr:`~nextcord.AuditLogDiff.format_type`
    - :attr:`~nextcord.AuditLogDiff.description`
    - :attr:`~nextcord.AuditLogDiff.available`

    .. versionadded:: 2.0
    """
    sticker_update = 91
    """A sticker was updated.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`GuildSticker` or :class:`Object` with the ID of the sticker
    which was updated.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.emoji`
    - :attr:`~nextcord.AuditLogDiff.type`
    - :attr:`~nextcord.AuditLogDiff.format_type`
    - :attr:`~nextcord.AuditLogDiff.description`
    - :attr:`~nextcord.AuditLogDiff.available`

    .. versionadded:: 2.0
    """
    sticker_delete = 92
    """A sticker was deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`GuildSticker` or :class:`Object` with the ID of the sticker
    which was updated.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.emoji`
    - :attr:`~nextcord.AuditLogDiff.type`
    - :attr:`~nextcord.AuditLogDiff.format_type`
    - :attr:`~nextcord.AuditLogDiff.description`
    - :attr:`~nextcord.AuditLogDiff.available`

    .. versionadded:: 2.0
    """
    scheduled_event_create = 100
    """A scheduled event was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`ScheduledEvent` or :class:`Object` with the ID of the scheduled event which
    was created.
    """
    scheduled_event_update = 101
    """A scheduled event was updated.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`ScheduledEvent` or :class:`Object` with the ID of the scheduled event which
    was created.
    """
    scheduled_event_delete = 102
    """A scheduled event was deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`ScheduledEvent` or :class:`Object` with the ID of the scheduled event which
    was created.
    """
    thread_create = 110
    """A thread was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Thread` or :class:`Object` with the ID of the thread which
    was created.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.archived`
    - :attr:`~nextcord.AuditLogDiff.locked`
    - :attr:`~nextcord.AuditLogDiff.auto_archive_duration`

    .. versionadded:: 2.0
    """
    thread_update = 111
    """A thread was updated.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Thread` or :class:`Object` with the ID of the thread which
    was updated.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.archived`
    - :attr:`~nextcord.AuditLogDiff.locked`
    - :attr:`~nextcord.AuditLogDiff.auto_archive_duration`

    .. versionadded:: 2.0
    """
    thread_delete = 112
    """A thread was deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Thread` or :class:`Object` with the ID of the thread which
    was deleted.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.archived`
    - :attr:`~nextcord.AuditLogDiff.locked`
    - :attr:`~nextcord.AuditLogDiff.auto_archive_duration`

    .. versionadded:: 2.0
    """
    auto_moderation_rule_create = 140
    """An auto moderation rule was created.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`AutoModerationRule` or :class:`Object` with the ID of the
    rule which was created.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.actions`
    - :attr:`~nextcord.AuditLogDiff.enabled`
    - :attr:`~nextcord.AuditLogDiff.exempt_channels`
    - :attr:`~nextcord.AuditLogDiff.exempt_roles`
    - :attr:`~nextcord.AuditLogDiff.event_type`
    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.trigger_type`
    - :attr:`~nextcord.AuditLogDiff.trigger_metadata`

    .. versionadded:: 2.1
    """
    auto_moderation_rule_update = 141
    """An auto moderation rule was updated.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`AutoModerationRule` or :class:`Object` with the ID of the
    rule which was updated.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.actions`
    - :attr:`~nextcord.AuditLogDiff.enabled`
    - :attr:`~nextcord.AuditLogDiff.exempt_channels`
    - :attr:`~nextcord.AuditLogDiff.exempt_roles`
    - :attr:`~nextcord.AuditLogDiff.event_type`
    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.trigger_type`
    - :attr:`~nextcord.AuditLogDiff.trigger_metadata`

    .. versionadded:: 2.1
    """
    auto_moderation_rule_delete = 142
    """An auto moderation rule was deleted.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`AutoModerationRule` or :class:`Object` with the ID of the
    rule which was deleted.

    Possible attributes for :class:`nextcord.AuditLogDiff`:

    - :attr:`~nextcord.AuditLogDiff.actions`
    - :attr:`~nextcord.AuditLogDiff.enabled`
    - :attr:`~nextcord.AuditLogDiff.exempt_channels`
    - :attr:`~nextcord.AuditLogDiff.exempt_roles`
    - :attr:`~nextcord.AuditLogDiff.event_type`
    - :attr:`~nextcord.AuditLogDiff.name`
    - :attr:`~nextcord.AuditLogDiff.trigger_type`
    - :attr:`~nextcord.AuditLogDiff.trigger_metadata`

    .. versionadded:: 2.1
    """
    auto_moderation_block_message = 143
    """A message was blocked by an auto moderation rule.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Member` or :class:`User` whose message was blocked.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    set to an unspecified proxy object with these three attributes:

    - ``channel``: A :class:`~abc.GuildChannel`, :class:`Thread` or :class:`Object` with the channel ID where the message was blocked.
    - ``rule_name``: A :class:`str` with the name of the rule.
    - ``rule_trigger_type``: A :class:`AutoModerationTriggerType` value with the trigger type of the rule.

    .. versionadded:: 2.1
    """
    auto_moderation_flag_to_channel = 144
    """A message was flagged by an auto moderation rule.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Member` or :class:`User` whose message was flagged.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    set to an unspecified proxy object with these three attributes:

    - ``channel``: A :class:`~abc.GuildChannel`, :class:`Thread` or :class:`Object` with the channel ID where the message was flagged.
    - ``rule_name``: A :class:`str` with the name of the rule.
    - ``rule_trigger_type``: A :class:`AutoModerationTriggerType` value with the trigger type of the rule.

    .. versionadded:: 2.3
    """
    auto_moderation_user_communication_disabled = 145
    """A member was timed out by an auto moderation rule.

    When this is the action, the type of :attr:`~AuditLogEntry.target` is
    the :class:`Member` or :class:`User` who was timed out.

    When this is the action, the type of :attr:`~AuditLogEntry.extra` is
    set to an unspecified proxy object with these three attributes:

    - ``channel``: A :class:`~abc.GuildChannel`, :class:`Thread` or :class:`Object` with the channel ID where the member was timed out.
    - ``rule_name``: A :class:`str` with the name of the rule.
    - ``rule_trigger_type``: A :class:`AutoModerationTriggerType` value with the trigger type of the rule.

    .. versionadded:: 2.3
    """

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
    """The user is an Early Verified Bot Developer."""
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
    """Represents the type of application command.

    .. versionadded:: 2.0
    """

    chat_input = 1
    """The command is a slash command."""
    user = 2
    """The command is a user context menu command."""
    message = 3
    """The command is a message context menu command."""


class ApplicationCommandOptionType(IntEnum):
    """Represents the type of application command option.

    .. versionadded:: 2.0
    """

    sub_command = 1
    """The option is a subcommand."""
    sub_command_group = 2
    """The option is a subcommand group."""
    string = 3
    """The option is a string."""
    integer = 4
    """The option is an integer."""
    boolean = 5
    """The option is a boolean."""
    user = 6
    """The option is a user."""
    channel = 7
    """The option is a channel."""
    role = 8
    """The option is a role."""
    mentionable = 9
    """The option is a mentionable."""
    number = 10
    """The option is a number. This is a double, AKA floating point."""
    attachment = 11
    """The option is an attachment."""


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
    """Represents the status of a scheduled event."""

    scheduled = 1
    """The event is scheduled to happen."""
    active = 2
    """The event is happening."""
    completed = 3
    """The event has finished."""
    canceled = 4
    """The event was cancelled."""
    cancelled = 4
    """An alias for :attr:`ScheduledEventStatus.canceled`."""


class AutoModerationEventType(IntEnum):
    """Represents what event context an auto moderation rule will be checked.

    .. versionadded:: 2.1
    """

    message_send = 1
    """A member sends or edits a message in the guild."""


class AutoModerationTriggerType(IntEnum):
    """Represents the type of content which can trigger an auto moderation rule.

    .. versionadded:: 2.1

    .. versionchanged:: 2.2

        Removed ``harmful_link`` as it is no longer used by Discord.
    """

    keyword = 1
    """This rule checks if content contains words from a user defined list of keywords."""
    spam = 3
    """This rule checks if content represents generic spam."""
    keyword_preset = 4
    """This rule checks if content contains words from Discord pre-defined wordsets."""
    mention_spam = 5
    """This rule checks if the number of mentions in the message is more than the maximum allowed.

    .. versionadded:: 2.3
    """


class KeywordPresetType(IntEnum):
    """Represents the type of a keyword preset auto moderation rule.

    .. versionadded:: 2.1
    """

    profanity = 1
    """Words that may be considered forms of swearing or cursing."""
    sexual_content = 2
    """Words that refer to sexually explicit behaviour or activity."""
    slurs = 3
    """Personal insults or words that may be considered hate speech."""


class AutoModerationActionType(IntEnum):
    """Represents the action that will be taken if an auto moderation rule is triggered.

    .. versionadded:: 2.1
    """

    block_message = 1
    """Blocks a message with content matching the rule."""
    send_alert_message = 2
    """Logs message content to a specified channel."""
    timeout = 3
    """Timeout user for a specified duration.

    .. note::

        This action type can only be used with the :attr:`Permissions.moderate_members` permission.
    """


class SortOrderType(IntEnum):
    """The default sort order type used to sort posts in a :class:`ForumChannel`.

    .. versionadded:: 2.3
    """

    latest_activity = 0
    """Sort forum posts by their activity."""
    creation_date = 1
    """Sort forum posts by their creation date."""


class RoleConnectionMetadataType(IntEnum):
    """Represents the type of comparison a role connection metadata record will use.

    .. versionadded:: 2.4
    """

    integer_less_than_or_equal = 1
    integer_greater_than_or_equal = 2
    """The metadata value must be less than or equal to the guild's configured value."""
    integer_equal = 3
    integer_not_equal = 4
    """The metadata value must be greater than or equal to the guild's configured value."""
    datetime_less_than_or_equal = 5
    datetime_greater_than_or_equal = 6
    """The metadata value must be equal to the guild's configured value."""
    boolean_equal = 7
    boolean_not_equal = 8
    """The metadata value must be not equal to the guild's configured value."""


class ForumLayoutType(IntEnum):
    """The default layout type used to display posts in a :class:`ForumChannel`.

    .. versionadded:: 2.4
    """

    not_set = 0
    """No default has been set by channel administrators."""
    list = 1
    """Display posts as a list, more text focused."""
    gallery = 2
    """Display posts as a collection of posts with images, this is more image focused."""


class InviteType(IntEnum):
    """Represents the type of an invite.

    .. versionadded:: 3.0
    """

    guild = 0
    """The invite is for a guild."""
    group_dm = 1
    """The invite is for a group DM."""
    friend = 2
    """The invite is for a Discord user."""


class IntegrationType(IntEnum):
    """Where a :class:`BaseApplicationCommand` is available, only for globally-scoped commands.

    .. versionadded:: 3.0
    """

    guild_install = 0
    """App is installable to servers."""
    user_install = 1
    """App is installable to users."""


class InteractionContextType(IntEnum):
    """Where a :class:`BaseApplicationCommand` can be used, only for globally-scoped commands, or where a :class:`Interaction` originates from.

    .. versionadded:: 3.0
    """

    guild = 0
    """The :class:`BaseApplicationCommand` can be used within servers, or the :class:`Interaction` originates from a server."""
    bot_dm = 1
    """The :class:`BaseApplicationCommand` can be used within DMs with the app's bot user, or the :class:`Interaction` originates from such DMs."""
    private_channel = 2
    """The :class:`BaseApplicationCommand` can be used within Group DMs and DMs other than the app's bot user, or the :class:`Interaction` originates from such channels."""


class MessageReferenceType(IntEnum):
    """Represents the type of reference that a message is.

    .. versionadded:: 3.0
    """

    default = 0
    """The reference is used as a reply."""
    forward = 1
    """The reference is used to point to a message."""


T = TypeVar("T")


def try_enum(cls: Type[T], val: Any) -> T:
    """A function that tries to turn the value into enum ``cls``.

    If it fails it returns a proxy invalid value instead.
    """

    try:
        return cls(val)
    except ValueError:
        return UnknownEnumValue(name=f"unknown_{val}", value=val)  # type: ignore
