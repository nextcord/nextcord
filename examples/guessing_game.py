import asyncio
import random

import nextcord
from nextcord.ext import commands

intents = nextcord.intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)


@bot.command()
async def guess(ctx):
    await ctx.send("Guess a number between 1 and 10.")


@bot.command()
async def guess(ctx, guess: int = None):
    def is_correct(message):
        return message.author == ctx.author and message.content.isdigit()

    answer = random.randint(1, 10)

    if not guess:
        await ctx.send("Guess a number between 1 and 10.")
        try:
            guess = await bot.wait_for("message", check=is_correct, timeout=5.0)
            guess = guess.content
        except asyncio.TimeoutError:
            return await ctx.send(f"Sorry, you took too long it was {answer}.")

    if int(guess) == answer:
        await ctx.send("You are right!")
    else:
        await ctx.send(f"Oops. It is actually {answer}.")


bot.run("token")
