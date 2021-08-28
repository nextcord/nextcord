from nextcord.ext import commands

class Bot(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


bot = Bot(command_prefix=commands.when_mentioned_or('$'))

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.reply('Hello!')

bot.run('token')
