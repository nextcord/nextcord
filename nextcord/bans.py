# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Optional

__all__ = ("BanEntry",)

if TYPE_CHECKING:
    from .user import User


class BanEntry(NamedTuple):
    reason: Optional[str]
    user: "User"
