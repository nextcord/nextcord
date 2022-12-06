# SPDX-License-Identifier: MIT

from typing import List, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired

from .snowflake import Snowflake
from .threads import ThreadArchiveDuration, ThreadMember, ThreadMetadata
from .user import PartialUser

OverwriteType = Literal[0, 1]
SortOrderType = Literal[0, 1]


class PermissionOverwrite(TypedDict):
    id: Snowflake
    type: OverwriteType
    allow: str
    deny: str


ChannelType = Literal[0, 1, 2, 3, 4, 5, 6, 10, 11, 12, 13]


class _BaseChannel(TypedDict):
    id: Snowflake
    name: str


class _BaseGuildChannel(_BaseChannel):
    guild_id: Snowflake
    position: int
    permission_overwrites: List[PermissionOverwrite]
    nsfw: bool
    parent_id: Optional[Snowflake]


class PartialChannel(_BaseChannel):
    type: ChannelType


class TextChannel(_BaseGuildChannel):
    type: Literal[0]
    topic: NotRequired[str]
    last_message_id: NotRequired[Optional[Snowflake]]
    last_pin_timestamp: NotRequired[str]
    rate_limit_per_user: NotRequired[int]
    default_auto_archive_duration: NotRequired[ThreadArchiveDuration]


class ForumChannel(_BaseGuildChannel):
    type: Literal[15]
    topic: NotRequired[str]
    last_message_id: NotRequired[Optional[Snowflake]]
    rate_limit_per_user: NotRequired[int]
    default_auto_archive_duration: NotRequired[ThreadArchiveDuration]
    default_sort_order: Optional[SortOrderType]


class NewsChannel(_BaseGuildChannel):
    type: Literal[5]
    topic: NotRequired[str]
    last_message_id: NotRequired[Optional[Snowflake]]
    last_pin_timestamp: NotRequired[str]
    rate_limit_per_user: NotRequired[int]
    default_auto_archive_duration: NotRequired[ThreadArchiveDuration]


VideoQualityMode = Literal[1, 2]


class VoiceChannel(_BaseGuildChannel):
    type: Literal[2]
    bitrate: int
    user_limit: int
    last_message_id: NotRequired[Optional[Snowflake]]
    rtc_region: NotRequired[Optional[str]]
    video_quality_mode: NotRequired[VideoQualityMode]


class CategoryChannel(_BaseGuildChannel):
    type: Literal[4]


class StageChannel(_BaseGuildChannel):
    type: Literal[13]
    bitrate: int
    user_limit: int
    rtc_region: NotRequired[Optional[str]]
    topic: NotRequired[str]


class ThreadChannel(_BaseChannel):
    type: Literal[10, 11, 12]
    guild_id: Snowflake
    parent_id: Snowflake
    owner_id: Snowflake
    nsfw: bool
    last_message_id: Optional[Snowflake]
    rate_limit_per_user: int
    message_count: int
    member_count: int
    thread_metadata: ThreadMetadata
    member: NotRequired[ThreadMember]
    last_pin_timestamp: NotRequired[str]


GuildChannel = Union[
    TextChannel,
    ForumChannel,
    NewsChannel,
    VoiceChannel,
    CategoryChannel,
    StageChannel,
    ThreadChannel,
]


class DMChannel(_BaseChannel):
    type: Literal[1]
    last_message_id: Optional[Snowflake]
    recipients: List[PartialUser]


class GroupDMChannel(_BaseChannel):
    type: Literal[3]
    icon: Optional[str]
    owner_id: Snowflake


Channel = Union[GuildChannel, DMChannel, GroupDMChannel]

PrivacyLevel = Literal[1, 2]


class StageInstance(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    channel_id: Snowflake
    topic: str
    privacy_level: PrivacyLevel
    discoverable_disabled: bool
