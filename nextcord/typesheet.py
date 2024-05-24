from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .guild import AsyncGuild
from .interactions import Interaction
from .member import AsyncMember
from .message import AsyncMessage
from .types.guild import Guild as GuildPayload
from .types.interactions import Interaction as InteractionPayload
from .types.member import Member as MemberPayload
from .types.message import Message as MessagePayload
from .types.user import User as UserPayload
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

    async def create_guild(self, payload: GuildPayload) -> AsyncGuild:
        raise NotImplementedError

    async def create_interaction(self, payload: InteractionPayload) -> Interaction:
        raise NotImplementedError

    async def create_member(self, payload: MemberPayload, guild_id: int) -> AsyncMember:
        raise NotImplementedError

    async def create_message(self, payload: MessagePayload) -> AsyncMessage:
        raise NotImplementedError

    async def create_user(self, payload: UserPayload) -> AsyncUser:
        raise NotImplementedError


class DefaultTypeSheet(BaseTypeSheet):
    async def create_guild(self, payload: GuildPayload) -> AsyncGuild:
        return AsyncGuild.from_guild_payload(payload, bot=self._bot)

    async def create_interaction(self, payload: InteractionPayload) -> Interaction:
        return await Interaction.from_interaction_payload(payload, bot=self._bot)

    async def create_member(self, payload: MemberPayload, guild_id: int) -> AsyncMember:
        return AsyncMember.from_member_payload(payload, guild_id, bot=self._bot)

    async def create_message(self, payload: MessagePayload) -> AsyncMessage:
        return AsyncMessage.from_message_payload(payload, bot=self._bot)

    async def create_user(self, payload: UserPayload) -> AsyncUser:
        return AsyncUser.from_user_payload(payload, bot=self._bot)
