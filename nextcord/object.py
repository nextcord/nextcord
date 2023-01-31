# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, SupportsInt, Union

from . import utils
from .mixins import Hashable

if TYPE_CHECKING:
    import datetime

    SupportsIntCast = Union[SupportsInt, str, bytes, bytearray]

__all__ = ("Object",)


class Object(Hashable):
    """Represents a generic Discord object.

    The purpose of this class is to allow you to create 'miniature'
    versions of data classes if you want to pass in just an ID. Most functions
    that take in a specific data class with an ID can also take in this class
    as a substitute instead. Note that even though this is the case, not all
    objects (if any) actually inherit from this class.

    There are also some cases where some websocket events are received
    in :dpyissue:`strange order <21>` and when such events happened you would
    receive this class rather than the actual data class. These cases are
    extremely rare.

    .. container:: operations

        .. describe:: x == y

            Checks if two objects are equal.

        .. describe:: x != y

            Checks if two objects are not equal.

        .. describe:: hash(x)

            Returns the object's hash.

    Attributes
    ----------
    id: :class:`int`
        The ID of the object.
    """

    def __init__(self, id: SupportsIntCast) -> None:
        try:
            id = int(id)
        except ValueError:
            raise TypeError(
                f"id parameter must be convertable to int not {id.__class__!r}"
            ) from None
        else:
            self.id = id

    def __repr__(self) -> str:
        return f"<Object id={self.id!r}>"

    def __int__(self) -> int:
        return self.id

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the snowflake's creation time in UTC."""
        return utils.snowflake_time(self.id)
