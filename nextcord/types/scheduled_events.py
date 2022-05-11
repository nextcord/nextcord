"""
The MIT License (MIT)

Copyright (c) 2021-present tag-epic

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from typing import Literal, TypedDict

from .member import Member
from .snowflake import Snowflake
from .user import User

ScheduledEventEntityType = Literal[1, 2, 3]
ScheduledEventPrivacyLevel = Literal[2]
ScheduledEventStatus = Literal[1, 2, 3, 4]


class EntityMetadata(TypedDict, total=False):
    location: str


class ScheduledEvent(TypedDict, total=False):
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

class ScheduledEventUser(TypedDict, total=False):
    guild_scheduled_event_id: Snowflake
    user: User
    member: Member
