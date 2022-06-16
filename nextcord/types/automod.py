from typing import List, Literal, TypedDict

from .snowflake import Snowflake

EventType = Literal[1]
TriggerType = Literal[1, 2, 3, 4]
KeywordPresetType = Literal[1, 2, 3]
ActionType = Literal[1, 2, 3]


class _ActionMetadataAlertMessage(TypedDict, total=False):
    channel_id: Snowflake

class _ActionMetadataTimeout(TypedDict, total=False):
    duration_seconds: int

class ActionMetadata(_ActionMetadataAlertMessage, _ActionMetadataTimeout):
    pass

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
    exempt_roles: List[Snowflake]
    exempt_channels: List[Snowflake]
