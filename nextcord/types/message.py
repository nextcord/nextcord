# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired

from .channel import ChannelType
from .components import Component
from .embed import Embed
from .emoji import PartialEmoji
from .interactions import MessageInteraction, MessageInteractionMetadata
from .member import Member, UserWithMember
from .snowflake import Snowflake, SnowflakeList
from .sticker import StickerItem
from .user import User


class ChannelMention(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    type: ChannelType
    name: str


class Reaction(TypedDict):
    count: int
    me: bool
    emoji: PartialEmoji


class Attachment(TypedDict):
    id: Snowflake
    filename: str
    size: int
    url: str
    proxy_url: str
    height: NotRequired[Optional[int]]
    width: NotRequired[Optional[int]]
    description: NotRequired[str]
    content_type: NotRequired[str]
    spoiler: NotRequired[bool]
    duration_secs: NotRequired[float]
    waveform: NotRequired[str]
    flags: NotRequired[int]


MessageActivityType = Literal[1, 2, 3, 5]


class MessageActivity(TypedDict):
    type: MessageActivityType
    party_id: str


class MessageApplication(TypedDict):
    id: Snowflake
    description: str
    icon: Optional[str]
    name: str
    cover_image: NotRequired[str]


MessageType = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 18, 19, 20, 21]
MessageReferenceType = Literal[0, 1]


class MessageReference(TypedDict, total=False):
    type: MessageReferenceType
    message_id: Snowflake
    channel_id: Snowflake
    guild_id: Snowflake
    fail_if_not_exists: bool


class MessageSnapshotMessage(TypedDict):
    type: MessageType
    content: str
    embeds: List[Embed]
    attachments: List[Attachment]
    timestamp: str
    edited_timestamp: Optional[str]
    flags: NotRequired[int]
    mentions: List[User]
    mention_roles: SnowflakeList
    sticker_items: NotRequired[List[StickerItem]]
    components: NotRequired[List[Component]]


class MessageSnapshot(TypedDict):
    message: MessageSnapshotMessage


class Message(TypedDict):
    id: Snowflake
    channel_id: Snowflake
    author: User
    content: str
    timestamp: str
    edited_timestamp: Optional[str]
    tts: bool
    mention_everyone: bool
    mentions: List[UserWithMember]
    mention_roles: SnowflakeList
    attachments: List[Attachment]
    embeds: List[Embed]
    pinned: bool
    type: MessageType
    guild_id: NotRequired[Snowflake]
    member: NotRequired[Member]
    mention_channels: NotRequired[List[ChannelMention]]
    reactions: NotRequired[List[Reaction]]
    nonce: NotRequired[Union[int, str]]
    webhook_id: NotRequired[Snowflake]
    activity: NotRequired[MessageActivity]
    application: NotRequired[MessageApplication]
    application_id: NotRequired[Snowflake]
    message_reference: NotRequired[MessageReference]
    message_snapshots: NotRequired[List[MessageSnapshot]]
    referenced_message: NotRequired[Optional[Message]]
    flags: NotRequired[int]
    sticker_items: NotRequired[List[StickerItem]]
    interaction_metadata: NotRequired[MessageInteractionMetadata]
    interaction: NotRequired[MessageInteraction]
    components: NotRequired[List[Component]]


AllowedMentionType = Literal["roles", "users", "everyone"]


class AllowedMentions(TypedDict):
    parse: List[AllowedMentionType]
    roles: SnowflakeList
    users: SnowflakeList
    replied_user: bool
