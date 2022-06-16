from typing import List, Literal, TypedDict, Union

from .snowflake import Snowflake

EventType = Literal[1]
TriggerType = Literal[1, 2, 3, 4]
KeywordPresetType = Literal[1, 2, 3]
ActionType = Literal[1, 2, 3]


class ActionMetadataAlertMessage(TypedDict):
    channel_id: Snowflake


class ActionMetadataTimeout(TypedDict):
    duration_seconds: int


ActionMetadata = Union[ActionMetadataAlertMessage, ActionMetadataTimeout]


class TriggerMetadataKeywordFilter(TypedDict):
    keyword_filter: List[str]


class TriggerMetadataKeywordPreset(TypedDict):
    presets: List[KeywordPresetType]


TriggerMetadata = Union[TriggerMetadataKeywordFilter, TriggerMetadataKeywordPreset]


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
