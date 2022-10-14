import asyncio

from nextcord.ext import commands


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create the background task and run it in the background
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def my_background_task(self):
        await self.wait_until_ready()
        counter = 0
        channel = self.get_channel(1234567)  # channel ID goes here
        while not self.is_closed():
            counter += 1
            await channel.send(counter)
            await asyncio.sleep(60)  # task runs every 60 seconds


bot = Bot()
bot.run("token")
