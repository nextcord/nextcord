"""An experiment to allow for webhooks to change channels.

Example:
```py
webhook = await ctx.bot.fetch_webhook(id)
channel = ctx.guild.text_channels[1]

await webhook.move_to(channel=channel)
```
"""
from nextcord import utils, errors, webhook, TextChannel
import asyncio
import json
import aiohttp

# register endpoint

_old_prepare = webhook.WebhookAdapter._prepare


def _prepare(self, webhook):
    _old_prepare(self, webhook)
    self._move_url = "{0.BASE}/webhooks/{1}".format(self, webhook.id)


webhook.WebhookAdapter._prepare = _prepare


def _move_webhook(self, token, **payload):
    return self.request("PATCH", self._move_url, payload=payload, token=token)


webhook.WebhookAdapter.move_webhook = _move_webhook

# fix up AsyncWebhookAdapter.request to provide token -- was hoping to not need to replace it completely


async def _request(self, verb, url, payload=None, multipart=None, *, files=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = token

    data = None
    files = files or []
    if payload:
        headers["Content-Type"] = "application/json"
        data = utils.to_json(payload)

    if multipart:
        data = aiohttp.FormData()
        for key, value in multipart.items():
            if key.startswith("file"):
                data.add_field(key, value[1], filename=value[0], content_type=value[2])
            else:
                data.add_field(key, value)

    for tries in range(5):
        for file in files:
            file.reset(seek=tries)

        async with self.session.request(verb, url, headers=headers, data=data) as r:
            # Coerce empty strings to return None for hygiene purposes
            response = (await r.text(encoding="utf-8")) or None
            if r.headers["Content-Type"] == "application/json":
                response = json.loads(response)

            # check if we have rate limit header information
            remaining = r.headers.get("X-Ratelimit-Remaining")
            if remaining == "0" and r.status != 429:
                delta = utils._parse_ratelimit_header(r)
                await asyncio.sleep(delta)

            if 300 > r.status >= 200:
                return response

            # we are being rate limited
            if r.status == 429:
                retry_after = response["retry_after"] / 1000.0
                await asyncio.sleep(retry_after)
                continue

            if r.status in (500, 502):
                await asyncio.sleep(1 + tries * 2)
                continue

            if r.status == 403:
                raise errors.Forbidden(r, response)
            elif r.status == 404:
                raise errors.NotFound(r, response)
            else:
                raise errors.HTTPException(r, response)
    # no more retries
    raise errors.HTTPException(r, response)


webhook.AsyncWebhookAdapter.request = _request

# add the method + _async_move


async def _async_move(self, channel_id, token, payload):
    await self._adapter.move_webhook(token, **payload)

    self.channel_id = channel_id


def _move_to(self, channel):
    if not isinstance(channel, TextChannel):
        raise TypeError(
            "Expected TextChannel parameter, received %s instead." % channel.__class__.__name__
        )

    payload = {"channel_id": channel.id}

    token = channel._state.http.token

    if channel._state.is_bot:
        token = "Bot " + token

    if isinstance(self._adapter, webhook.AsyncWebhookAdapter):
        return self._async_move(channel.id, token, payload)


webhook.Webhook._async_move = _async_move
webhook.Webhook.move_to = _move_to
