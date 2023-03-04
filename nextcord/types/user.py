# SPDX-License-Identifier: MIT

from typing import Literal, Optional, TypedDict

from .snowflake import Snowflake


class PartialUser(TypedDict):
    id: Snowflake
    username: str
    discriminator: str
    avatar: Optional[str]


PremiumType = Literal[0, 1, 2]


class User(PartialUser, total=False):
    bot: bool
    system: bool
    mfa_enabled: bool
    local: str
    verified: bool
    email: Optional[str]
    flags: int
    premium_type: PremiumType
    public_flags: int
