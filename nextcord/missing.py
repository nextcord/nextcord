# SPDX-License-Identifier: MIT

from typing import Any, TypeVar, Union

T = TypeVar("T")

__all__ = ("MISSING", "MissingOr")


class _MissingSentinel:
    def __eq__(self, other: Any) -> bool:
        return self is other

    def __hash__(self):
        return id(self)

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "..."


MISSING = _MissingSentinel()


def __new__(cls: type) -> _MissingSentinel:
    return MISSING


_MissingSentinel.__new__ = __new__
del __new__


MissingOr = Union[T, _MissingSentinel]
