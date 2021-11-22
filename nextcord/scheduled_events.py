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

from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

from .enums import PrivacyLevel
from .errors import InvalidArgument
from .mixins import Hashable
from .types.scheduled_events import ScheduledEvent as ScheduledEventPayload
from .utils import MISSING, parse_time

__all__: Tuple[str] = (
    'EntityMetadata',
    'ScheduledEvent'
)

if TYPE_CHECKING:
    from datetime import datetime

    from .abc import GuildChannel
    from .enums import EventStatus, EntityType
    from .guild import Guild
    from .state import ConnectionState
    from .user import User


class EntityMetadata:
    def __init__(self, **kwargs) -> None:
        valid_keys = {
            'location'
        }
        for k, v in kwargs.items():
            if k not in valid_keys:
                raise InvalidArgument(f'Invalid key: {k}')
            else:
            setattr(self, k, v)


class ScheduledEvent(Hashable):
    __slots__: Tuple[str] = (
        'channel',
        'channel_id',
        'creator',
        'description',
        'end_time',
        'guild',
        'id',
        'location',
        'name',
        'privacy_level',
        'start_time',
        'user_count',
        '_state'
    )

    def __init__(
        self, *, guild: Guild, state: ConnectionState, data: ScheduledEventPayload
    ) -> None:
        self.guild: Guild = guild
        self._state: ConnectionState = state
        self._from_data(data)

    def _from_data(self, data: ScheduledEventPayload) -> None:
        self.id: int = int(data['id'])
        if creator := data.get('creator'):
            self.creator: Optional[User] = self._state.store_user(creator)
        else:
            self.creator: Optional[User] = None
        self.name: str = data['name']
        self.description: str = data.get('description', '')
        self.start_time: datetime = parse_time(data['scheduled_start_time'])
        self.end_time: Optional[datetime] = parse_time(data['scheduled_end_time'])
        self.privacy_level: PrivacyLevel = PrivacyLevel(data['privacy_level'])
        if (_ := data.get('entity_metadata')) and (location := _.get('location')):
            self.location: str = location
        else:
            self.location: str = ''
        self.user_count: int = data.get('user_count', 0)
        self.channel: Optional[GuildChannel] = self._state.get_channel(
            int(data.get('channel_id'))
        )
        self.channel_id: Optional[int] = data.get('channel_id')

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        value = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
        return f'<{self.__class__.__name__} {value}>'

    async def delete(self) -> None:
        await self._state.http.delete_event(self.guild.id, self.id)
