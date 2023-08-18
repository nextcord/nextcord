from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union, cast

from .partial_emoji import PartialEmoji

from .asset import SoundAsset
from .emoji import Emoji
from .user import User

if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState
    from .types.soundboard import SoundboardSound as SoundboardSoundPayload


class PartialSoundboardSound:
    __slots__ = (
        "_state",
        "guild_id",
        "emoji",
        "id",
        "override_path",
        "volume",
    )

    def __init__(
        self,
        guild_id: int,
        emoji: Optional[Union[Emoji, PartialEmoji, str]],
        sound_id: int,
        sound_override_path: Optional[str],
        sound_volume: Optional[float],
        state: ConnectionState,
    ) -> None:
        self._state: ConnectionState = state

        self.guild_id: int = guild_id
        self.id: int = sound_id
        self.emoji: Optional[Union[Emoji, PartialEmoji, str]] = emoji
        self.override_path: Optional[str] = sound_override_path
        self.volume: Optional[float] = sound_volume

    @property
    def sound(self) -> SoundAsset:
        if self.override_path is not None:
            return SoundAsset._from_default_soundboard_sound(self._state, self.override_path)
        else:
            return SoundAsset._from_guild_soundboard_sound(self._state, self.id)

    def __repr__(self) -> str:
        return f"<PartialSoundboardSound id={self.id} emoji={self.emoji!r} guild_id={self.guild_id} override_path={self.override_path} volume={self.volume}>"


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
        "override_path",
    )

    def __init__(
        self, data: SoundboardSoundPayload, guild: Optional[Guild], state: ConnectionState
    ):
        self._state: ConnectionState = state
        self._update(data, guild, state)

    def _update(
        self, data: SoundboardSoundPayload, guild: Optional[Guild], state: ConnectionState
    ) -> None:
        self.name: str = data["name"]
        self.id: int = int(data["sound_id"])
        self.volume: float = data["volume"]

        self.emoji_id: Optional[int] = int(data["emoji_id"]) if data["emoji_id"] else None
        self.emoji_name: Optional[str] = data["emoji_name"]

        # guild_id is only None if the sound is global
        self.guild_id: Optional[int] = int(data["guild_id"]) if "guild_id" in data else None
        self.guild: Optional[Guild] = guild

        self.user_id: int = int(data["user_id"])
        self.user: Optional[User] = User(state=state, data=data["user"]) if "user" in data else None
        self.available: bool = data.get("available", True)

        self.override_path: Optional[str] = data.get("override_path", None)

    @property
    def emoji(self) -> Optional[Emoji]:
        return self._state.get_emoji(self.emoji_id)

    @property
    def sound(self) -> SoundAsset:
        if self.override_path is not None:
            return SoundAsset._from_default_soundboard_sound(self._state, self.override_path)
        else:
            return SoundAsset._from_guild_soundboard_sound(self._state, self.id)

    def __eq__(self, other: Any | SoundboardSound) -> bool:
        if not isinstance(other, SoundboardSound):
            raise TypeError(
                f"Expected type SoundboardSound, received {type(other).__name__!r} instead"
            )

        return other.id == self.id

    def __repr__(self) -> str:
        return f"<SoundboardSound id={self.id} name={self.name!r} volume={self.volume} emoji={self.emoji!r} user_id={self.user_id} available={self.available}>"
