import logging
import asyncio

from nextcord import Client
from nextcord.gateway import ResumeWebSocket

from .config import Configuration

logger = logging.getLogger(__name__)


class Scientist(Client):
    def __init__(self, *args, **kwargs):
        self.config: Configuration = kwargs.pop('config')
        logger.debug('Initiated Scientist with %s.', self.config)

        self.analyst = self.config.anal_cls(self.config.recorder, self.config.event_flags, self.config.op_flags)
        super().__init__(*args, **kwargs)
        self.http = self.config.httpclient_cls.from_http_client(self.http, self.config.session_cls, self.analyst)
    
    def dispatch(self, event, *args, **kwargs) -> None:
        self._schedule_event(self.analyst.log, 'science_logging', event, *args, **kwargs)
        super().dispatch(event, *args, **kwargs)
    
    async def start(self, *args, **kwargs) -> None:
        await self.config.recorder.start()
        next_id = await self.config.recorder.last_events_id() + 1
        logger.debug("The next ID for the 'events' table is %s", next_id)
        await super().start(*args, **kwargs)
    
    async def close(self) -> None:
        await super().close()
        if self.config.recorder.started:
            curr_id = await self.config.recorder.last_events_id()
            logger.debug("The final ID for the 'events' table is %s", curr_id)
            await self.config.recorder.end()
    
    async def _connect(self) -> None:
        cls = self.config.gw_cls
        coro = cls.from_client(self, shard_id=self.shard_id)
        self.ws: cls = await asyncio.wait_for(coro, timeout=180.0)
        while True:
            try:
                await self.ws.poll_event()
            except ResumeWebSocket:
                logger.info('Got a request to RESUME the websocket.')
                self.dispatch('disconnect')
                coro = cls.from_client(self, shard_id=self.shard_id, session=self.ws.session_id,
                                                    sequence=self.ws.sequence, resume=True)
                self.ws = await asyncio.wait_for(coro, timeout=180.0)
