import datetime
import json

from databases import Database
import sqlalchemy
from sqlalchemy import sql

from .base import BaseRecorder
from ..op import OpDetails

metadata = sqlalchemy.MetaData()

events_id_seq = sqlalchemy.Sequence('events_id_seq', metadata=metadata)

events = sqlalchemy.Table(
    'events', metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, events_id_seq, primary_key=True),
    sqlalchemy.Column('time', sqlalchemy.Time),
    sqlalchemy.Column('name', sqlalchemy.Text),
    sqlalchemy.Column('payload', sqlalchemy.Text),
    sqlalchemy.Column('unknown', sqlalchemy.Boolean),
)

packets_id_seq = sqlalchemy.Sequence('packets_id_seq', metadata=metadata)

packets = sqlalchemy.Table(
    'packets', metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, packets_id_seq, primary_key=True),
    sqlalchemy.Column('time', sqlalchemy.Time),
    sqlalchemy.Column('op_code', sqlalchemy.Integer),
    sqlalchemy.Column('event_name', sqlalchemy.Text),
    sqlalchemy.Column('payload', sqlalchemy.Text),
    sqlalchemy.Column('inbound', sqlalchemy.Boolean),
)


class DatabasesRecorder(BaseRecorder):
    started: bool = False
    def __init__(self, database_url: str):
        self.db: Database = Database(database_url)
    
    async def start(self) -> None:
        await self.db.connect()
        self.started = True
    
    async def end(self) -> None:
        await self.db.disconnect()
        self.started = False
    
    async def last_events_id(self) -> int:
        query = packets.select().order_by(packets.c.id.desc()).limit(1)
        packets_id = await self.db.fetch_val(query)
        return packets_id

    async def save_events(self, name: str, payload: dict, *, unknown: bool=False) -> None:
        query = events.insert().values(
            time=datetime.datetime.utcnow(),
            name=name,
            payload=json.dumps(payload),
            unknown=unknown,
        )
        await self.db.execute(query)
    
    async def save_packets(self, op_code: int, details: OpDetails) -> None:
        query = packets.insert().values(
            time=datetime.datetime.utcnow(),
            op_code=op_code,
            event_name=details.event_name,
            payload=json.dumps(details.payload),
            inbound=details.inbound,
        )
        await self.db.execute(query)

    async def save_requests(self, *args, **kwargs) -> None:
        # TODO: log properly
