# This is an example for heads or tails
# It is a simple game where the user has to guess
# if the coin flip will result in heads or tails

# example: $headortails heads

import random

import nextcord
from nextcord.ext import commands

intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)


@bot.command()
async def headortails(ctx, answer):
    if random.choice(["heads", "tails"]) == answer:
        await ctx.reply("Congratulations")
    else:
        await ctx.reply("Sorry you lost")


bot.run("token")
