"""
The MIT License (MIT)

Copyright (c) 2021-present tag-epic

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from typing import List, Literal, Optional, TypedDict, Union

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
    allow_list: List[str]


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


class _AutoModerationRuleExecutionOptional(TypedDict, total=False):
    channel_id: Snowflake
    message_id: Snowflake
    alert_system_message_id: Snowflake


class AutoModerationActionExecution(_AutoModerationRuleExecutionOptional):
    guild_id: Snowflake
    action: AutoModerationAction
    rule_id: Snowflake
    rule_trigger_type: TriggerType
    user_id: Snowflake
    content: str
    matched_keyword: Optional[str]
    matched_content: Optional[str]
