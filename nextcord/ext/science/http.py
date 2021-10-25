import time
import sys
from urllib.parse import quote as _uriquote
import weakref
import asyncio

from aiohttp import ClientSession
from nextcord.http import HTTPClient, Route, MaybeUnlock, json_or_text
from nextcord import utils
from nextcord.errors import HTTPException, Forbidden, NotFound, LoginFailure, GatewayNotFound

from .snoopy import Analyst


class Beaker:
    def __init__(self, *args, **kwargs):
        self._pipette: Pipette = kwargs.pop('pipette')
        self._session = ClientSession(*args, **kwargs)
        self.prepare_request_method()
    
    def __getattr__(self, name):
        return getattr(self._session, name)
    
    def prepare_request_method(self):
        _old_request = self._session._request
        async def _request(s, *args, **kwargs):
            start = time.monotonic()
            try:
                ret = await _old_request(s, *args, **kwargs)
            except Exception as e:
                await self._pipette.analyst.http_request_error(*args, kwargs, exc=e)
                raise
            else:
                end = time.monotonic()
                dur = end - start
                await self._pipette.analyst.http_request(*args, kwargs, ret=ret, dur=dur)
                return ret
        self._session._request = _request


class Pipette(HTTPClient):
    session_cls: Beaker
    analyst: Analyst

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from . import __version__ # circular import
        self.user_agent += f' nextcord-ext-science/{__version__}'
    
    @classmethod
    def from_http_client(cls, http_client: HTTPClient, session_cls: Beaker, analyst: Analyst):
        old = http_client
        self = cls(
            old.connector,
            proxy=old.proxy,
            proxy_auth=old.proxy_auth,
            loop=old.loop,
            unsync_clock=not old.use_clock,
        )
        self.session_cls = session_cls
        self.analyst = analyst
        return self
        
    def recreate(self):
        if self._HTTPClient__session.closed:
            self._HTTPClient__session = self.session_cls(connector=self.connector, pipette=self)

    async def static_login(self, token, *, bot):
        print(dir(self))
        # Necessary to get aiohttp to stop complaining about session creation
        self._HTTPClient__session = self.session_cls(connector=self.connector, pipette=self)
        print(self._HTTPClient__session)
        old_token, old_bot = self.token, self.bot_token
        self._token(token, bot=bot)

        try:
            print(self._HTTPClient__session)
            data = await self.request(Route('GET', '/users/@me'))
        except HTTPException as exc:
            self._token(old_token, bot=old_bot)
            if exc.response.status == 401:
                raise LoginFailure('Improper token has been passed.') from exc
            raise

        return data
# 
# create table 
# requests(
#   id serial primary key, 
#   time time, 
#   verb text, 
#   url text, 
#   data text, 
#   headers text, 
#   params text,
#   result text,
#   error text
# )
#
