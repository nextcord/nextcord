# SPDX-License-Identifier: MIT

from typing import List, Literal, Optional, TypedDict

from typing_extensions import NotRequired

from .snowflake import Snowflake

AutoModerationEventType = Literal[1]
AutoModerationTriggerType = Literal[1, 2, 3, 4, 5]
KeywordPresetType = Literal[1, 2, 3]
AutoModerationActionType = Literal[1, 2, 3, 4]


class AutoModerationTriggerMetadata(TypedDict, total=False):
    keyword_filter: List[str]
    regex_patterns: List[str]
    presets: List[KeywordPresetType]
    allow_list: List[str]
    mention_total_limit: Optional[int]


class AutoModerationActionMetadata(TypedDict, total=False):
    channel_id: Snowflake
    duration_seconds: int


class AutoModerationAction(TypedDict):
    type: AutoModerationActionType
    metadata: NotRequired[AutoModerationActionMetadata]


class AutoModerationRule(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    name: str
    creator_id: Snowflake
    event_type: AutoModerationEventType
    trigger_type: AutoModerationTriggerType
    trigger_metadata: AutoModerationTriggerMetadata
    actions: List[AutoModerationAction]
    enabled: bool
    exempt_roles: List[Snowflake]
    exempt_channels: List[Snowflake]


class AutoModerationRuleCreate(TypedDict):
    name: str
    event_type: AutoModerationEventType
    trigger_type: AutoModerationTriggerType
    actions: List[AutoModerationAction]
    trigger_metadata: NotRequired[AutoModerationTriggerMetadata]
    enabled: NotRequired[bool]
    exempt_roles: NotRequired[List[Snowflake]]
    exempt_channels: NotRequired[List[Snowflake]]


class AutoModerationRuleModify(TypedDict, total=False):
    name: str
    event_type: AutoModerationEventType
    trigger_metadata: AutoModerationTriggerMetadata
    actions: List[AutoModerationAction]
    enabled: bool
    exempt_roles: List[Snowflake]
    exempt_channels: List[Snowflake]


class AutoModerationActionExecution(TypedDict):
    guild_id: Snowflake
    action: AutoModerationAction
    rule_id: Snowflake
    rule_trigger_type: AutoModerationTriggerType
    user_id: Snowflake
    matched_keyword: Optional[str]
    channel_id: NotRequired[Snowflake]
    message_id: NotRequired[Snowflake]
    alert_system_message_id: NotRequired[Snowflake]
    content: NotRequired[str]
    matched_content: NotRequired[Optional[str]]
