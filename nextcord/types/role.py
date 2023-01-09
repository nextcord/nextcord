# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TypedDict

from typing_extensions import NotRequired

from .snowflake import Snowflake


class Role(TypedDict):
    id: Snowflake
    name: str
    color: int
    hoist: bool
    position: int
    permissions: str
    managed: bool
    mentionable: bool
    tags: NotRequired[RoleTags]
    unicode_emoji: NotRequired[str]
    icon: NotRequired[str]


class RoleTags(TypedDict, total=False):
    bot_id: Snowflake
    integration_id: Snowflake
    premium_subscriber: None
    subscription_listing_id: Snowflake
    available_for_purchase: None
    guild_connections: None
