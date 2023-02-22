# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List, Optional, TypedDict

from .snowflake import Snowflake
from .user import PartialUser


class TeamMember(TypedDict):
    user: PartialUser
    membership_state: int
    permissions: List[str]
    team_id: Snowflake


class Team(TypedDict):
    id: Snowflake
    name: str
    owner_id: Snowflake
    members: List[TeamMember]
    icon: Optional[str]
