# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List, Optional, TypedDict

from typing_extensions import NotRequired

from .snowflake import Snowflake
from .team import Team
from .user import User


class BaseAppInfo(TypedDict):
    id: Snowflake
    name: str
    verify_key: str
    icon: Optional[str]
    summary: str
    description: str


class AppInfo(BaseAppInfo):
    rpc_origins: List[str]
    owner: User
    bot_public: bool
    bot_require_code_grant: bool
    team: NotRequired[Team]
    terms_of_service_url: NotRequired[str]
    privacy_policy_url: NotRequired[str]
    hook: NotRequired[bool]
    max_participants: NotRequired[int]


class PartialAppInfo(BaseAppInfo, total=False):
    rpc_origins: List[str]
    cover_image: str
    hook: bool
    terms_of_service_url: str
    privacy_policy_url: str
    max_participants: int
    flags: int
