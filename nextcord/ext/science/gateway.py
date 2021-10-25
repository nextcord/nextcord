from nextcord.gateway import nextcordWebSocket


class BunsenBurner(nextcordWebSocket):
    @classmethod
    async def from_client(cls, client, **kwargs):
        client.analyst.ready_timer.start()
        return await super().from_client(client, **kwargs)

    async def send_as_json(self, data):
        self._dispatch('socket_send', data)
        await super().send_as_json(data)
