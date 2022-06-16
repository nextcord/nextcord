# This is an example for sending message to a channel using its webhook URL.
# You can use this to send messages to a channel without using the bot.

import asyncio

import aiohttp
import nextcord


async def send_to_webhook(url, content):
    # Create a new HTTP session and use it to create webhook object
    async with aiohttp.ClientSession() as session:
        webhook = nextcord.Webhook.from_url(url, session=session)
        await webhook.send(content)


asyncio.run(send_to_webhook("url", "Hello, world!"))
