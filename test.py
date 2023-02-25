from nextcord import Intents, File, Embed
from nextcord.ext import commands
import logging

logging.basicConfig(level=logging.DEBUG)

bot = commands.Bot(intents=Intents.default(), command_prefix=commands.when_mentioned)

@bot.event
async def on_ready():
    print(bot.user)

@bot.slash_command()
async def test(ctx):
    file = File("C:\\Users\\XxHEROSOLDIERxX\\Desktop\\nz5798tb85v51.JPG")
    file1 = File("C:\\Users\\XxHEROSOLDIERxX\\Desktop\\nz5798tb85v51.JPG")
    em = Embed(title="Test")
    em.set_image(file=file)
    es = Embed(title="h")
    es.set_image(file=file)
    msg = await ctx.send(embeds=[es])
    es.set_image(file=file1)
    await msg.edit(embed=es)

bot.run("OTc1MzM4NTUwMjg1NDM5MDE2.GWIudC.Cb4r4iCSAuf6c80qzY9DSdThAutdwqGfqNFd70")