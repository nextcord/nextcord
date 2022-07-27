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

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from .abc import Snowflake
from .asset import Asset
from .enums import ScheduledEventPrivacyLevel
from .iterators import ScheduledEventUserIterator
from .mixins import Hashable
from .utils import MISSING, _obj_to_base64_data, parse_time

__all__: Tuple[str, ...] = (
    "EntityMetadata",
    "ScheduledEventUser",
    "ScheduledEvent",
)

if TYPE_CHECKING:
    from datetime import datetime

    from .abc import GuildChannel
    from .enums import ScheduledEventEntityType, ScheduledEventStatus
    from .file import File
    from .guild import Guild
    from .member import Member
    from .message import Attachment
    from .state import ConnectionState
    from .types.scheduled_events import (
        ScheduledEvent as ScheduledEventPayload,
        ScheduledEventUser as ScheduledEventUserPayload,
    )
    from .user import User


class EntityMetadata:
    """Represents the metadata for an event

    Parameters
    ----------
    location : Optional[str]
        The location of the event, defaults to None
    """

    # kwargs is for if more attributes are added to the api, prevent breakage
    def __init__(self, *, location: Optional[str] = None, **kwargs: Any) -> None:
        self.location: Optional[str] = location
        for k, v in kwargs.items():
            setattr(self, k, v)


class ScheduledEventUser(Hashable):
    """Represents a user in a scheduled event

    Attributes
    ----------
    event: :class:`ScheduledEvent`
        The event the user is interested in.
    user: Optional[:class:`User`]
        The related user object. Blank if no member intents
    member: Optional[:class:`Member`]
        The related member object, if requested with
        :meth:`ScheduledEvent.fetch_users`.
    user_id: int
        The id of the interested user


    .. warning::

        user or member may be ``None``, this may occur if you don't have
        :attr:`Intents.members` enabled.
    """

    __slots__: Tuple[str, ...] = (
        "_state",
        "event",
        "user",
        "member",
        "user_id",
    )

    def __init__(
        self,
        *,
        update: bool = True,
        event: ScheduledEvent,
        state: ConnectionState,
        data: Optional[ScheduledEventUserPayload] = None,
    ) -> None:
        self.event: ScheduledEvent = event
        self._state = state

        if update and data:
            self._update(data)

    def __repr__(self) -> str:
        attrs: List[Tuple[str, Any]] = [
            ("user_id", self.user_id),
            ("event", str(self.event)),
            ("user", str(self.user)),
            ("member", str(self.member)),
        ]
        joined = " ".join("%s=%r" % t for t in attrs)
        return f"<{self.__class__.__name__} {joined}>"

    @classmethod
    def from_id(
        cls, *, event: ScheduledEvent, state: ConnectionState, user_id: int
    ) -> ScheduledEventUser:
        obj = cls(event=event, state=state, update=False)
        obj.user_id = user_id
        obj.user = state.get_user(user_id)
        obj.member = event.guild.get_member(user_id)
        return obj

    def _update(self, data: ScheduledEventUserPayload) -> None:
        self.user: Optional[User] = self._state.store_user(data["user"])
        self.user_id: int = int(data["user"]["id"])
        if member := data.get("member"):
            if not self._state.member_cache_flags._empty:
                try:
                    self.member: Optional[Member] = self.event.guild.get_member(
                        member["id"]  # type: ignore # (handled below)
                    )
                except KeyError:
                    m = Member(data=member, guild=self.event.guild, state=self._state)  # type: ignore
                    self.member: Optional[Member] = m
            else:
                m = Member(data=member, guild=self.event.guild, state=self._state)  # type: ignore
                self.member: Optional[Member] = m
        else:
            self.member: Optional[Member] = None


