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

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from .enums import ScheduledEventPrivacyLevel
from .iterators import ScheduledEventUserIterator
from .mixins import Hashable
from .types.snowflake import Snowflake
from .utils import MISSING, parse_time

__all__: Tuple[str] = (
    'EntityMetadata',
    'ScheduledEventUser',
    'ScheduledEvent'
)

if TYPE_CHECKING:
    from datetime import datetime

    from .abc import GuildChannel
    from .enums import ScheduledEventStatus, EntityType
    from .guild import Guild
    from .member import Member
    from .state import ConnectionState
    from .types.scheduled_events import (
        ScheduledEvent as ScheduledEventPayload,
        ScheduledEventUser as ScheduledEventUserPayload
    )
    from .user import User


class EntityMetadata:
    __slots__: Tuple[str] = (
        'location'
    )

    def __init__(self, *, location: Optional[str] = None, **kwargs: Any) -> None:
        self.location: Optional[str] = location
        for k, v in kwargs.items():
            setattr(self, k, v)


class ScheduledEventUser(Hashable):
    __slots__: Tuple[str] = (
        'event',
        'user',
        'member'
    )

    def __init__(
        self,
        *,
        event: ScheduledEvent,
        state: ConnectionState,
        data: ScheduledEventUserPayload
    ) -> None:
        self.event = event
        self._state = state

        self._update(data)

    def _update(self, data: ScheduledEventUserPayload) -> None:
        self.user: User = self._state.store_user(data['user'])
        if member := data.get('member'):
            if not self._state.member_cache_flags._empty:
                try:
                    self.member: Optional[Member] = self.guild.get_member(
                        member['id']
                    )
                except KeyError:
                    m = Member(data=member, guild=self.guild, state=self._state)
                    self.member: Optional[Member] = m
            else:
                m = Member(data=member, guild=self.guild, state=self._state)
                self.member: Optional[Member] = m
        else:
            self.member: Optional[Member] = None


class ScheduledEvent(Hashable):
    __slots__: Tuple[str] = (
        'channel',
        'channel_id',
        'creator',
        'description',
        'end_time',
        'guild',
        'id',
        'metadata',
        'name',
        'privacy_level',
        'start_time',
        'user_count',
        '_state',
        '_users',
    )

    def __init__(
        self, *, guild: Guild, state: ConnectionState, data: ScheduledEventPayload
    ) -> None:
        self.guild: Guild = guild
        self._state: ConnectionState = state
        self._update(data)

    def _update(self, data: ScheduledEventPayload) -> None:
        self.id: int = int(data['id'])
        if creator := data.get('creator'):
            self.creator: Optional[User] = self._state.store_user(creator)
        else:
            self.creator: Optional[User] = None
        self.name: str = data['name']
        self.description: str = data.get('description', '')
        self.start_time: datetime = parse_time(data['scheduled_start_time'])
        self.end_time: Optional[datetime] = parse_time(data['scheduled_end_time'])
        self.privacy_level: ScheduledEventPrivacyLevel = ScheduledEventPrivacyLevel(
            data['privacy_level']
        )
        self.metadata: EntityMetadata = EntityMetadata(**data.get('metadata', {}))
        self.user_count: int = data.get('user_count', 0)
        self.channel: Optional[GuildChannel] = self._state.get_channel(
            int(data.get('channel_id') or 0)
        )
        self.channel_id: Optional[int] = data.get('channel_id')
        self._users: Dict[int, ScheduledEventUser] = {}
        self._update_users(data.get('users', []))

    def _update_users(self, data: List[ScheduledEventUserPayload]) -> None:
        for user in data:
            self._users[user['user']['id']] = ScheduledEventUser(
                event=self, state=self._state, data=user
            )

    def _update_user(self, data: ScheduledEventUserPayload) -> ScheduledEventUser:
        if user := self._users.get(data['user']['id']):
            user._update(data)
        else:
            user = ScheduledEventUser(event=self, state=self._state, data=data)
            self._users[user.user.id] = user
        return user

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        attrs: List[Tuple[str, Any]] = [
            ('id', self.id),
            ('name', self.name),
            ('guild_id', self.guild),
            ('description', self.description),
            ('start_time', self.start_time),
            ('end_time', self.end_time),
        ]
        joined = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {joined}>'

    @property
    def location(self) -> str:
        return self.metadata.location

    @property  # TODO: mention in docs its not accurate until fetch users
    def users(self) -> ScheduledEventUser:
        return list(self._users.values())
 
    async def delete(self) -> None:
        await self._state.http.delete_event(self.guild.id, self.id)

    async def edit(
        self,
        *,
        channel: Optional[GuildChannel] = MISSING,
        metadata: Optional[EntityMetadata] = MISSING,
        name: str = MISSING,
        privacy_level: Optional[ScheduledEventPrivacyLevel] = MISSING,
        start_time: Optional[datetime] = MISSING,
        end_time: Optional[datetime] = MISSING,
        description: str = MISSING,
        type: Optional[EntityType] = MISSING,
        status: Optional[ScheduledEventStatus] = MISSING
    ) -> ScheduledEvent:
        payload: dict = {}
        if channel is not MISSING:
            payload['channel_id'] = channel.id
        if metadata is not MISSING:
            payload['entity_metadata'] = metadata.__dict__
        if name is not MISSING:
            payload['name'] = name
        if privacy_level is not MISSING:
            payload['privacy_level'] = privacy_level.value
        if start_time is not MISSING:
            payload['scheduled_start_time'] = start_time.isoformat()
        if end_time is not MISSING:
            payload['scheduled_end_time'] = end_time.isoformat()
        if description is not MISSING:
            payload['description'] = description
        if type is not MISSING:
            payload['type'] = type.value
        if status is not MISSING:
            payload['status'] = status.value
        if not payload:
            return self
        data = self._state.http.edit_event(**payload)
        return ScheduledEvent(guild=self.guild, state=self._state, data=data)

    def get_user(self, id: int) -> ScheduledEventUser:
        return self._users.get(id)

    async def fetch_users(
        self,
        *,
        limit: int = 100,
        with_member: bool = False,
        before: Snowflake = None,
        after: Snowflake = None
    ) -> ScheduledEventUserIterator:
        return ScheduledEventUserIterator(
            self.guild,
            self,
            limit=limit,
            with_member=with_member,
            before=before,
            after=after
        )
