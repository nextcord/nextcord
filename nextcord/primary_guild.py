# SPDX-License-Identifier: MIT

__all__ = ("PrimaryGuild",)


from typing import Optional

from nextcord import Asset

from . import utils
from .state import ConnectionState
from .types.user import UserPrimaryGuild as UserPrimaryGuildPayload


class PrimaryGuild:
    """Represents a primary guild for a user.

    .. versionadded:: 3.2

    Attributes
    ----------
    identity_guild_id: Optional[:class:`int`]
        The ID of the primary guild.
    identity_enabled: Optional[:class:`bool`]
        Whether displaying the primary guild is enabled.
    tag: Optional[:class:`str`]
        The tag of the primary guild.
    badge: Optional[:class:`str`]
        The badge of the primary guild.
    """

    __slots__ = (
        "_state",
        "identity_guild_id",
        "identity_enabled",
        "tag",
        "_badge",
    )

    def __init__(self, *, data: UserPrimaryGuildPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.identity_guild_id: Optional[int] = utils.get_as_snowflake(data, "identity_guild_id")
        self.identity_enabled: Optional[bool] = data.get("identity_enabled")
        self.tag: Optional[str] = data.get("tag")
        self._badge: Optional[str] = data.get("badge")

    @property
    def badge(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the badge of the primary guild."""
        if self._badge is not None and self.identity_guild_id is not None:
            return Asset._from_primary_guild_badge(
                self._state, guild_id=self.identity_guild_id, badge_hash=self._badge
            )
        return None

    def __repr__(self) -> str:
        return (
            f"<PrimaryGuild identity_guild_id={self.identity_guild_id!r} "
            f"identity_enabled={self.identity_enabled!r} tag={self.tag!r} "
            f"badge={self.badge!r}>"
        )
