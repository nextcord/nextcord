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


class StrEnum(str, Enum):
    """An enum that supports comparing and hashing as a string."""

    def __str__(self) -> str:
        return self.value


class ChannelType(IntEnum):
    text = 0
    private = 1
    voice = 2
    group = 3
    category = 4
    news = 5
    news_thread = 10
    public_thread = 11
    private_thread = 12
    stage_voice = 13
    guild_directory = 14
    forum = 15

    def __str__(self) -> str:
        return self.name


class MessageType(IntEnum):
    default = 0
    recipient_add = 1
    recipient_remove = 2
    call = 3
    channel_name_change = 4
    channel_icon_change = 5
    pins_add = 6
    new_member = 7
    premium_guild_subscription = 8
    premium_guild_tier_1 = 9
    premium_guild_tier_2 = 10
    premium_guild_tier_3 = 11
    channel_follow_add = 12
    guild_stream = 13
    guild_discovery_disqualified = 14
    guild_discovery_requalified = 15
    guild_discovery_grace_period_initial_warning = 16
    guild_discovery_grace_period_final_warning = 17
    thread_created = 18
    reply = 19
    chat_input_command = 20
    thread_starter_message = 21
    guild_invite_reminder = 22
    context_menu_command = 23
    auto_moderation_action = 24


class VoiceRegion(StrEnum):
    us_west = "us-west"
    us_east = "us-east"
    us_south = "us-south"
    us_central = "us-central"
    eu_west = "eu-west"
    eu_central = "eu-central"
    singapore = "singapore"
    london = "london"
    sydney = "sydney"
    amsterdam = "amsterdam"
    frankfurt = "frankfurt"
    brazil = "brazil"
    hongkong = "hongkong"
    russia = "russia"
    japan = "japan"
    southafrica = "southafrica"
    south_korea = "south-korea"
    india = "india"
    europe = "europe"
    dubai = "dubai"
    vip_us_east = "vip-us-east"
    vip_us_west = "vip-us-west"
    vip_amsterdam = "vip-amsterdam"


class SpeakingState(IntEnum):
    none = 0
    voice = 1 << 0
    soundshare = 1 << 1
    priority = 1 << 2

    def __str__(self) -> str:
        return self.name


class VerificationLevel(IntEnum):
    none = 0
    low = 1
    medium = 2
    high = 3
    highest = 4

    def __str__(self) -> str:
        return self.name


class ContentFilter(IntEnum):
    disabled = 0
    no_role = 1
    all_members = 2

    def __str__(self) -> str:
        return self.name


class Status(StrEnum):
    online = "online"
    offline = "offline"
    idle = "idle"
    dnd = "dnd"
    do_not_disturb = "dnd"
    invisible = "invisible"


class DefaultAvatar(IntEnum):
    blurple = 0
    grey = 1
    gray = 1
    green = 2
    orange = 3
    red = 4

    def __str__(self) -> str:
        return self.name


class NotificationLevel(IntEnum):
    all_messages = 0
    only_mentions = 1


class AuditLogActionCategory(IntEnum):
    create = 1
    delete = 2
    update = 3


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
        if v == -1:
            return "all"
        elif v < 10:
            return "guild"
        elif v < 20:
            return "channel"
        elif v < 30:
            return "user"
        elif v < 40:
            return "role"
        elif v < 50:
            return "invite"
        elif v < 60:
            return "webhook"
        elif v < 70:
            return "emoji"
        elif v == 73:
            return "channel"
        elif v < 80:
            return "message"
        elif v < 83:
            return "integration"
        elif v < 90:
            return "stage_instance"
        elif v < 93:
            return "sticker"
        elif v < 103:
            return "event"
        elif v < 113:
            return "thread"
        elif v < 122:
            return "application_command_or_integration"
        elif v < 140:
            return None
        elif v == 143:
            return "user"
        elif v < 143:
            return "auto_moderation_rule"
        else:
            return None


class UserFlags(IntEnum):
    staff = 1 << 0
    partner = 1 << 1
    hypesquad = 1 << 2
    bug_hunter = 1 << 3
    mfa_sms = 1 << 4
    premium_promo_dismissed = 1 << 5
    hypesquad_bravery = 1 << 6
    hypesquad_brilliance = 1 << 7
    hypesquad_balance = 1 << 8
    early_supporter = 1 << 9
    team_user = 1 << 10
    system = 1 << 12
    has_unread_urgent_messages = 1 << 13
    bug_hunter_level_2 = 1 << 14
    verified_bot = 1 << 16
    verified_bot_developer = 1 << 17
    discord_certified_moderator = 1 << 18
    bot_http_interactions = 1 << 19
    known_spammer = 1 << 20
    active_developer = 1 << 22


class ActivityType(IntEnum):
    unknown = -1
    playing = 0
    streaming = 1
    listening = 2
    watching = 3
    custom = 4
    competing = 5


class TeamMembershipState(IntEnum):
    invited = 1
    accepted = 2


class WebhookType(IntEnum):
    incoming = 1
    channel_follower = 2
    application = 3


class ExpireBehaviour(IntEnum):
    remove_role = 0
    kick = 1


ExpireBehavior = ExpireBehaviour


class StickerType(IntEnum):
    standard = 1
    guild = 2


class StickerFormatType(IntEnum):
    png = 1
    apng = 2
    lottie = 3
    gif = 4

    @property
    def file_extension(self) -> str:
        # fmt: off
        lookup: Dict[StickerFormatType, str] = {
            StickerFormatType.png: 'png',
            StickerFormatType.apng: 'png',
            StickerFormatType.lottie: 'json',
            StickerFormatType.gif: 'gif',
        }
        # fmt: on
        return lookup[self]


class InviteTarget(IntEnum):
    unknown = 0
    stream = 1
    embedded_application = 2


class InteractionType(IntEnum):
    ping = 1
    application_command = 2
    component = 3
    application_command_autocomplete = 4
    modal_submit = 5


class InteractionResponseType(IntEnum):
    pong = 1
    # ack = 2 (deprecated)
    # channel_message = 3 (deprecated)
    channel_message = 4  # (with source)
    deferred_channel_message = 5  # (with source)
    deferred_message_update = 6  # for components
    message_update = 7  # for components
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
    """Russian | Pусский"""
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
    auto = 1
    full = 2


class ComponentType(IntEnum):
    action_row = 1
    button = 2
    select = 3
    string_select = 3
    text_input = 4
    user_select = 5
    role_select = 6
    mentionable_select = 7
    channel_select = 8


class ButtonStyle(IntEnum):
    primary = 1
    secondary = 2
    success = 3
    danger = 4
    link = 5

    # Aliases
    blurple = 1
    grey = 2
    gray = 2
    green = 3
    red = 4
    url = 5


class TextInputStyle(IntEnum):
    short = 1
    paragraph = 2


class StagePrivacyLevel(IntEnum):
    public = 1
    closed = 2
    guild_only = 2


class NSFWLevel(IntEnum):
    default = 0
    explicit = 1
    safe = 2
    age_restricted = 3


class ScheduledEventEntityType(IntEnum):
    stage_instance = 1
    voice = 2
    external = 3


class ScheduledEventPrivacyLevel(IntEnum):
    guild_only = 2


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
