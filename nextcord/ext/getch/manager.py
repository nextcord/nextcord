"""
    Copyright (c) 2020 Ext-Creators

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

from nextcord.channel import _channel_factory
from nextcord.enums import ChannelType
from nextcord.object import Object
from nextcord.errors import InvalidData

class GetchManager:
    def __init__(self, *, bot):
        self.bot = bot
        self.http = bot.http
        self._connection = bot._connection
    
    def fetch_guild(self, id: int):
        return self.bot.fetch_guild(id)
    
    def get_guild(self, id: int):
        return self.bot.get_guild(id)
    
    async def fetch_channel(self, id: int, *, guild=None):
        data = await self.http.get_channel(id)

        factory, ch_type = _channel_factory(data['type'])
        if factory is None:
            raise InvalidData('Unknown channel type {type} for channel ID {id}.'.format_map(data))

        if ch_type in (ChannelType.group, ChannelType.private):
            channel = factory(me=self.user, data=data, state=self._connection)
        else:
            guild_id = int(data['guild_id'])
            guild = guild or self.get_guild(guild_id) or Object(id=guild_id)
            channel = factory(guild=guild, state=self._connection, data=data)

        return channel
    
    def get_channel(self, id: int):
        return self.bot.get_channel(id)
    
    async def fetch_message(self, id: int, *, channel=None):
        data = await self.http.get_message(channel.id, id)
        return self._connection.create_message(channel=channel, data=data)

    def get_message(self, id: int):
        return self._connection._get_message(id)
