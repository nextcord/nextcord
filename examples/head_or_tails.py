# This is a example for head and tails
# It is like coinflip but then in discord.

# example: $headortails heads

import random # import the standard random library

from nextcord.ext import commands # import the commands extension from the next cord library

bot = commands.Bot(command_prefix="$")

@bot.command() # register a command called 'headortails' using the @bot.command decorator.
async def headortails(ctx, answer=None):
    if random.choice(["heads", "tails"]) == answer: # choose a random string, either 'heads' or 'tails'
        # from the list and check it against the answer variable
        await ctx.reply("Congratulations") # reply with 'Congratulations' with a discord reply.
    else:
        await ctx.reply("Sorry you lost") # reply with 'Sorry you lost' with a discord reply.
 
bot.run("token")
