from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .guild import AsyncGuild
from .member import AsyncMember
from .message import AsyncMessage
from .types.guild import Guild as GuildData
from .types.member import Member as MemberData
from .types.message import Message as MessageData
from .types.user import User as UserData
from .user import AsyncUser

if TYPE_CHECKING:
    from .client import Client


__all__ = (
    "BaseTypeSheet",
    "DefaultTypeSheet",
)


class BaseTypeSheet(Protocol):
    _bot: Client

    def __init__(self, bot: Client, **kwargs) -> None:
        self._bot = bot

    async def create_guild(self, guild_data: GuildData) -> AsyncGuild:
        raise NotImplementedError

    async def create_member(self, member_data: MemberData, guild_id: int) -> AsyncMember:
        raise NotImplementedError

    async def create_message(self, message_data: MessageData) -> AsyncMessage:
        raise NotImplementedError

    async def create_user(self, user_data: UserData) -> AsyncUser:
        raise NotImplementedError


class DefaultTypeSheet(BaseTypeSheet):
    async def create_guild(self, guild_data: GuildData) -> AsyncGuild:
        return AsyncGuild.from_guild_payload(guild_data, bot=self._bot)

    async def create_member(self, member_data: MemberData, guild_id: int) -> AsyncMember:
        return AsyncMember.from_member_payload(member_data, guild_id, bot=self._bot)

    async def create_message(self, message_data: MessageData) -> AsyncMessage:
        return AsyncMessage.from_message_payload(message_data, bot=self._bot)

    async def create_user(self, user_data: UserData) -> AsyncUser:
        return AsyncUser.from_payload(user_data, bot=self._bot)
