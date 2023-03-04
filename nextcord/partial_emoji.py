# SPDX-License-Identifier: MIT

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from . import utils
from .asset import Asset, AssetMixin
from .errors import InvalidArgument

__all__ = ("PartialEmoji",)

if TYPE_CHECKING:
    from datetime import datetime

    from typing_extensions import Self

    from .state import ConnectionState
    from .types.emoji import DefaultReaction
    from .types.message import PartialEmoji as PartialEmojiPayload


class _EmojiTag:
    __slots__ = ()

    id: int

    def _to_partial(self) -> PartialEmoji:
        raise NotImplementedError


class PartialEmoji(_EmojiTag, AssetMixin):
    """Represents a "partial" emoji.

    This model will be given in two scenarios:

    - "Raw" data events such as :func:`on_raw_reaction_add`
    - Custom emoji that the bot cannot see from e.g. :attr:`Message.reactions`

    .. container:: operations

        .. describe:: x == y

            Checks if two emoji are the same.

        .. describe:: x != y

            Checks if two emoji are not the same.

        .. describe:: hash(x)

            Return the emoji's hash.

        .. describe:: str(x)

            Returns the emoji rendered for discord.

    Attributes
    ----------
    name: Optional[:class:`str`]
        The custom emoji name, if applicable, or the unicode codepoint
        of the non-custom emoji. This can be ``None`` if the emoji
        got deleted (e.g. removing a reaction with a deleted emoji).
    animated: :class:`bool`
        Whether the emoji is animated or not.
    id: Optional[:class:`int`]
        The ID of the custom emoji, if applicable.
    """

    __slots__ = ("animated", "name", "id", "_state")

    _CUSTOM_EMOJI_RE = re.compile(
        r"<?(?P<animated>a)?:?(?P<name>[A-Za-z0-9\_]+):(?P<id>[0-9]{13,20})>?"
    )

    if TYPE_CHECKING:
        id: Optional[int]

    def __init__(self, *, name: str, animated: bool = False, id: Optional[int] = None) -> None:
        self.animated = animated
        self.name = name
        self.id = id
        self._state: Optional[ConnectionState] = None

    @classmethod
    def from_dict(cls, data: Union[PartialEmojiPayload, Dict[str, Any]]) -> Self:
        return cls(
            animated=data.get("animated", False),
            id=utils.get_as_snowflake(data, "id"),
            name=data.get("name") or "",
        )

    @classmethod
    def from_default_reaction(cls, data: DefaultReaction) -> Self:
        return cls(
            id=utils.get_as_snowflake(data, "emoji_id"),
            name=data.get("emoji_name") or "",
        )

    @classmethod
    def from_str(cls, value: str) -> Self:
        """Converts a Discord string representation of an emoji to a :class:`PartialEmoji`.

        The formats accepted are:

        - ``a:name:id``
        - ``<a:name:id>``
        - ``name:id``
        - ``<:name:id>``

        If the format does not match then it is assumed to be a unicode emoji.

        .. versionadded:: 2.0

        Parameters
        ----------
        value: :class:`str`
            The string representation of an emoji.

        Returns
        -------
        :class:`PartialEmoji`
            The partial emoji from this string.
        """
        match = cls._CUSTOM_EMOJI_RE.match(value)
        if match is not None:
            groups = match.groupdict()
            animated = bool(groups["animated"])
            emoji_id = int(groups["id"])
            name = groups["name"]
            return cls(name=name, animated=animated, id=emoji_id)

        return cls(name=value, id=None, animated=False)

    def to_dict(self) -> Dict[str, Any]:
        o: Dict[str, Any] = {"name": self.name}
        if self.id:
            o["id"] = self.id
        if self.animated:
            o["animated"] = self.animated
        return o

    def _to_partial(self) -> PartialEmoji:
        return self

    @classmethod
    def with_state(
        cls,
        state: ConnectionState,
        *,
        name: str,
        animated: bool = False,
        id: Optional[int] = None,
    ) -> Self:
        self = cls(name=name, animated=animated, id=id)
        self._state = state
        return self

    def __str__(self) -> str:
        if self.id is None:
            return self.name
        if self.animated:
            return f"<a:{self.name}:{self.id}>"
        return f"<:{self.name}:{self.id}>"

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} animated={self.animated} name={self.name!r} id={self.id}>"
        )

    def __eq__(self, other: Any) -> bool:
        if self.is_unicode_emoji():
            return isinstance(other, PartialEmoji) and self.name == other.name

        if isinstance(other, _EmojiTag):
            return self.id == other.id
        return False

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.id, self.name))

    def is_custom_emoji(self) -> bool:
        """:class:`bool`: Checks if this is a custom non-Unicode emoji."""
        return self.id is not None

    def is_unicode_emoji(self) -> bool:
        """:class:`bool`: Checks if this is a Unicode emoji."""
        return self.id is None

    def _as_reaction(self) -> str:
        if self.id is None:
            return self.name
        return f"{self.name}:{self.id}"

    @property
    def created_at(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: Returns the emoji's creation time in UTC, or None if Unicode emoji.

        .. versionadded:: 1.6
        """
        if self.id is None:
            return None

        return utils.snowflake_time(self.id)

    @property
    def url(self) -> str:
        """:class:`str`: Returns the URL of the emoji, if it is custom.

        If this isn't a custom emoji then an empty string is returned
        """
        if self.is_unicode_emoji():
            return ""

        fmt = "gif" if self.animated else "png"
        return f"{Asset.BASE}/emojis/{self.id}.{fmt}"

    async def read(self) -> bytes:
        if self.is_unicode_emoji():
            raise InvalidArgument("PartialEmoji is not a custom emoji")

        return await super().read()
