from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .emoji import Emoji
from .guild import Guild
from .user import User

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.soundboard import SoundboardSound as SoundboardSoundPayload


class SoundboardSound:
    __slots__ = (
        "_state",
        "name",
        "id",
        "volume",
        "emoji_id",
        "emoji_name",
        "guild_id",
        "guild",
        "user_id",
        "user",
        "available",
    )

    def __init__(self, data: SoundboardSoundPayload, guild: Guild, state: ConnectionState) -> None:
        self._state: ConnectionState = state

        self._update(data, guild, state)

    def _update(self, data: SoundboardSoundPayload, guild: Guild, state: ConnectionState) -> None:
        self.name: str = data["name"]
        self.id: int = int(data["sound_id"])
        self.volume: float = data["volume"]

        self.emoji_id: Optional[int] = int(data["emoji_id"]) if data["emoji_id"] else None
        self.emoji_name: Optional[str] = data["emoji_name"]

        # guild_id is only None if the sound is global
        self.guild_id: Optional[int] = int(data["guild_id"]) if "guild_id" in data else None
        self.guild = guild

        self.user_id: int = int(data["user_id"])
        self.user: Optional[User] = User(state=state, data=data["user"]) if "user" in data else None
        self.available: bool = data.get("available", True)

    @property
    def emoji(self) -> Optional[Emoji]:
        return self._state.get_emoji(self.emoji_id)

    @property
    def sound(self) -> Any:
        # TODO
        raise NotImplementedError
