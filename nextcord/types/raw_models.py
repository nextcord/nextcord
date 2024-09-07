# SPDX-License-Identifier: MIT

from typing import List, TypedDict

from typing_extensions import NotRequired

from ..enums import ReactionType
from .emoji import PartialEmoji
from .member import Member
from .snowflake import Snowflake
from .user import User


class MessageDeleteEvent(TypedDict):
    id: Snowflake
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


class BulkMessageDeleteEvent(TypedDict):
    ids: List[Snowflake]
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


class MessageUpdateEvent(TypedDict):
    id: Snowflake
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


class ReactionActionEvent(TypedDict):
    user_id: Snowflake
    channel_id: Snowflake
    message_id: Snowflake
    emoji: PartialEmoji
    guild_id: NotRequired[Snowflake]
    member: NotRequired[Member]
    burst: bool
    burst_colors: NotRequired[List[str]]
    type: ReactionType


class ReactionClearEvent(TypedDict):
    channel_id: Snowflake
    message_id: Snowflake
    guild_id: NotRequired[Snowflake]


class ReactionClearEmojiEvent(TypedDict):
    channel_id: int
    message_id: int
    emoji: PartialEmoji
    guild_id: NotRequired[Snowflake]
    burst: bool


class IntegrationDeleteEvent(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    application_id: NotRequired[Snowflake]


class TypingEvent(TypedDict):
    channel_id: Snowflake
    user_id: Snowflake
    timestamp: int
    guild_id: NotRequired[Snowflake]
    member: NotRequired[Member]


class MemberRemoveEvent(TypedDict):
    guild_id: Snowflake
    user: User
