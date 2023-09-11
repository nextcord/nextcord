# SPDX-License-Identifier: MIT

from enum import Enum
from time import time as now
from typing import Hashable, Optional, Union

# Avoiding super() call speeds up by 2x
# Cache speedup is very beneficial as it will be one of
# the hotest spots called
__set_item__ = dict.__setitem__
__get_item__ = dict.__getitem__
__get__ = dict.get
__pop__ = dict.pop


class CacheMissing(Enum):
    MISSING = 0


_MISSING = CacheMissing.MISSING


class SizedDict(dict):
    __slots__ = ("maxsize",)

    def __init__(self, maxsize: Optional[Union[float, int]] = None) -> None:
        self.maxsize: Union[float, int] = maxsize or float("inf")

    def __setitem__(self, key, val) -> None:
        """Ensures doesn't exceed max size before adding new item."""
        if len(self) >= self.maxsize:
            for item in self:  # iter to delete first item
                del self[item]
                break
        __set_item__(self, key, val)


class BetterTTLCache(dict):
    __slots__ = ("maxsize", "ttl", "timelink", "working")

    def __init__(
        self, maxsize: Optional[int] = None, ttl: Optional[Union[int, float]] = None
    ) -> None:
        self.maxsize: Union[int, float] = maxsize or float("inf")
        self.ttl: Optional[Union[int, float]] = ttl
        self.timelink: dict[Hashable, float] = {}
        self.working: bool = False

    def __getitem__(self, key):
        """Expires items before returning getitem."""
        self.__expire__()
        return __get_item__(self, key)

    def __setitem__(self, key, val) -> None:
        """
        Expires and ensures self max size is maintained before setting new item.
        """
        self.__expire__()
        if len(self) >= self.maxsize:
            for item in self:  # iter to delete first item
                del self[item]
                break
        __set_item__(self, key, val)
        self.update_time(key)

    def __expire__(self) -> None:
        """
        Takes care of expiring keys in the timelink that have passed their ttl lifespan.
        Uses a rolling motion for expiring, all items at the start of the timelink
        are assumed to be the earliest created items to avoid checking every item.
        Timelink order must be managed properly in order for expiration to work.
        """
        if not self.ttl or self.working:
            return

        self.working = True

        expiration = now() - self.ttl
        expired = []

        for key, time in self.timelink.items():
            if time > expiration:
                break
            expired.append(key)

        for item in expired:
            del self[item]
            del self.timelink[item]

        self.working = False

    def get(self, key, default=None):
        """Expire before returning from get."""
        self.__expire__()
        return __get__(self, key, default)

    def pop(self, key, default=None):
        """Pop from timelink before returning pop from self"""
        __pop__(self.timelink, key, None)
        return __pop__(self, key, default)

    def get_with_update(self, key, default=None):
        """Get an item whilst updating the timelink for the item."""
        self.__expire__()
        item = __get__(self, key, _MISSING)
        if item is not _MISSING:
            self.update_time(key)
            return item
        return default

    def set_with_persist_ttl(self, key, val) -> bool:
        """Setting a value without updating timelink if the key already exists."""
        self.__expire__()
        if len(self) >= self.maxsize:
            for item in self:
                del self[item]
                break
        __set_item__(self, key, val)
        if key not in self.timelink:
            self.timelink[key] = now()
            return True
        return False

    def update_time(self, key) -> None:
        """
        Update the timelink for a key.
        Creates the key anew if it does not exist in the timelink.
        Make sure the item exists in self, could result in memory leak if used improperly!
        """
        self.timelink[key] = self.timelink.pop(key, None) or now()
