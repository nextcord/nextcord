from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .guild import AsyncGuild
from .interactions import Interaction
from .member import Member
from .message import Message
from .user import User

if TYPE_CHECKING:
    from .client import Client
    from .types.activity import PartialPresenceUpdate as PresencePayload
    from .types.guild import Guild as GuildPayload
    from .types.interactions import Interaction as InteractionPayload
    from .types.member import Member as MemberPayload
    from .types.message import Message as MessagePayload
    from .types.user import User as UserPayload


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

    async def create_member(
        self, member_payload: MemberPayload, presence_payload: PresencePayload | None, guild_id: int
    ) -> Member:
        raise NotImplementedError

    async def create_message(self, payload: MessagePayload) -> Message:
        raise NotImplementedError

    async def create_user(self, payload: UserPayload) -> User:
        raise NotImplementedError


class DefaultTypeSheet(BaseTypeSheet):
    async def create_guild(self, payload: GuildPayload) -> AsyncGuild:
        return AsyncGuild.from_guild_payload(payload, bot=self._bot)

    async def create_interaction(self, payload: InteractionPayload) -> Interaction:
        return await Interaction.from_interaction_payload(payload, bot=self._bot)

    async def create_member(self, member_payload: MemberPayload, presence_payload: PresencePayload | None, guild_id: int) -> Member:
        return await Member.from_member_payload(member_payload, presence_payload, guild_id, bot=self._bot)

    async def create_message(self, payload: MessagePayload) -> Message:
        return await Message.from_message_payload(payload, bot=self._bot)

    async def create_user(self, payload: UserPayload) -> User:
        return await User.from_user_payload(payload, bot=self._bot)