class ScheduledEvent(Hashable):
    """Represents a Discord scheduled event

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two events are equal.

        .. describe:: x != y

            Checks if two events are not equal.

        .. describe:: hash(x)

            Returns the event's hash.

        .. describe:: str(x)

            Returns the event's name.

    Attributes
    ----------
    channel: Optional[:class:`abc.GuildChannel`]
        The channel the event will take place, if any.
    channel_id: Optional[:class:`int`]
        The channel id where the event will take place, if any.
    creator: Optional[:class:`User`]
        The user who created the event, if cached.
    description: :class:`str`
        The description of the event.
    end_time: :class:`datetime.datetime`
        The scheduled end time for the event, if set.
    guild: :class:`Guild`
        The guild the event will be in.
    id: :class:`int`
        The snowflake id for the event.
    metadata: Optional[:class:`EntityMetadata`]
        The metadata for the event, if any.
    name: :class:`str`
        The name of the event.
    privacy_level: :class:`ScheduledEventPrivacyLevel`
        The privacy level for the event.
    start_time: :class:`datetime.datetime`
        The scheduled start time for the event.
    user_count: :class:`int`
        An approximate count of the 'interested' users.
    image: :class:`Asset`
        The event cover image.
    """

    __slots__: Tuple[str, ...] = (
        "channel",
        "channel_id",
        "creator",
        "description",
        "end_time",
        "guild",
        "id",
        "metadata",
        "name",
        "privacy_level",
        "start_time",
        "user_count",
        "_state",
        "_users",
        "image",
    )

    def __init__(
        self, *, guild: Guild, state: ConnectionState, data: ScheduledEventPayload
    ) -> None:
        self.guild: Guild = guild
        self._state: ConnectionState = state
        self._update(data)

    def _update(self, data: ScheduledEventPayload) -> None:
        self.id: int = int(data["id"])
        if creator := data.get("creator"):
            self.creator: Optional[User] = self._state.store_user(creator)
        else:
            self.creator: Optional[User] = None
        self.name: str = data["name"]
        self.description: str = data.get("description", "")
        self.start_time: datetime = parse_time(data["scheduled_start_time"])
        self.end_time: Optional[datetime] = parse_time(data.get("scheduled_end_time"))
        self.privacy_level: ScheduledEventPrivacyLevel = ScheduledEventPrivacyLevel(
            data["privacy_level"]
        )
        self.metadata: EntityMetadata = EntityMetadata(**data.get("metadata", {}))
        self.user_count: int = data.get("user_count", 0)
        self.channel: Optional[GuildChannel] = self._state.get_channel(  # type: ignore # who knows
            int(data.get("channel_id") or 0)
        )
        channel_id = data.get("channel_id")
        self.channel_id: Optional[int] = int(channel_id) if channel_id else None
        self._users: Dict[int, ScheduledEventUser] = {}
        self._update_users(data.get("users", []))

        if image := data.get("image"):
            self.image: Optional[Asset] = Asset._from_scheduled_event_image(
                self._state, self.id, image
            )
        else:
            self.image: Optional[Asset] = None

    def _update_users(self, data: List[ScheduledEventUserPayload]) -> None:
        for user in data:
            self._users[int(user["user"]["id"])] = ScheduledEventUser(
                event=self, state=self._state, data=user
            )

    def _update_user(self, data: ScheduledEventUserPayload) -> ScheduledEventUser:
        if user := self._users.get(int(data["user"]["id"])):
            user._update(data)
        else:
            user = ScheduledEventUser(event=self, state=self._state, data=data)
            self._users[user.user_id] = user
            self.user_count += 1
        return user

    def _remove_user(self, user_id: int) -> None:
        if self._users.pop(user_id, None):
            self.user_count -= 1

    def __str__(self) -> str:
        return self.name

    def _add_user(self, user: ScheduledEventUser) -> None:
        self._users[user.user_id] = user
        self.user_count += 1

    def __repr__(self) -> str:
        attrs: List[Tuple[str, Any]] = [
            ("id", self.id),
            ("name", self.name),
            ("guild_id", self.guild.id),
            ("description", self.description),
            ("start_time", str(self.start_time)),
            ("end_time", str(self.end_time)),
        ]
        joined = " ".join("%s=%r" % t for t in attrs)
        return f"<{self.__class__.__name__} {joined}>"

    @property
    def location(self) -> Optional[str]:
        """Optional[:class:`str`]: The location of the event, if any."""
        return self.metadata.location

    @property
    def users(self) -> List[ScheduledEventUser]:
        """List[:class:`ScheduledEventUser`]: The users who are interested in the event.

        .. note::
            This may not be accurate or populated until
            :meth:`~.ScheduledEvent.fetch_users` is called
        """
        return list(self._users.values())

    async def delete(self) -> None:
        """|coro|

        Delete the scheduled event.
        """
        await self._state.http.delete_event(self.guild.id, self.id)

    async def edit(
        self,
        *,
        channel: GuildChannel = MISSING,
        metadata: EntityMetadata = MISSING,
        name: str = MISSING,
        privacy_level: ScheduledEventPrivacyLevel = MISSING,
        start_time: datetime = MISSING,
        end_time: datetime = MISSING,
        description: str = MISSING,
        type: ScheduledEventEntityType = MISSING,
        status: ScheduledEventStatus = MISSING,
        reason: Optional[str] = None,
        image: Optional[Union[bytes, Asset, Attachment, File]] = MISSING,
    ) -> ScheduledEvent:
        """|coro|

        Edit the scheduled event.

        .. versionchanged:: 2.1
            The ``image`` parameter now accepts :class:`File`, :class:`Attachment`, and :class:`Asset`.

        Parameters
        ----------
        channel: :class:`abc.GuildChannel`
            The new channel for the event.
        metadata: :class:`EntityMetadata`
            The new metadata for the event.
        name: :class:`str`
            The new name for the event.
        privacy_level: :class:`ScheduledEventPrivacyLevel`
            The new privacy level for the event.
        start_time: :class:`py:datetime.datetime`
            The new scheduled start time.
        end_time: :class:`py:datetime.datetime`
            The new scheduled end time.
        description: :class:`str`
            The new description for the event.
        type: :class:`ScheduledEventEntityType`
            The new type for the event.
        status: :class:`ScheduledEventStatus`
            The new status for the event.
        reason: Optional[:class:`str`]
            The reason for editing this scheduled event. Shows up in the audit logs.

            .. note::

                Only the following edits to an event's status are permitted:
                scheduled -> active ;
                active -> completed ;
                scheduled -> canceled
        image: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the cover image. Could be ``None`` to denote removal of the cover image.

        Returns
        -------
        :class:`ScheduledEvent`
            The updated event object.
        """
        payload: Dict[str, Any] = {}
        if channel is not MISSING:
            payload["channel_id"] = channel.id

        if metadata is not MISSING:
            payload["entity_metadata"] = metadata.__dict__

        if name is not MISSING:
            payload["name"] = name

        if privacy_level is not MISSING:
            payload["privacy_level"] = privacy_level.value

        if start_time is not MISSING:
            payload["scheduled_start_time"] = start_time.isoformat()

        if end_time is not MISSING:
            payload["scheduled_end_time"] = end_time.isoformat()

        if description is not MISSING:
            payload["description"] = description

        if type is not MISSING:
            payload["type"] = type.value

        if status is not MISSING:
            payload["status"] = status.value

        if image is not MISSING:
            payload["image"] = await _obj_to_base64_data(image)

        if not payload:
            return self

        data = await self._state.http.edit_event(self.guild.id, self.id, reason=reason, **payload)
        return ScheduledEvent(guild=self.guild, state=self._state, data=data)

    def get_user(self, user_id: int) -> Optional[ScheduledEventUser]:
        """Get a user that is interested.

        .. note::

            This may not be accurate or populated until
            :meth:`ScheduledEvent.fetch_users` is called.

        Parameters
        ----------
        user_id: :class:`int`
            The user id to get from cache.

        Returns
        -------
        Optional[:class:`ScheduledEventUser`]
            The user object, if found.
        """
        return self._users.get(user_id)

    def fetch_users(
        self,
        *,
        limit: int = 100,
        with_member: bool = False,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
    ) -> ScheduledEventUserIterator:
        """Fetch the users that are interested, returns an asyc iterator.

        Parameters
        ----------
        limit: :class:`int`
            Amount of users to fetch, by default 100
        with_member: :class:`bool`
            If the user objects should contain members too, by default False
        before: Optional[:class:`int`]
            A snowflake id to start with, useful for chunks of users, by default None
        after: Optional[:class:`int`]
            A snowflake id to end with, useful for chunks of usersby default None

        Yields
        -------
        :class:`ScheduledEventUser`
            A full event user object
        """
        return ScheduledEventUserIterator(
            self.guild, self, limit=limit, with_member=with_member, before=before, after=after
        )
