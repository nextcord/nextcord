# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List, Literal, Optional, TypedDict

from typing_extensions import NotRequired

from .snowflake import Snowflake
from .user import PartialUser

StatusType = Literal["idle", "dnd", "online", "offline"]


class PartialPresenceUpdate(TypedDict):
    user: PartialUser
    guild_id: Snowflake
    status: StatusType
    activities: List[Activity]
    client_status: ClientStatus


class ClientStatus(TypedDict, total=False):
    desktop: str
    mobile: str
    web: str


class ActivityTimestamps(TypedDict, total=False):
    start: int
    end: int


class ActivityParty(TypedDict, total=False):
    id: str
    size: List[int]


class ActivityAssets(TypedDict, total=False):
    large_image: str
    large_text: str
    small_image: str
    small_text: str


class ActivitySecrets(TypedDict, total=False):
    join: str
    spectate: str
    match: str


class ActivityEmoji(TypedDict):
    id: NotRequired[Snowflake]
    animated: NotRequired[bool]
    name: str


class ActivityButton(TypedDict):
    label: str
    url: str


ActivityType = Literal[0, 1, 2, 4, 5]


class SendableActivity(TypedDict):
    name: str
    type: ActivityType
    url: NotRequired[Optional[str]]


class _BaseActivity(SendableActivity):
    created_at: int


class Activity(_BaseActivity, total=False):
    state: Optional[str]
    details: Optional[str]
    timestamps: ActivityTimestamps
    assets: ActivityAssets
    party: ActivityParty
    application_id: Snowflake
    flags: int
    emoji: Optional[ActivityEmoji]
    secrets: ActivitySecrets
    session_id: Optional[str]
    instance: bool
    buttons: List[ActivityButton]
