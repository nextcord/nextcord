# SPDX-License-Identifier: MIT

from typing import Literal, TypedDict

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
    channel_id: Snowflake
    name: str
    description: str
    scheduled_start_time: str
    scheduled_end_time: str
    privacy_level: ScheduledEventPrivacyLevel
    status: ScheduledEventStatus
    entity_type: ScheduledEventEntityType
    entity_id: Snowflake
    entity_metadata: EntityMetadata
    creator: User
    user_count: int
    image: str


class ScheduledEventUser(TypedDict):
    guild_scheduled_event_id: Snowflake
    user: User
    member: Member
