from typing import Pattern
from .constants import EmojiType
import re

import nextcord


class Position:
    __slots__ = ('number', 'bucket')

    def __init__(self, number: int, *, bucket: int = 1):
        self.bucket = bucket
        self.number = number

    def __lt__(self, other):
        if not isinstance(other, Position) or not isinstance(self, Position):
            return NotImplemented

        return (self.bucket, self.number) < (other.bucket, other.number)

    def __eq__(self, other):
        return isinstance(other, Position) and other.bucket == self.bucket and other.number == self.number

    def __le__(self, other):
        r = Position.__lt__(other, self)
        if r is NotImplemented:
            return NotImplemented
        return not r

    def __gt__(self, other):
        return Position.__lt__(other, self)

    def __ge__(self, other):
        r = Position.__lt__(self, other)
        if r is NotImplemented:
            return NotImplemented
        return not r

    def __repr__(self):
        return '<{0.__class__.__name__}: {0.number}>'.format(self)


class Last(Position):
    __slots__ = ()

    def __init__(self, number=0):
        super().__init__(number, bucket=2)


class First(Position):
    __slots__ = ()

    def __init__(self, number=0):
        super().__init__(number, bucket=0)


_custom_emoji = re.compile(
    r'<?(?P<animated>a)?:?(?P<name>[A-Za-z0-9\_]+):(?P<id>[0-9]{13,20})>?')


def _cast_emoji(obj: EmojiType, *, _custom_emoji: Pattern[str]=_custom_emoji):
    if isinstance(obj, nextcord.PartialEmoji):
        return obj

    obj = str(obj)
    match = _custom_emoji.match(obj)
    if match is not None:
        groups = match.groupdict()
        animated = bool(groups['animated'])
        emoji_id = int(groups['id'])
        name = groups['name']
        return nextcord.PartialEmoji(name=name, animated=animated, id=emoji_id)
    return nextcord.PartialEmoji(name=obj, id=None, animated=False)
