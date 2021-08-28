import nextcord
import asyncio

from nextcord.ext import commands


class MyClient(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message: nextcord.Message):
        if message.content.startswith('!editme'):
            msg = await message.channel.send('10')
            await asyncio.sleep(3.0)
            await msg.edit(content='40')

    async def on_message_edit(self, before: nextcord.Message, after: nextcord.Message):
        msg = f'**{before.author}** edited their message:\n{before.content} -> {after.content}'
        await before.channel.send(msg)

bot = MyClient(command_prefix=commands.when_mentioned_or('$'))

@bot.command()
async def editme(ctx: commands.Context):
    msg = await ctx.send('10')
    await asyncio.sleep(3.0)
    await msg.edit(content='40')


bot.run('token')
