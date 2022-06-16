from typing import TypedDict, List
from .snowflake import Snowflake

class ActionMetadata(TypedDict):
    channel_id: Snowflake
    duration_seconds: int

class TriggerMetadata(TypedDict):
    keyword_filter: List[str]
    presets: List[int]

class _AutoModerationActionOptional(TypedDict, total=False):
    metadata: ActionMetadata

class AutoModerationAction(_AutoModerationActionOptional):
    type: int


class AutoModerationRule(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    name: str
    creator_id: Snowflake
    event_type: int
    trigger_type: int
    trigger_metadata: TriggerMetadata
    actions: List[AutoModerationAction]
    enabled: bool
    exempt_role: List[Snowflake]
    exempt_channel: List[Snowflake]
