# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator, List, Optional, Union

from .colour import Colour
from .enums import ReactionType
from .iterators import reaction_iterator
from .utils import cached_slot_property

__all__ = ("Reaction",)

if TYPE_CHECKING:
    from .abc import Snowflake
    from .emoji import Emoji
    from .member import Member
    from .message import Message
    from .partial_emoji import PartialEmoji
    from .types.message import (
        Reaction as ReactionPayload,
        ReactionCountDetails as ReactionCountDetailsPayload,
    )
    from .user import User


class ReactionCountDetails:
    """Represents a reaction's count details.

    .. versionadded:: 3.2

    Attributes
    ----------
    burst: :class:`int`
        The amount of burst reactions.
    normal: :class:`int`
        The amount of normal reactions.
    """

    __slots__ = ("burst", "normal")

    def __init__(self, data: ReactionCountDetailsPayload) -> None:
        self.burst: int = data["burst"]
        self.normal: int = data["normal"]


class Reaction:
    """Represents a reaction to a message.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two reactions are equal. This works by checking if the emoji
            is the same. So two messages with the same reaction will be considered
            "equal".

        .. describe:: x != y

            Checks if two reactions are not equal.

        .. describe:: hash(x)

            Returns the reaction's hash.

        .. describe:: str(x)

            Returns the string form of the reaction's emoji.

    Attributes
    ----------
    emoji: Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`]
        The reaction emoji. May be a custom emoji, or a unicode emoji.
    count: :class:`int`
        Number of times this reaction was made
    count_details: :class:`ReactionCountDetails`
        The count details for this reaction.

        .. versionadded:: 3.2
    me: :class:`bool`
        If the user sent this reaction.
    me_burst: :class:`bool`
        If the user sent a burst reaction.

        .. versionadded:: 3.2
    message: :class:`Message`
        Message this reaction is for.
    """

    __slots__ = (
        "_burst_colours",
        "_cs_burst_colours",
        "count",
        "count_details",
        "emoji",
        "me",
        "me_burst",
        "message",
    )

    def __init__(
        self,
        *,
        message: Message,
        data: ReactionPayload,
        emoji: Optional[Union[PartialEmoji, Emoji, str]] = None,
    ) -> None:
        self.message: Message = message
        self.emoji: Union[PartialEmoji, Emoji, str] = emoji or message._state.get_reaction_emoji(
            data["emoji"]
        )
        self.count: int = data.get("count", 1)
        self.me: bool = data.get("me")
        self.me_burst: bool = data.get("me_burst")
        self.count_details: ReactionCountDetails = ReactionCountDetails(data=data["count_details"])

        self._burst_colours: List[str] = data.get("burst_colors")

    # TODO: typeguard
    def is_custom_emoji(self) -> bool:
        """:class:`bool`: If this is a custom emoji."""
        return not isinstance(self.emoji, str)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and other.emoji == self.emoji

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return other.emoji != self.emoji
        return True

    def __hash__(self) -> int:
        return hash(self.emoji)

    def __str__(self) -> str:
        return str(self.emoji)

    def __repr__(self) -> str:
        return f"<Reaction emoji={self.emoji!r} me={self.me} count={self.count}>"

    @cached_slot_property("_cs_burst_colours")
    def burst_colours(self) -> List[Colour]:
        """List[:class:`Colour`]: The HEX colours used for a burst reaction.

        .. versionadded:: 3.2
        """
        return [Colour(value=int(c.strip("#"), base=16)) for c in self._burst_colours]

    @property
    def burst_colors(self) -> List[Colour]:
        """List[:class:`Colour`]: An alias of :attr:`.burst_colours`.

        .. versionadded:: 3.2
        """
        return self.burst_colours

    async def remove(self, user: Snowflake) -> None:
        """|coro|

        Remove the reaction by the provided :class:`User` from the message.

        If the reaction is not your own (i.e. ``user`` parameter is not you) then
        the :attr:`~Permissions.manage_messages` permission is needed.

        The ``user`` parameter must represent a user or member and meet
        the :class:`abc.Snowflake` abc.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
             The user or member from which to remove the reaction.

        Raises
        ------
        HTTPException
            Removing the reaction failed.
        Forbidden
            You do not have the proper permissions to remove the reaction.
        NotFound
            The user you specified, or the reaction's message was not found.
        """

        await self.message.remove_reaction(self.emoji, user)

    async def clear(self) -> None:
        """|coro|

        Clears this reaction from the message.

        You need the :attr:`~Permissions.manage_messages` permission to use this.

        .. versionadded:: 1.3

        Raises
        ------
        HTTPException
            Clearing the reaction failed.
        Forbidden
            You do not have the proper permissions to clear the reaction.
        NotFound
            The emoji you specified was not found.
        InvalidArgument
            The emoji parameter is invalid.
        """
        await self.message.clear_reaction(self.emoji)

    def users(
        self,
        *,
        limit: Optional[int] = None,
        after: Optional[Snowflake] = None,
        type: ReactionType = ReactionType.normal,
    ) -> AsyncIterator[User | Member]:
        """Returns an :class:`AsyncIterator` representing the users that have reacted to the message.

        The ``after`` parameter must represent a member
        and meet the :class:`abc.Snowflake` abc.

        Examples
        --------

        Usage ::

            # I do not actually recommend doing this.
            async for user in reaction.users():
                await channel.send(f'{user} has reacted with {reaction.emoji}!')

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The maximum number of results to return.
            If not provided, returns all the users who
            reacted to the message.
        after: Optional[:class:`abc.Snowflake`]
            For pagination, reactions are sorted by member.
        type: :class:`ReactionType`
            The type of reactions to return.
            Defaults to `~ReactionType.normal` if not provided.

            .. versionadded:: 3.2

        Raises
        ------
        HTTPException
            Getting the users for the reaction failed.

        Yields
        ------
        Union[:class:`User`, :class:`Member`]
            The member (if retrievable) or the user that has reacted
            to this message. The case where it can be a :class:`Member` is
            in a guild message context. Sometimes it can be a :class:`User`
            if the member has left the guild.
        """

        if not isinstance(self.emoji, str):
            emoji = f"{self.emoji.name}:{self.emoji.id}"
        else:
            emoji = self.emoji

        if limit is None:
            limit = self.count

        return reaction_iterator(self.message, emoji, limit, after, type)
