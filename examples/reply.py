from nextcord.ext import commands


bot = commands.Bot(command_prefix='$')

@bot.command()
async def hello(ctx):
    await ctx.reply('Hello!')

bot.run('token')
