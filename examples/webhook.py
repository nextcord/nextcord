import aiohttp
import nextcord
import requests

async def webhook_url(url, content):
    async with aiohttp.ClientSession() as session:
        webhook = nextcord.Webhook.from_url(url, session=session)
        await webhook.send(content)

# Synchronous version of webhook_url
def webhook_url_sync(url, content):
    with requests.Session() as session:
        webhook = nextcord.SyncWebhook.from_url(url, session=session)
        webhook.send(content)
