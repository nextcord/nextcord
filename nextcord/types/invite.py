# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired

from .appinfo import PartialAppInfo
from .channel import PartialChannel
from .guild import InviteGuild, _GuildPreviewUnique
from .snowflake import Snowflake
from .user import PartialUser

InviteTargetType = Literal[1, 2]


class _InviteMetadata(TypedDict, total=False):
    uses: int
    max_uses: int
    max_age: int
    temporary: bool
    created_at: str
    expires_at: Optional[str]
    revoked: Optional[bool]


class VanityInvite(_InviteMetadata):
    code: Optional[str]


class IncompleteInvite(_InviteMetadata):
    code: str
    channel: PartialChannel


class Invite(IncompleteInvite, total=False):
    guild: InviteGuild
    inviter: PartialUser
    target_user: PartialUser
    target_type: InviteTargetType
    target_application: PartialAppInfo


class InviteWithCounts(Invite, _GuildPreviewUnique):
    ...


class GatewayInviteCreate(TypedDict):
    channel_id: Snowflake
    code: str
    created_at: str
    max_age: int
    max_uses: int
    temporary: bool
    uses: bool
    guild_id: NotRequired[Snowflake]
    inviter: NotRequired[PartialUser]
    target_type: NotRequired[InviteTargetType]
    target_user: NotRequired[PartialUser]
    target_application: NotRequired[PartialAppInfo]


class GatewayInviteDelete(TypedDict):
    channel_id: Snowflake
    code: str
    guild_id: NotRequired[Snowflake]


GatewayInvite = Union[GatewayInviteCreate, GatewayInviteDelete]
