from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from .emoji import Emoji
from .enums import AnimationType
from .soundboard import PartialSoundboardSound, SoundboardSound

from .partial_emoji import PartialEmoji

if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState
    from .types.voice import VoiceChannelEffectSend as VoiceChannelEffectSendPayload


class VoiceChannelEffect:
    def __init__(self, data: VoiceChannelEffectSendPayload, state: ConnectionState):
        self._state: ConnectionState = state
        self._update(data)

    def _update(self, data: VoiceChannelEffectSendPayload) -> None:
        self.channel_id: int = int(data["channel_id"])
        self.guild_id: int = int(data["guild_id"])
        self.guild: Optional[Guild] = self._state._get_guild(self.guild_id)
        self.user_id: int = int(data["user_id"])

        self.emoji: Optional[Union[Emoji, PartialEmoji, str]] = None

        if partial_emoji := data.get("emoji", None):
            self.emoji = self._state._upgrade_partial_emoji(PartialEmoji.from_dict(partial_emoji))

        self.animation_type: Optional[AnimationType] = None

        if animation_type := data.get("animation_type", None):
            self.animation_type = AnimationType(animation_type)

        self.animation_id: Optional[int] = data.get("animation_id", None)

        self.sound_id: Optional[int] = int(data["sound_id"]) if "sound_id" in data else None
        self.sound_override_path: Optional[str] = data.get("sound_override_path", None)
        self.sound_volume: Optional[float] = data.get("sound_volume", None)

    @property
    def sound(self) -> Optional[Union[SoundboardSound, PartialSoundboardSound]]:
        if not self.sound_id:
            # TODO: what error to raise
            raise TypeError("This VoiceChannelEffect is not a sound effect")

        partial = PartialSoundboardSound(
            self.guild_id,
            self.emoji,
            self.sound_id,
            self.sound_override_path,
            self.sound_volume,
            self._state,
        )

        return self._state._upgrade_partial_soundboard_sound(partial)

    def __repr__(self) -> str:
        return f"<VoiceChannelEffect channel_id={self.channel_id} guild_id={self.guild_id} user_id={self.user_id} emoji={self.emoji} animation_type={self.animation_type} animation_id={self.animation_id} sound_id={self.sound_id} sound_override_path={self.sound_override_path} sound_volume={self.sound_volume}>"
