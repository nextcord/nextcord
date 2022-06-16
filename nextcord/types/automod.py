from typing import TypedDict, List, Literal
from .snowflake import Snowflake


EventType = Literal[1]
TriggerType = Literal[1, 2, 3, 4]
KeywordPresetType = Literal[1, 2, 3]
ActionType = Literal[1, 2, 3]


class ActionMetadata(TypedDict):
    channel_id: Snowflake
    duration_seconds: int

class TriggerMetadata(TypedDict):
    keyword_filter: List[str]
    presets: List[KeywordPresetType]

class _AutoModerationActionOptional(TypedDict, total=False):
    metadata: ActionMetadata

class AutoModerationAction(_AutoModerationActionOptional):
    type: ActionType


class AutoModerationRule(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    name: str
    creator_id: Snowflake
    event_type: EventType
    trigger_type: TriggerType
    trigger_metadata: TriggerMetadata
    actions: List[AutoModerationAction]
    enabled: bool
    exempt_role: List[Snowflake]
    exempt_channel: List[Snowflake]
