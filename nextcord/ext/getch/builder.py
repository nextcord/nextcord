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

from __future__ import annotations
from .manager import GetchManager

class GetchBuilder:
    def __init__(self, *, bot):
        self.http = GetchManager(bot=bot)
        self.ids = {
            'guild': None,
            'channel': None,
            'message': None,
        }

    async def getch(self):
        guild = None
        channel = None
        message = None

        if (guild_id := self.ids['guild']):
            guild = self.http.get_guild(guild_id) or await self.http.fetch_guild(guild_id)

        if (channel_id := self.ids['channel']):
            channel = self.http.get_channel(channel_id) or await self.http.fetch_channel(channel_id, guild=guild)
        
        if (message_id := self.ids['message']):
            message = self.http.get_message(message_id) or await self.http.fetch_message(message_id, channel=channel)

        # return whatever object in order of depth.
        return message or channel or guild

    def uild(self, id: int) -> GetchBuilder:
        self.ids['guild'] = id
        return self

    def annel(self, id: int) -> GetchBuilder:
        self.ids['channel'] = id
        return self

    def essage(self, id: int) -> GetchBuilder:
        self.ids['message'] = id
        return self
