import random

from nextcord.ext import commands

bot = commands.Bot(command_prefix="$")

@bot.command()
async def headortails(ctx, answer=None):
    machine_choice = random.choice(["heads", "tails"])

    if machine_choice == answer:
        await ctx.send("Congratulations")
    else:
        await ctx.send("Sorry you lost")
 
bot.run("token")
