# SPDX-License-Identifier: MIT

from enum import Enum
from time import time as now
from typing import Hashable, Optional, Union

class CacheMissing(Enum):
    MISSING = 0


_MISSING = CacheMissing.MISSING


class SizedDict(dict):
    """This represents a sized cache dictionary where objects over size limit
    will be removed upon adding a new object.

    .. note::
        This cache relies on the presumed order of dictionaries after Python 3.7
        This allows for the cache to be much faster and take 3x less memory than
        the TTL cache from the `collections` module.
    """

    __slots__ = ("maxsize",)

    def __init__(self, maxsize: Optional[Union[float, int]] = None) -> None:
        self.maxsize: Union[float, int] = maxsize or float("inf")

    def __setitem__(self, key, val) -> None:
        """Ensures doesn't exceed max size before adding new item."""
        if len(self) >= self.maxsize:
            for item in self:  # iter to delete first item
                del self[item]
                break
        super().__setitem__(key, val)


class BetterTTLCache(dict):
    """This represents a timed cache dictionary where objects past a certain age
    will be removed upon the next get (lazy ttl), and objects over size limit
    will be removed upon setting a new object.

    .. note::
        This cache relies on the presumed order of dictionaries after Python 3.7
        This allows for the cache to be much faster and take 3x less memory than
        the TTL cache from the `collections` module.
    """

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
        return super().__getitem__(key)

    def __setitem__(self, key, val) -> None:
        """
        Expires and ensures self max size is maintained before setting new item.
        """
        self.__expire__()
        if len(self) >= self.maxsize:
            for item in self:  # iter to delete first item
                del self[item]
                break
        super().__setitem__(key, val)
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
        return super().get(key, default)

    def pop(self, key, default=None):
        """Pop from timelink before returning pop from self"""
        self.timelink.pop(key, None)
        return super().pop(key, default)

    def get_with_update(self, key, default=None):
        """Get an item whilst updating the timelink for the item."""
        self.__expire__()
        item = super().get(key, _MISSING)
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
        super().__setitem__(key, val)
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
