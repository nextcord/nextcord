from __future__ import annotations

from typing import Dict, Iterable, Optional
from collections.abc import Collection
from .types.guild import Guild as GuildData
from .types.message import Message as MessageData
from .types.user import User as UserData


__all__ = (
    "BaseCache",
    "MemoryCache",
    "NullCache",
)


class BaseCache:
    def __init__(self, **kwargs):
        pass

    """A non-functional, NotImplemented cache class that any Nextcord and user made cache should subclass."""

    # Guilds
    async def add_guild(self, guild_data: GuildData):
        raise NotImplementedError

    async def get_guild(self, guild_id: int) -> Optional[GuildData]:
        raise NotImplementedError

    async def get_guild_ids(self) -> Iterable[int]:
        # TODO: Should this return an async interator?
        raise NotImplementedError

    # Messages
    async def add_message(self, message_data: MessageData):
        raise NotImplementedError

    async def remove_message(self, message_id: int) -> bool:
        """Must return True if the message corresponding to the ID was found and removed, False if not found."""
        raise NotImplementedError

    async def get_message(self, message_id: int) -> Optional[MessageData]:
        raise NotImplementedError

    async def get_message_ids(self) -> Iterable[int]:
        # TODO: Should this return an async interator?
        raise NotImplementedError

    # Users
    async def add_user(self, user_data: UserData):
        raise NotImplementedError

    async def get_user(self, user_id: int) -> Optional[UserData]:
        raise NotImplementedError

    async def get_user_ids(self) -> Iterable[int]:
        # TODO: Should this return an async interator?
        raise NotImplementedError


class NullCache(BaseCache):
    pass


class MemoryCache(BaseCache):
    _guilds: Dict[int, GuildData]
    _messages: dict[int, MessageData]
    _users: Dict[int, UserData]

    def __init__(self, **kwargs):
        super().__init__()
        self._guilds = {}
        self._messages = {}
        self._users = {}

    async def add_guild(self, guild_data: GuildData):
        self._guilds[int(guild_data["id"])] = guild_data

    async def get_guild(self, guild_id: int) -> Optional[GuildData]:
        return self._guilds.get(guild_id, None)

    async def get_guild_ids(self) -> Iterable[int]:
        return tuple(self._guilds.keys())

    async def add_message(self, message_data: MessageData):
        self._messages[int(message_data["id"])] = message_data

    async def remove_message(self, message_id: int) -> bool:
        return True if self._messages.pop(message_id, None) is not None else False

    async def get_message(self, message_id: int) -> Optional[MessageData]:
        return self._messages.get(message_id, None)

    async def get_message_ids(self) -> Iterable[int]:
        return tuple(self._messages.keys())

    async def add_user(self, user_data: UserData):
        self._users[int(user_data["id"])] = user_data

    async def get_user(self, user_id: int) -> Optional[UserData]:
        return self._users.get(user_id, None)

    async def get_user_ids(self) -> Iterable[int]:
        return tuple(self._users.keys())





