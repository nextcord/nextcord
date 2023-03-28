from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from aiohttp.typedefs import Handler, StreamResponse

_log = logging.getLogger(__name__)


__all__ = (
    "RoleConnVerifyEndpoint",
    "role_conn_metadata_generator",
)


ROLE_CONN_RESPONSE_TEMPLATE = """
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


class RoleConnVerifyEndpoint:
    def __init__(self) -> None:
        pass

    def middleware(self, route: str):
        @web.middleware
        async def role_conn_endpoint_middleware(request: web.Request, handler: Handler) -> StreamResponse:
            if request.path.startswith(route) and request.method == "GET":
                _log.debug("Received oauth on url %s", request.url)
                return web.Response(
                    body=ROLE_CONN_RESPONSE_TEMPLATE.format(
                        "Nothing Accepted.", "<h1>👍 Nothing Received 👍</h1><h1>Close Whenever</h1>"
                    ), content_type="text/html"
                )
            else:
                _log.debug("Ignoring request %s %s", request.method, request.url)
                resp = await handler(request)
                return resp

        return role_conn_endpoint_middleware

    async def on_role_conn_verify_endpoint(self) -> None:
        pass

    async def start(
        self, *, route: str = "/endpoint/oauth2", host: str = "0.0.0.0", port: int = 8080
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
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
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


def role_conn_metadata_generator(arg1) -> dict:
    ret = {}

    return ret
