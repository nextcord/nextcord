
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .asset import Asset

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.guild import GuildPreview as GuildPreviewPayload


class GuildPreview:
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
        "stickers"
    )

    def __init__(self, *, data: GuildPreviewPayload, state: ConnectionState):
        self._state = state
        self.id = int(data["id"])
        self.name: str = data["name"]
        self._icon: Optional[str] = data.get("icon")
        self._splash: Optional[str] = data.get("splash")
        self._discovery_splash: Optional[str] = data.get("discovery_splash")
        self.emojis = data["emojis"]
        self.features: List[str] = data["features"]
        self.approximate_member_count: int = data["approximate_member_count"]
        self.approximate_presence_count: int = data["approximate_presence_count"]
        self.description: Optional[str] = data.get("description") or None
        self.stickers = data["stickers"]

    def __repr__(self) -> str:
        return f"<GuildPreview id={self.id!r} name={self.name!r}>"

    @property
    def icon(self) -> Optional[Asset]:
        if not self._icon:
            return None

        return Asset._from_guild_icon(self._state, self.id, self._icon)

    @property
    def splash(self) -> Optional[Asset]:
        if not self._splash:
            return None

        return Asset._from_guild_image(self._state, self.id, self._splash, "splashes")

    @property
    def discovery_splash(self) -> Optional[Asset]:
        if not self._discovery_splash:
            return None

        return Asset._from_guild_image(self._state, self.id, self._discovery_splash, "discovery-splashes")