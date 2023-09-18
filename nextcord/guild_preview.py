# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .asset import Asset
from .emoji import Emoji
from .sticker import GuildSticker

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.guild import GuildFeature, GuildPreview as GuildPreviewPayload

__all__ = ("GuildPreview",)


class GuildPreview:
    """Represents a Discord guild preview.

    Attributes
    ----------
    id: :class:`int`
        The guild's ID
    name: :class:`str`
        The guild name.
    features: List[:class:`str`]
        The features the guild has access to.
    approximate_member_count: :class:`int`
        The approximate amount of members in the guild.
    approximate_presence_count: :class:`int`
        The approximate amount of presences for the guild.
    description: Optional[:class:`str`]
        The guild's description.
    emojis: List[:class:`Emoji`]
        All the emojis that the guild owns, if any.
    stickers: List[:class:`GuildSticker`]
        All the stickers that the guild owns, if any.

    .. versionadded :: 2.6
    """

    __slots__ = (
        "_state",
        "id",
        "name",
        "_icon",
        "_splash",
        "_discovery_splash",
        "emojis",
        "features",
        "approximate_member_count",
        "approximate_presence_count",
        "description",
        "stickers",
    )

    def __init__(self, *, data: GuildPreviewPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data["id"])
        self.name: str = data["name"]
        self._icon: Optional[str] = data.get("icon")
        self._splash: Optional[str] = data.get("splash")
        self._discovery_splash: Optional[str] = data.get("discovery_splash")
        self.features: List[GuildFeature] = data["features"]
        self.approximate_member_count: int = data["approximate_member_count"]
        self.approximate_presence_count: int = data["approximate_presence_count"]
        self.description: Optional[str] = data.get("description")
        self.emojis: List[Emoji] = [
            Emoji(guild=self, state=self._state, data=emoji) for emoji in data["emojis"]
        ]
        self.stickers: List[GuildSticker] = [
            GuildSticker(state=self._state, data=sticker) for sticker in data["stickers"]
        ]

    def __repr__(self) -> str:
        return f"<GuildPreview id={self.id!r} name={self.name!r}>"

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's icon asset, if avaliable."""
        if not self._icon:
            return None

        return Asset._from_guild_icon(self._state, self.id, self._icon)

    @property
    def splash(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's invite splash asset, if avaliable."""
        if not self._splash:
            return None

        return Asset._from_guild_image(self._state, self.id, self._splash, "splashes")

    @property
    def discovery_splash(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's discovery splash asset, if avaliable."""
        if not self._discovery_splash:
            return None

        return Asset._from_guild_image(
            self._state, self.id, self._discovery_splash, "discovery-splashes"
        )
