# SPDX-License-Identifier: MIT

from enum import Enum, auto
from typing import Literal, TypeVar, Union

T = TypeVar("T")

class _MissingSentinel(Enum):
    MISSING = auto()

    def __bool__(self) -> Literal[False]: ...

MISSING: Literal[_MissingSentinel.MISSING] = _MissingSentinel.MISSING
MissingOr = Union[T, _MissingSentinel]
