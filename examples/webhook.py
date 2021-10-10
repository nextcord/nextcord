import aiohttp
import nextcord
from nextcord.ext import commands
import requests

bot = commands.Bot(command_prefix='$')

@bot.command()
async def webhook_url(ctx, url, *, content):
    async with aiohttp.ClientSession() as session:
        webhook = nextcord.Webhook.from_url(url, session=session)
        await webhook.send(content)

# Synchronous version of webhook_url
@bot.command()
async def webhook_url_sync(ctx, url, *, content):
    with requests.Session() as session:
        webhook = nextcord.SyncWebhook.from_url(url, session=session)
        webhook.send(content)

# Use first webhook from provided channel. Bot must have manage_webhook permission.
# Channel must have at least one webhook.
@bot.command()
async def webhook_channel(ctx, channel: nextcord.TextChannel, *, content):
    webhooks = await channel.webhooks()
    if len(webhooks) == 0:
        return await ctx.reply("There are no webhooks for this channel.")
    await webhooks[0].send(content)

bot.run('token')
