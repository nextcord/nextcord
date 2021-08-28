import discord

from discord.ext import commands

class MyBot(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message_delete(self, message):
        msg = f'{message.author} has deleted the message: {message.content}'
        await message.channel.send(msg)

bot = MyBot(command_prefix=commands.when_mentioned_or('$'))
bot.run('token')

@bot.command()
async def deleteme(ctx: commands.Context):
    msg = await ctx.send('I will delete myself now...')
    await msg.delete()

    # this also works
    await ctx.send('Goodbye in 3 seconds...', delete_after=3.0)

