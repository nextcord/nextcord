from __future__ import annotations

from typing import Dict, Optional, Protocol, Tuple, TYPE_CHECKING
from collections.abc import Sequence


if TYPE_CHECKING:
    from .types.guild import Guild as GuildPayload
    from .types.member import Member as MemberPayload
    from .types.message import Message as MessagePayload
    from .types.activity import PartialPresenceUpdate as PresencePayload
    from .types.user import User as UserPayload

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
    async def add_guild(self, guild_data: GuildPayload) -> None:
        raise NotImplementedError

    async def get_guild(self, guild_id: int) -> Optional[GuildPayload]:
        raise NotImplementedError

    async def get_guild_ids(self) -> Sequence[int]:
        # TODO: Should this return an async interator?
        raise NotImplementedError

    # Members
    async def add_member(self, member_data: MemberPayload, guild_id: int) -> None:
        raise NotImplementedError

    async def remove_member(self, member_id: int, guild_id: int) -> bool:
        """Must return True if the member corresponding to the IDs was found and removed, False if not found."""
        raise NotImplementedError

    async def get_member(self, member_id: int, guild_id: int) -> Optional[MemberPayload]:
        raise NotImplementedError

    async def get_member_ids(self) -> Sequence[Tuple[int, int]]:
        """Must return a sequence of tuples containing the Member ID and Guild ID in that order."""
        raise NotImplementedError

    # Messages
    async def add_message(self, message_data: MessagePayload) -> None:
        raise NotImplementedError

    async def remove_message(self, message_id: int) -> bool:
        """Must return True if the message corresponding to the ID was found and removed, False if not found."""
        raise NotImplementedError

    async def get_message(self, message_id: int) -> Optional[MessagePayload]:
        raise NotImplementedError

    async def get_message_ids(self) -> Sequence[int]:
        # TODO: Should this return an async interator?
        raise NotImplementedError

    # Presences
    async def add_presence(self, payload: PresencePayload) -> None:
        raise NotImplementedError

    async def remove_presence(self, member_id: int, guild_id: int) -> bool:
        raise NotImplementedError

    async def get_presence(self, member_id: int, guild_id: int) -> PresencePayload | None:
        raise NotImplementedError

    # Users
    async def add_user(self, user_data: UserPayload) -> None:
        raise NotImplementedError

    async def get_user(self, user_id: int) -> Optional[UserPayload]:
        raise NotImplementedError

    async def get_user_ids(self) -> Sequence[int]:
        # TODO: Should this return an async interator?
        raise NotImplementedError


class NullCache(BaseCache):
    pass


class MemoryCache(BaseCache):
    _guilds: Dict[int, GuildPayload]
    _members: Dict[Tuple[int, int], MemberPayload]
    """{(member_id, guild_id): MemberData}"""
    _messages: dict[int, MessagePayload]
    _presences: dict[tuple[int, int], PresencePayload]
    """{(member_id, guild_id): PresencePayload}"""
    _users: Dict[int, UserPayload]

    # noinspection PyProtocol
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._guilds = {}
        self._members = {}
        self._messages = {}
        self._presences = {}
        self._users = {}

    async def add_guild(self, guild_data: GuildPayload) -> None:
        self._guilds[int(guild_data["id"])] = guild_data

    async def get_guild(self, guild_id: int) -> Optional[GuildPayload]:
        return self._guilds.get(guild_id, None)

    async def get_guild_ids(self) -> Sequence[int]:
        return tuple(self._guilds.keys())

    async def add_member(self, member_data: MemberPayload, guild_id: int) -> None:
        self._members[(int(member_data["user"]["id"]), guild_id)] = member_data

    async def remove_member(self, member_id: int, guild_id: int) -> bool:
        return self._members.pop((member_id, guild_id), None) is not None

    async def get_member(self, member_id: int, guild_id: int) -> Optional[MemberPayload]:
        return self._members.get((member_id, guild_id), None)

    async def get_member_ids(self) -> Sequence[Tuple[int, int]]:
        return tuple(self._members.keys())

    async def add_message(self, message_data: MessagePayload) -> None:
        self._messages[int(message_data["id"])] = message_data

    async def remove_message(self, message_id: int) -> bool:
        return self._messages.pop(message_id, None) is not None

    async def get_message(self, message_id: int) -> Optional[MessagePayload]:
        return self._messages.get(message_id, None)

    async def get_message_ids(self) -> Sequence[int]:
        return tuple(self._messages.keys())

    async def add_presence(self, payload: PresencePayload) -> None:
        self._presences[(int(payload["user"]["id"]), int(payload["guild_id"]))] = payload

    async def remove_presence(self, member_id: int, guild_id: int) -> bool:
        return self._presences.pop((member_id, guild_id), None) is not None

    async def get_presence(self, member_id: int, guild_id: int) -> PresencePayload | None:
        return self._presences.get((member_id, guild_id))

    async def add_user(self, user_data: UserPayload) -> None:
        self._users[int(user_data["id"])] = user_data

    async def get_user(self, user_id: int) -> Optional[UserPayload]:
        return self._users.get(user_id, None)

    async def get_user_ids(self) -> Sequence[int]:
        return tuple(self._users.keys())
