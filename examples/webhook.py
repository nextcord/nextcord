import aiohttp
import asyncio
import nextcord

async def send_to_webhook(url, content):
    async with aiohttp.ClientSession() as session:
        webhook = nextcord.Webhook.from_url(url, session=session)
        await webhook.send(content)

loop = asyncio.get_event_loop()
url = 'url'
content = 'Hello, world!'
loop.run_until_complete(send_to_webhook(url, content))
