import aiohttp
import nextcord
import requests

async def webhook_url(url, content):
    async with aiohttp.ClientSession() as session:
        webhook = nextcord.Webhook.from_url(url, session=session)
        await webhook.send(content)
