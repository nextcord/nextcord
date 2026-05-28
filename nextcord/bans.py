# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, List, NamedTuple, Optional

from .object import Object

__all__ = ("BanEntry",)

if TYPE_CHECKING:
    from .user import User


class BanEntry(NamedTuple):
    reason: Optional[str]
    user: "User"


class BulkBan(NamedTuple):
    banned_users: List[Object]
    failed_users: List[Object]
