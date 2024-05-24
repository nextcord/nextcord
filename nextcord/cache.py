from __future__ import annotations

from typing import Dict, Optional, Protocol, Tuple
from collections.abc import Sequence

from .types.guild import Guild as GuildData
from .types.member import Member as MemberData
from .types.message import Message as MessageData
from .types.user import User as UserData

__all__ = (
    "BaseCache",
    "MemoryCache",
    "NullCache",
)


class BaseCache(Protocol):
    """A non-functional, NotImplemented cache class that any Nextcord and user made cache should subclass."""
    def __init__(self, **kwargs) -> None:
        pass

    # Guilds
    async def add_guild(self, guild_data: GuildData) -> None:
        raise NotImplementedError

    async def get_guild(self, guild_id: int) -> Optional[GuildData]:
        raise NotImplementedError

    async def get_guild_ids(self) -> Sequence[int]:
        # TODO: Should this return an async interator?
        raise NotImplementedError

    # Members
    async def add_member(self, member_data: MemberData, guild_id: int) -> None:
        raise NotImplementedError

    async def remove_member(self, member_id: int, guild_id: int) -> bool:
        """Must return True if the member corresponding to the IDs was found and removed, False if not found."""
        raise NotImplementedError

    async def get_member(self, member_id: int, guild_id: int) -> Optional[MemberData]:
        raise NotImplementedError

    async def get_member_ids(self) -> Sequence[Tuple[int, int]]:
        """Must return a sequence of tuples containing the Member ID and Guild ID in that order."""
        raise NotImplementedError

    # Messages
    async def add_message(self, message_data: MessageData) -> None:
        raise NotImplementedError

    async def remove_message(self, message_id: int) -> bool:
        """Must return True if the message corresponding to the ID was found and removed, False if not found."""
        raise NotImplementedError

    async def get_message(self, message_id: int) -> Optional[MessageData]:
        raise NotImplementedError

    async def get_message_ids(self) -> Sequence[int]:
        # TODO: Should this return an async interator?
        raise NotImplementedError

    # Users
    async def add_user(self, user_data: UserData) -> None:
        raise NotImplementedError

    async def get_user(self, user_id: int) -> Optional[UserData]:
        raise NotImplementedError

    async def get_user_ids(self) -> Sequence[int]:
        # TODO: Should this return an async interator?
        raise NotImplementedError


class NullCache(BaseCache):
    pass


class MemoryCache(BaseCache):
    _guilds: Dict[int, GuildData]
    _members: Dict[Tuple[int, int], MemberData]
    """{(guild_id, member_id): MemberData}"""
    _messages: dict[int, MessageData]
    _users: Dict[int, UserData]

    # noinspection PyProtocol
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._guilds = {}
        self._members = {}
        self._messages = {}
        self._users = {}

    async def add_guild(self, guild_data: GuildData) -> None:
        self._guilds[int(guild_data["id"])] = guild_data

    async def get_guild(self, guild_id: int) -> Optional[GuildData]:
        return self._guilds.get(guild_id, None)

    async def get_guild_ids(self) -> Sequence[int]:
        return tuple(self._guilds.keys())

    async def add_member(self, member_data: MemberData, guild_id: int) -> None:
        self._members[(int(member_data["user"]["id"]), guild_id)] = member_data

    async def remove_member(self, member_id: int, guild_id: int) -> bool:
        return self._members.pop((member_id, guild_id), None) is not None

    async def get_member(self, member_id: int, guild_id: int) -> Optional[MemberData]:
        return self._members.get((member_id, guild_id), None)

    async def get_member_ids(self) -> Sequence[Tuple[int, int]]:
        return tuple(self._members.keys())

    async def add_message(self, message_data: MessageData) -> None:
        self._messages[int(message_data["id"])] = message_data

    async def remove_message(self, message_id: int) -> bool:
        return self._messages.pop(message_id, None) is not None

    async def get_message(self, message_id: int) -> Optional[MessageData]:
        return self._messages.get(message_id, None)

    async def get_message_ids(self) -> Sequence[int]:
        return tuple(self._messages.keys())

    async def add_user(self, user_data: UserData) -> None:
        self._users[int(user_data["id"])] = user_data

    async def get_user(self, user_id: int) -> Optional[UserData]:
        return self._users.get(user_id, None)

    async def get_user_ids(self) -> Sequence[int]:
        return tuple(self._users.keys())
