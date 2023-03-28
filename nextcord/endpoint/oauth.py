from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from aiohttp import web
from yarl import URL

from ..enums import OAuth2Scopes

_log = logging.getLogger(__name__)


__all__ = (
    "OAuth2Endpoint",
    "oauth_url_request_generator",
)


OAUTH_RESPONSE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🔒</text></svg>">
    <title>{}</title>
  </head>
  <body>
	{}
  </body>
</html>
"""


class OAuth2Endpoint:
    def __init__(self) -> None:
        pass

    def middleware(self, route: str):
        @web.middleware
        async def oauth_endpoint_middleware(request: web.Request, handler):
            if request.path.startswith(route) and request.method == "GET":
                _log.debug("Received oauth on url %s", request.url)
                if request.rel_url.query.get("code"):
                    _log.debug("Query has code, executing on_oauth_endpoint and sending positive response.")
                    # TODO: Should this made into a task or try/except so errors don't affect the response, or
                    #  should erroring make a 50X error appear like it does currently?
                    await self.on_oauth_endpoint(
                        request.url.with_query(None).human_repr(),
                        request.rel_url.query["code"],
                        request.rel_url.query.get("state", None)
                    )
                    # TODO: Look into a better way of handling this, allowing custom responses? Maybe put them inside
                    #  __init__ as kwargs?
                    return web.Response(
                        body=OAUTH_RESPONSE_TEMPLATE.format(
                            "OAuth Accepted.", "<h1>👍 OAuth Received 👍</h1><h1>Close Whenever</h1>"
                        ), content_type="text/html"
                    )
                else:
                    _log.debug("Query doesn't have code, sending negative response.")
                    return web.Response(
                        body=OAUTH_RESPONSE_TEMPLATE.format(
                            "OAuth Accepted.", "<h1>👎 No Oauth 👎</h1><h1>Close Whenever</h1>"
                        ), content_type="text/html"
                    )
            else:
                _log.debug("Ignoring request %s %s", request.method, request.url)
                resp = await handler(request)
                return resp

        return oauth_endpoint_middleware

    async def on_oauth_endpoint(self, redirect_uri: str, code: str, state: Optional[str]) -> None:
        _log.critical("%s %s, %s", redirect_uri, code, state)

    async def start(
            self,
            *,
            route: str = "/endpoint/oauth2",
            host: str = "0.0.0.0",
            port: int = 8080
    ) -> web.TCPSite:
        app = web.Application(middlewares=[self.middleware(route)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        _log.info("%s listening on %s on route %s", self.__class__.__name__, site.name, route)
        return site

    def run(
            self,
            *,
            route: str = "/endpoint/oauth2",
            host: str = "0.0.0.0",
            port: int = 8080,
            loop: asyncio.AbstractEventLoop | None = None
    ):
        loop = loop or asyncio.new_event_loop()
        task = loop.create_task(self.start(route=route, host=host, port=port))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            _log.debug("KeyboardInterrupt encountered, stopping loop.")
            if task.done():
                site = task.result()
                loop.run_until_complete(site.stop())
            else:
                task.cancel()
            loop.run_until_complete(asyncio.sleep(0.25))


def oauth_url_request_generator(
    redirect_uri: str,
    client_id: int,
    scopes: List[OAuth2Scopes],
    state: str,
    base_url: str = "https://discord.com/api/oauth2/authorize",
):
    ret = URL(base_url)
    ret = ret.with_query(
        {
            "redirect_uri": redirect_uri,
            "client_id": str(client_id),
            "scope": " ".join([scope.value for scope in scopes]),
            "state": state,
            "response_type": "code",
        }
    )
    return ret
