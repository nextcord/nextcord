# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .abc import MessageableChannel
    from .message import Message
    from .state import ConnectionState

__all__ = (
    "EqualityComparable",
    "Hashable",
    "PinsMixin",
)


class EqualityComparable:
    __slots__ = ()

    id: int

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.id == self.id

    def __ne__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return other.id != self.id
        return True


class Hashable(EqualityComparable):
    __slots__ = ()

    def __hash__(self) -> int:
        return self.id >> 22


class PinsMixin:
    __slots__ = ()
    _state: ConnectionState

    async def _get_channel(self) -> MessageableChannel:
        raise NotImplementedError

    async def pins(self) -> List[Message]:
        """|coro|

        Retrieves all messages that are currently pinned in the channel.

        .. note::

            Due to a limitation with the Discord API, the :class:`.Message`
            objects returned by this method do not contain complete
            :attr:`.Message.reactions` data.

        Raises
        ------
        ~nextcord.HTTPException
            Retrieving the pinned messages failed.

        Returns
        -------
        List[:class:`~nextcord.Message`]
            The messages that are currently pinned.
        """

        channel = await self._get_channel()
        state = self._state
        data = await state.http.pins_from(channel.id)
        return [state.create_message(channel=channel, data=m) for m in data]
