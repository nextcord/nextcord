"""
    Copyright 2021 Ext-Creators

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

"""An experiment that allows `x in y` syntax for various nextcord objects.

Example:
```py
channel in guild

member in channel

member in role
```
"""

import nextcord
from nextcord.channel import CategoryChannel, DMChannel, TextChannel

if nextcord.version_info < (1, 7, 0):
    from nextcord.channel import VoiceChannel as VocalGuildChannel
else:
    from nextcord.channel import VocalGuildChannel

from nextcord.guild import Guild
from nextcord.member import Member
from nextcord.message import Message
from nextcord.role import Role
from nextcord.user import User, BaseUser


def _Guild__contains__(self, item):
    if hasattr(item, "guild"):
        return item.guild == self

    if isinstance(item, BaseUser):
        return item.id in self._members

    return False


Guild.__contains__ = _Guild__contains__


def _Role__contains__(self, item):
    if isinstance(item, User):
        item = self.guild._members.get(item.id)

    if isinstance(item, Member):
        return item._roles.has(self.id)

    return False


Role.__contains__ = _Role__contains__


def _TextChannel__contains__(self, item):
    if hasattr(item, "channel"):
        return item.channel == self

    if isinstance(item, User):
        item = self.guild._members.get(item.id)

    if isinstance(item, Member):
        return self.permissions_for(item).read_messages

    return False


TextChannel.__contains__ = _TextChannel__contains__


def _VocalGuildChannel__contains__(self, item):
    if isinstance(item, BaseUser) and item.id in self.voice_states:
        return True

    return False


VocalGuildChannel.__contains__ = _VocalGuildChannel__contains__


def _CategoryChannel__contains__(self, item):
    if hasattr(item, "category"):
        return item.category == self

    return False


CategoryChannel.__contains__ = _CategoryChannel__contains__


def _DMChannel__contains__(self, item):
    if hasattr(item, "channel"):
        return item.channel == self

    if isinstance(item, BaseUser):
        return item in (self.me, self.recipient)

    return False


DMChannel.__contains__ = _DMChannel__contains__
