from nextcord.ext import commands

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


bot = Bot(command_prefix=commands.when_mentioned_or('$'))

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.reply('Hello!')

bot.run('token')
