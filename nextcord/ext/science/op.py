from typing import List, Callable, Tuple
from dataclasses import dataclass

from .flags import OpFlags

OP_DICT: List[Callable[[OpFlags], bool]]= [
    lambda opflag: opflag.DISPATCH,
    lambda opflag: opflag.HEARTBEAT,
    lambda opflag: opflag.IDENTIFY,
    lambda opflag: opflag.PRESENCE,
    lambda opflag: opflag.VOICE_STATE,
    lambda opflag: opflag.VOICE_PING,
    lambda opflag: opflag.RESUME,
    lambda opflag: opflag.RECONNECT,
    lambda opflag: opflag.REQUEST_MEMBERS,
    lambda opflag: opflag.INVALIDATE_MEMBERS,
    lambda opflag: opflag.HELLO,
    lambda opflag: opflag.HEARTBEAT_ACK,
    lambda opflag: opflag.GUILD_SYNC,
]

@dataclass
class OpDetails:
    inbound: bool

    # Op 0
    event_name: str = ""

    payload: dict = None
