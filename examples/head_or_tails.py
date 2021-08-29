import random

from nextcord.ext import commands

bot = commands.Bot(command_prefix="h!")

@bot.command()
async def headortails(ctx, answer=None):
    number = random.randint((0,1))
    
    tails = 0
    heads = 1
    
    if answer is None:
        await ctx.send("You have not set an argumeny, please do: h!headsortails `heads` or h!headsortails `tails`")
    else:
        if answer is not "heads" or answer is not "tails":
            await ctx.send("Invalid agrument, the arguments are: `heads` or `tails`! ")
        else:
            if number == tails :
                if answer == "tails":
                    await ctx.send("You won, congratulations!!")
                else:
                    await ctx.send("Awhhh, you lost! :(")
            elif number == heads:
                if answer == "heads":
                    await ctx.send("You won, congratulations!!")
                else:
                    await ctx.send("Awhhh, you lost! :(")

    
