# This is a example for head and tails
# It is like coinflip but then in discord.

# example: $headortails heads

import random

from nextcord.ext import commands

bot = commands.Bot(command_prefix="$")

@bot.command()
async def headortails(ctx, answer=None):
    if random.choice(["heads", "tails"]) == answer:
        await ctx.reply("Congratulations")
    else:
        await ctx.reply("Sorry you lost")
 
bot.run("token")
