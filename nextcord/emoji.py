# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterator, List, Optional, Tuple, Union

from .asset import Asset, AssetMixin
from .partial_emoji import PartialEmoji, _EmojiTag
from .user import User
from .utils import MISSING, SnowflakeList, snowflake_time

__all__ = ("Emoji",)

if TYPE_CHECKING:
    from datetime import datetime

    from .abc import Snowflake
    from .guild import Guild
    from .guild_preview import GuildPreview
    from .role import Role
    from .state import ConnectionState
    from .types.emoji import Emoji as EmojiPayload


class Emoji(_EmojiTag, AssetMixin):
    """Represents a custom emoji.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two emoji are the same.

        .. describe:: x != y

            Checks if two emoji are not the same.

        .. describe:: hash(x)

            Return the emoji's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(field, value)`` pairs. This allows this class
            to be used as an iterable in list/dict/etc constructions.

        .. describe:: str(x)

            Returns the emoji rendered for discord.

    Attributes
    ----------
    name: :class:`str`
        The name of the emoji.
    id: :class:`int`
        The emoji's ID.
    require_colons: :class:`bool`
        If colons are required to use this emoji in the client (:PJSalt: vs PJSalt).
    animated: :class:`bool`
        Whether an emoji is animated or not.
    managed: :class:`bool`
        If this emoji is managed by a Twitch integration.
    guild_id: Optional[:class:`int`]
        The guild ID the emoji belongs to, if applicable. This is ```None`` for application emojis.

        .. versionchanged:: 3.1
            This attribute is now optional to account for application emojis.
    available: :class:`bool`
        Whether the emoji is available for use.
    user: Optional[:class:`User`]
        The user that created the emoji. This can only be retrieved using :meth:`Guild.fetch_emoji` and
        having the :attr:`~Permissions.manage_emojis` permission.
    application_id: Optional[:class:`int`]
        The ID of the application that this emoji belongs to, if applicable. This is ```None`` for guild emojis.

        .. versionadded:: 3.1
    """

    __slots__: Tuple[str, ...] = (
        "require_colons",
        "animated",
        "managed",
        "id",
        "name",
        "_roles",
        "guild_id",
        "_state",
        "user",
        "available",
        "application_id",
    )

    def __init__(
        self,
        *,
        state: ConnectionState,
        data: EmojiPayload,
        guild: Union[Guild, GuildPreview, None] = None,
        application_id: Optional[int] = None,
    ) -> None:
        self.guild_id: int | None = guild.id if guild else None
        self.application_id: int | None = application_id
        self._state: ConnectionState = state
        self._from_data(data)

    def _from_data(self, emoji: EmojiPayload) -> None:
        self.require_colons: bool = emoji.get("require_colons", False)
        self.managed: bool = emoji.get("managed", False)
        self.id: int = int(emoji["id"])  # type: ignore
        self.name: str = emoji["name"]  # type: ignore
        self.animated: bool = emoji.get("animated", False)
        self.available: bool = emoji.get("available", True)
        self._roles: SnowflakeList = SnowflakeList(map(int, emoji.get("roles", [])))
        user = emoji.get("user")
        self.user: Optional[User] = User(state=self._state, data=user) if user else None

    def _to_partial(self) -> PartialEmoji:
        return PartialEmoji(name=self.name, animated=self.animated, id=self.id)

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        for attr in self.__slots__:
            if attr[0] != "_":
                value = getattr(self, attr, None)
                if value is not None:
                    yield (attr, value)

    def __str__(self) -> str:
        if self.animated:
            return f"<a:{self.name}:{self.id}>"
        return f"<:{self.name}:{self.id}>"

    def __repr__(self) -> str:
        return f"<Emoji id={self.id} name={self.name!r} animated={self.animated} managed={self.managed}>"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, _EmojiTag) and self.id == other.id

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return self.id >> 22

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the emoji's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def url(self) -> str:
        """:class:`str`: Returns the URL of the emoji."""
        fmt = "gif" if self.animated else "png"
        return f"{Asset.BASE}/emojis/{self.id}.{fmt}"

    @property
    def roles(self) -> List[Role]:
        """List[:class:`Role`]: A :class:`list` of roles that is allowed to use this emoji.

        If roles is empty, the emoji is unrestricted.
        """
        guild = self.guild
        if guild is None:
            return []

        return [role for role in guild.roles if self._roles.has(role.id)]

    @property
    def guild(self) -> Guild | None:
        """:class:`Guild`: The guild this emoji belongs to, if applicable."""
        return self._state._get_guild(self.guild_id)

    def is_usable(self) -> bool:
        """:class:`bool`: Whether the bot can use this emoji.

        .. versionadded:: 1.3

        .. versionchanged:: 3.1
            This now accounts for application emojis as well by comparing the application ID.
        """
        if not self.available:
            return False
        if self.is_application_emoji() and self.application_id != self._state.application_id:
            return False
        if self.guild is None:
            return False
        if not self._roles:
            return True

        emoji_roles, my_roles = self._roles, self.guild.me._roles
        return any(my_roles.has(role_id) for role_id in emoji_roles)

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the custom emoji.

        You must have :attr:`~Permissions.manage_emojis` permission to
        do this.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for deleting this emoji. Shows up on the audit log.

            This is only available when deleting an emoji in a guild.

        Raises
        ------
        Forbidden
            You are not allowed to delete emojis.
        HTTPException
            An error occurred deleting the emoji.
        ValueError
            The emoji does not belong to a guild or application.
        """
        if self.guild is None and self.application_id is None:
            raise ValueError("Cannot delete an emoji without a guild_id or application_id.")

        if self.application_id is not None:
            await self._state.http.delete_application_emoji(self.application_id, self.id)
            return

        if self.guild is not None:
            await self._state.http.delete_custom_emoji(self.guild.id, self.id, reason=reason)

    async def edit(
        self, *, name: str = MISSING, roles: List[Snowflake] = MISSING, reason: Optional[str] = None
    ) -> Emoji:
        r"""|coro|

        Edits the custom emoji.

        You must have :attr:`~Permissions.manage_emojis` permission to
        do this.

        .. versionchanged:: 2.0
            The newly updated emoji is returned.

        Parameters
        ----------
        name: :class:`str`
            The new emoji name.
        roles: Optional[List[:class:`~nextcord.abc.Snowflake`]]
            A list of roles that can use this emoji. An empty list can be passed to make it available to everyone.

            This is only available when editing an emoji in a guild.
        reason: Optional[:class:`str`]
            The reason for editing this emoji. Shows up on the audit log.

            This is only available when editing an emoji in a guild.

        Raises
        ------
        Forbidden
            You are not allowed to edit emojis.
        HTTPException
            An error occurred editing the emoji.
        ValueError
            The emoji does not belong to a guild or application

        Returns
        -------
        :class:`Emoji`
            The newly updated emoji.
        """
        if self.guild is None and self.application_id is None:
            raise ValueError("Cannot edit an emoji without a guild_id or application_id.")

        payload = {}
        if name is not MISSING:
            payload["name"] = name

        if self.application_id is not None:
            data = await self._state.http.edit_application_emoji(
                self.application_id, self.id, payload=payload
            )
            return Emoji(state=self._state, data=data, application_id=self.application_id)

        if roles is not MISSING:
            payload["roles"] = [role.id for role in roles]

        if self.guild is not None:
            data = await self._state.http.edit_custom_emoji(
                self.guild.id, self.id, payload=payload, reason=reason
            )
            return Emoji(guild=self.guild, data=data, state=self._state)

        raise ValueError("Cannot edit an emoji without a guild_id or application_id.")

    def is_application_emoji(self) -> bool:
        """:class:`bool`: Whether the emoji is an application emoji."""
        return self.application_id is not None

    def is_guild_emoji(self) -> bool:
        """:class:`bool`: Whether the emoji is a guild emoji."""
        return self.guild is not None
