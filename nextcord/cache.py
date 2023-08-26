from time import time as now
from typing import Optional, Union

__set_item__ = dict.__setitem__
__get_item__ = dict.__getitem__
__get__ = dict.get
__pop__ = dict.pop


class SizedDict(dict):
    __slots__ = "maxsize"

    def __init__(self, maxsize: Optional[Union[float, int]] = None) -> None:
        if not maxsize:
            maxsize = float("inf")
        else:
            self.maxsize = maxsize

    def __getitem__(self, key):
        return __get_item__(self, key)

    def __setitem__(self, key, val) -> None:
        if len(self) >= self.maxsize:
            for item in self:
                del self[item]
                break
        __set_item__(self, key, val)


class BetterTTLCache(dict):
    __slots__ = ("maxsize", "ttl", "timelink", "working")

    def __init__(
        self, maxsize: Optional[int] = None, ttl: Optional[Union[int, float]] = None
    ) -> None:
        self.maxsize: float = float(maxsize) or float("inf")
        self.ttl: float = float(ttl)
        self.timelink = {}
        self.working: bool = False


    def __getitem__(self, key):
        self.__expire__()
        return __get_item__(self, key)

    def __setitem__(self, key, val) -> None:
        self.__expire__()
        if len(self) >= self.maxsize:
            for item in self:
                del self[item]
                break
        __set_item__(self, key, val)
        self.update_time(key)

    def __expire__(self) -> None:
        if not self.ttl or self.working:
            return

        self.working = True

        expiration = now() - self.ttl
        expired = []

        for key, time in self.timelink.items():
            if time <= expiration:
                expired.append(key)
            else:
                break
        for item in expired:
            del self[item]
            del self.timelink[item]

        self.working = False

    def get(self, key):
        self.__expire__()
        return __get__(self, key)

    def pop(self, key, default=None):
        __pop__(self.timelink, key, default)
        return __pop__(self, key, default)

    def get_with_update(self, key):
        self.__expire__()
        item = __get__(self, key)
        self.update_time(key)
        return item

    def set_with_persist_ttl(self, key, val) -> bool:
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
        # does not make sure the item exists in self, could result in memory leak if used improperly
        self.timelink[key] = self.timelink.pop(key, None) or now()
