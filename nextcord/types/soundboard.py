from __future__ import annotations

from typing import TYPE_CHECKING, Optional, TypedDict

from typing_extensions import NotRequired

if TYPE_CHECKING:
    from .snowflake import Snowflake
    from .user import User


class SoundboardSound(TypedDict):
    name: str
    sound_id: Snowflake
    id: Optional[Snowflake]  # Should be the same as sound_id, might be None
    volume: float
    emoji_id: Optional[Snowflake]
    emoji_name: Optional[str]
    override_path: Optional[str]
    guild_id: NotRequired[Snowflake]
    user_id: Snowflake
    available: NotRequired[bool]
    user: NotRequired[User]
