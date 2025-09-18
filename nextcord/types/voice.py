# SPDX-License-Identifier: MIT

from typing import List, Literal, Optional, TypedDict

from typing_extensions import NotRequired

from .emoji import PartialEmoji
from .member import MemberWithUser
from .snowflake import Snowflake

SupportedModes = Literal["xsalsa20_poly1305_lite", "xsalsa20_poly1305_suffix", "xsalsa20_poly1305"]
AnimationTypes = Literal[0, 1]


class _VoiceState(TypedDict):
    user_id: Snowflake
    session_id: str
    deaf: bool
    mute: bool
    self_deaf: bool
    self_mute: bool
    self_video: bool
    suppress: bool
    member: NotRequired[MemberWithUser]
    self_stream: NotRequired[bool]


class GuildVoiceState(_VoiceState):
    channel_id: Snowflake


class VoiceState(_VoiceState, total=False):
    channel_id: Optional[Snowflake]
    guild_id: Snowflake


class VoiceRegion(TypedDict):
    id: str
    name: str
    vip: bool
    optimal: bool
    deprecated: bool
    custom: bool


class VoiceServerUpdate(TypedDict):
    token: str
    guild_id: Snowflake
    endpoint: Optional[str]


class VoiceIdentify(TypedDict):
    server_id: Snowflake
    user_id: Snowflake
    session_id: str
    token: str


class VoiceReady(TypedDict):
    ssrc: int
    ip: str
    port: int
    modes: List[SupportedModes]
    heartbeat_interval: int


class VoiceChannelEffectSend(TypedDict):
    channel_id: Snowflake
    guild_id: Snowflake
    user_id: Snowflake
    emoji: NotRequired[Optional[PartialEmoji]]
    animation_type: NotRequired[AnimationTypes]  # enums.AnimationType
    animation_id: NotRequired[int]

    # These only exist with soundboard sounds
    sound_id: NotRequired[Snowflake]
    sound_override_path: NotRequired[str]
    sound_volume: NotRequired[float]
