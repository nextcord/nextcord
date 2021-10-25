import typing
from dataclasses import dataclass

from .flags import EventFlags, OpFlags
from .gateway import BunsenBurner
from .snoopy import Analyst
from .recorders.base import BaseRecorder
from .http import Beaker, Pipette


@dataclass
class Configuration:
    recorder: BaseRecorder
    event_flags: EventFlags = EventFlags.all()
    op_flags: OpFlags = OpFlags.all()
    gw_cls: BunsenBurner = BunsenBurner
    anal_cls: Analyst = Analyst
    httpclient_cls: Pipette = Pipette
    session_cls: Beaker = Beaker

Config = Configuration
