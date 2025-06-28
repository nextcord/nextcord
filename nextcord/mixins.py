# SPDX-License-Identifier: MIT
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, AsyncIterator, List, Optional

if TYPE_CHECKING:
    from .abc import MessageableChannel, SnowflakeTime
    from .message import Message, MessagePin
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

        .. deprecated:: 3.2

            Use .fetch_pins instead.

            This is due to a change in the Discord API where there can now be more than 50
            pinned messages, and thus requires an async iterator to fetch all of them.

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

        warnings.warn(
            ".pins is deprecated, use .fetch_pins instead.",
            stacklevel=2,
            category=FutureWarning,
        )

        channel = await self._get_channel()
        state = self._state
        data = await state.http.pins_from(channel.id)
        return [state.create_message(channel=channel, data=m) for m in data]

    async def fetch_pins(
        self, limit: int = 50, before: Optional[SnowflakeTime] = None
    ) -> AsyncIterator[MessagePin]:
        """|asynciter|

        Returns an async iterator of all messages that are currently pinned in the channel.

        This requires :attr:`~nextcord.Permissions.read_message_history`, otherwise the result will be empty.

        .. versionadded:: 3.2

        .. note::

            Due to a limitation with the Discord API, the :class:`.MessagePin`
            objects returned by this method do not contain complete
            :attr:`.MessagePin.message.reactions` data.

        Parameters
        ----------
        limit: :class:`int`
            The maximum number of messages to retrieve. Defaults to 50.
        before: Optional[Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]]
            The pin before which to retrieve pinned messages.
        after: Optional[Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]]
            The pin after which to retrieve pinned messages.

        Raises
        ------
        ~nextcord.HTTPException
            Retrieving the pinned messages failed.

        Yields
        ------
        :class:`~nextcord.MessagePin`
            The messages that are currently pinned.
        """
        from .iterators import pin_iterator

        channel = await self._get_channel()
        async for pin in pin_iterator(channel, limit=limit, before=before):
            yield pin
