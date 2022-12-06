# SPDX-License-Identifier: MIT

from typing import List, Optional, TypedDict

from typing_extensions import NotRequired

from .activity import Activity
from .snowflake import Snowflake
from .user import User


class WidgetChannel(TypedDict):
    id: Snowflake
    name: str
    position: int


class WidgetMember(User, total=False):
    nick: str
    game: Activity
    status: str
    avatar_url: str
    deaf: bool
    self_deaf: bool
    mute: bool
    self_mute: bool
    suppress: bool


class Widget(TypedDict):
    id: Snowflake
    name: str
    instant_invite: str
    channels: NotRequired[List[WidgetChannel]]
    members: NotRequired[List[WidgetMember]]
    presence_count: NotRequired[int]


class WidgetSettings(TypedDict):
    enabled: bool
    channel_id: Optional[Snowflake]
