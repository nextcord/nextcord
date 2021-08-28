import nextcord

from nextcord.ext import commands


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_message_delete(self, message: nextcord.Message):
        msg = f'{message.author} has deleted the message: {message.content}'
        await message.channel.send(msg)

bot = Bot(command_prefix='$')

@bot.command()
async def deleteme(ctx):
    msg = await ctx.send('I will delete myself now...')
    await msg.delete()

    # this also works
    await ctx.send('Goodbye in 3 seconds...', delete_after=3.0)


bot.run('token')
