# SPDX-License-Identifier: MIT

from typing import Literal, Optional, TypedDict

from typing_extensions import NotRequired

from .member import Member
from .snowflake import Snowflake
from .user import User

ScheduledEventEntityType = Literal[1, 2, 3]
ScheduledEventPrivacyLevel = Literal[2]
ScheduledEventStatus = Literal[1, 2, 3, 4]


class EntityMetadata(TypedDict, total=False):
    location: str


class ScheduledEvent(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    channel_id: Optional[Snowflake]
    creator_id: NotRequired[int]
    name: str
    description: NotRequired[Optional[str]]
    scheduled_start_time: str
    scheduled_end_time: Optional[str]
    privacy_level: ScheduledEventPrivacyLevel
    status: ScheduledEventStatus
    entity_type: ScheduledEventEntityType
    entity_id: Optional[Snowflake]
    entity_metadata: Optional[EntityMetadata]
    creator: NotRequired[User]
    user_count: NotRequired[int]
    image: NotRequired[Optional[str]]


class ScheduledEventUser(TypedDict):
    guild_scheduled_event_id: Snowflake
    user: User
    member: Member
