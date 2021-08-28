from nextcord.ext import commands

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


bot = Bot(command_prefix='$')

@bot.command()
async def hello(ctx):
    await ctx.reply('Hello!')

bot.run('token')
