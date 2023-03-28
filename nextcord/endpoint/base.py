import asyncio
import logging
from typing import Optional

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web import StreamResponse

_log = logging.getLogger(__name__)


__all__ = (
    "BaseEndpoint",
    "BaseMiddleware",
)


class BaseEndpoint:
    def __init__(self, middlewares: list) -> None:
        self.middlewares = middlewares

    async def start(self, *, host: str = "0.0.0.0", port: int = 8080) -> web.TCPSite:
        app = web.Application(middlewares=self.middlewares)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        _log.info("%s listening on %s", self.__class__.__name__, site.name)
        return site

    def run(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8080,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        loop = loop or asyncio.new_event_loop()
        task = loop.create_task(self.start(host=host, port=port))
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


class BaseMiddleware:
    def __init__(self, method: str = "GET", route: str = "/endpoint/default") -> None:
        self._method: Optional[str] = method
        self._route: Optional[str] = route

    @property
    def method(self) -> Optional[str]:
        return self._method

    @property
    def route(self) -> Optional[str]:
        return self._route

    def middleware(self):
        @web.middleware
        async def route_middleware(request: web.Request, handler: Handler) -> StreamResponse:
            if request.path.startswith(self.route) and request.method == self.method:
                return await self.on_middleware_match(request, handler)
            else:
                _log.debug("Ignoring request %s %s", request.method, request.url)
                resp = await handler(request)
                return resp

        return route_middleware

    async def on_middleware_match(self, request: web.Request, handler: Handler) -> StreamResponse:
        raise NotImplementedError
