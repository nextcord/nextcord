# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List, Optional, TypedDict

from .snowflake import Snowflake


class WelcomeScreen(TypedDict):
    description: Optional[str]
    welcome_channels: List[WelcomeScreenChannel]


class WelcomeScreenChannel(TypedDict):
    channel_id: Snowflake
    description: str
    emoji_id: Optional[Snowflake]
    emoji_name: Optional[str]
