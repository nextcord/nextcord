import time
import logging
import typing
from functools import wraps

from aiohttp.typedefs import StrOrURL
from aiohttp.client_reqrep import ClientResponse

from .recorders.base import BaseRecorder
from .flags import EventFlags, OpFlags
from .op import OP_DICT, OpDetails

logger = logging.getLogger(__name__)


class ReadyTimer:
    start_time: float
    end_time: float

    def start(self):
        self.start_time = time.monotonic()
    
    def end(self) -> float:
        self.end_time = time.monotonic()
        return self.end_time - self.start_time

def common_table(table, *, unknown=False):
    def wrapper(func):
        @wraps(func)
        async def wrapped(self, *args, **kwargs) -> None:
            save = getattr(self.recorder, 'save_{}'.format(table))
            args = await func(self, *args, **kwargs)
            if args is None:
                return
            
            if unknown:
                await save(*args, **kwargs, unknown=unknown)
            else:
                await save(*args, **kwargs)
        return wrapped
    return wrapper


class Analyst:
    ready_timer = ReadyTimer()

    def __init__(self, recorder: BaseRecorder, event_flags: EventFlags, op_flags: OpFlags):
        self.recorder = recorder
        self.event_flags = event_flags,
        self.op_flags = op_flags

    async def log(self, event_name, *args, **kwargs):
        handler = getattr(self, 'on_{}'.format(event_name), None)
        try:
            payload: dict = args[0]
        except IndexError:
            return
        
        if type(payload) is bytes:
            return # ping
        
        if handler is None:
            return await self.on_unknown_event(event_name, payload)
        
        if type(payload) is dict:
            await self.recorder.save_events(event_name, payload)
        # TODO: serialize dataclass objects
        await handler(*args, **kwargs)
    
    @common_table('events', unknown=True)
    async def on_unknown_event(self, event_name: str, payload: dict) -> typing.Tuple[str, dict]:
        if type(payload) is dict:
            return event_name, payload

    # TODO: log events

    @common_table('packets')
    async def on_socket_response(self, payload: dict) -> typing.Optional[typing.Tuple[int, OpDetails]]:
        op_code = payload['op']
        
        handler = getattr(self, 'on_socket_op_{}'.format(op_code), None)
        
        details = OpDetails(inbound=True, payload=payload)
        if handler:
            details = await handler(payload)
        
        should_log = OP_DICT[op_code](self.op_flags)
        if should_log:
            return op_code, details
    
    @common_table('packets')
    async def on_socket_send(self, payload: dict) -> typing.Optional[typing.Tuple[int, OpDetails]]:
        op_code = payload['op']

        # TODO: propagate

        details = OpDetails(inbound=False, payload=payload)

        should_log = OP_DICT[op_code](self.op_flags)
        if should_log:
            return op_code, details
    
    async def on_socket_op_0(self, payload: dict) -> OpDetails:
        event_name = payload['t']

        handler = getattr(self, 'on_socket_{}'.format(event_name), None)

        if handler:
            await handler(payload)

        return OpDetails(inbound=True, event_name=event_name, payload=payload)
    
    async def on_socket_READY(self, payload: dict) -> None:
        duration = self.ready_timer.end()
        logger.debug("Received READY event {:,.2f} milliseconds after connection.".format(duration * 1000))
    
    async def on_socket_RESUME(self, payload: dict) -> None:
        duration = self.ready_timer.end()
        logger.debug("Received RESUME event {:,.2f} milliseconds after reconnection.".format(duration * 1000))

    @common_table('requests')
    async def http_request(self, method: str, str_or_url: StrOrURL, **kwargs: dict) -> typing.Tuple[typing.Any, ...]:
        return method, str_or_url, kwargs
    
    @common_table('requests')
    async def http_request_error(self, method: str, str_or_url: StrOrURL, **kwargs: dict) -> typing.Tuple[typing.Any, ...]:
        return method, str_or_url, kwargs
