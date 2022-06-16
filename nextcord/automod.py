# TODO: add license
from __future__ import annotations
from .mixins import Hashable
from typing import TYPE_CHECKING
from .enums import (
    EventType,
    TriggerType,
    try_enum,
)

if TYPE_CHECKING:
    from .types.automod import AutoModerationRule as AutoModerationRulePayload
    from .state import ConnectionState
    from .guild import Guild
    from typing import List

class AutoModerationRule(Hashable):
    def __init__(self, *, state: ConnectionState, guild: Guild, data: AutoModerationRulePayload):
        self.id = int(data['id'])
        self.guild: Guild = guild
        self._state: ConnectionState = state
        self._from_payload(data)

        
    
    def _from_payload(self, data: AutoModerationRulePayload):
        self.guild_id: int = int(data['guild_id'])
        self.name: str = data['name']
        self.creator_id: int = int(data['creator_id'])
        self.event_type = try_enum(EventType, data['event_type'])  # left becuz idk what does it return so h
        self.trigger_type = try_enum(TriggerType, data['trigger_type'])  # same
        self.enabled: bool = data['enabled']
        self.exempt_roles_id: List[int] = [int(exempt_role) for exempt_role in data['exempt_roles']]
        self.exempt_channels_id: List[int] = [int(exempt_channel) for exempt_channel in data['exempt_channels']]
        # TODO: unpack trigger + action metadatas
    
    async def delete(self):
        await self._state.http.delete_automod_rule(guild_id=self.guild.id, rule_id=self.id)
    

    
