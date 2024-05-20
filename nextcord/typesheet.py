from __future__ import annotations

from typing import Dict, Iterable, Optional, TYPE_CHECKING

from .guild import AsyncGuild
from .member import Member
from .message import AsyncMessage

from .types.guild import Guild as GuildData
from .types.user import User as UserData
from .types.member import Member as MemberData
from .types.message import Message as MessageData

from .user import AsyncUser


if TYPE_CHECKING:
    from .client import Client


__all__ = (
    "BaseTypeSheet",
    "DefaultTypeSheet",
)


class BaseTypeSheet:
    _bot: Client

    def __init__(self, bot: Client, **kwargs):
        self._bot = bot

    async def create_guild(self, guild_data: GuildData) -> AsyncGuild:
        raise NotImplementedError

    async def create_member(self, member_data: MemberData) -> Member:
        raise NotImplementedError

    async def create_message(self, message_data: MessageData) -> AsyncMessage:
        raise NotImplementedError

    async def create_user(self, user_data: UserData) -> AsyncUser:
        raise NotImplementedError


class DefaultTypeSheet(BaseTypeSheet):
    async def create_guild(self, guild_data: GuildData) -> AsyncGuild:
        return AsyncGuild.from_guild_payload(guild_data, bot=self._bot)

    async def create_message(self, message_data: MessageData) -> AsyncMessage:
        return AsyncMessage.from_message_payload(message_data, bot=self._bot)

    async def create_user(self, user_data: UserData) -> AsyncUser:
        return AsyncUser.from_payload(user_data, bot=self._bot)
