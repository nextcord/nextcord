import random
import asyncio

from nextcord.ext import commands


class Bot(commands.Bot):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


bot = Bot(command_prefix=commands.when_mentioned_or('$'))

@bot.command()
async def guess(ctx: commands.Context):
    await ctx.send('Guess a number between 1 and 10.')

    def is_correct(m):
        return m.author == ctx.author and m.content.isdigit()

    answer = random.randint(1, 10)

    try:
        guess = await bot.wait_for('message', check=is_correct, timeout=5.0)
    except asyncio.TimeoutError:
        return await ctx.send(f'Sorry, you took too long it was {answer}.')

    if int(guess.content) == answer:
        await ctx.send('You are right!')
    else:
        await ctx.send(f'Oops. It is actually {answer}.')

bot.run('token')
