"""
The MIT License (MIT)

Copyright (c) 2022-present tag-epic

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

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .enums import KeywordPresetType, try_enum
from .utils import _get_as_snowflake

if TYPE_CHECKING:
    from .types.auto_moderation import (
        AutoModerationActionMetadata as ActionMetadataPayload,
        AutoModerationTriggerMetadata as TriggerMetadataPayload,
    )

__all__ = (
    "AutoModerationTriggerMetadata",
    "AutoModerationActionMetadata",
)


class AutoModerationTriggerMetadata:
    """Represents data about an auto moderation trigger rule.

    .. versionadded:: 2.1

    Attributes
    ----------
    keyword_filter: List[:class:`str`]
        A list of substrings which will be searched for in content.

        .. note::

            This is ``None`` and cannot be provided if the trigger type of the rule is not
            :attr:`AutoModerationTriggerType.keyword`.
    presets: List[:class:`KeywordPresetType`]
        A list of Discord pre-defined wordsets which will be searched for in content.

        .. note::

            This is ``None`` and cannot be provided if the trigger type of the rule is not
            :attr:`AutoModerationTriggerType.keyword_preset`.
    """

    __slots__ = ("keyword_filter", "presets")

    def __init__(
        self,
        keyword_filter: Optional[List[str]] = None,
        presets: Optional[List[KeywordPresetType]] = None,
    ) -> None:
        self.keyword_filter = keyword_filter
        self.presets = presets

    @classmethod
    def from_data(cls, data: TriggerMetadataPayload):
        keyword_filter = data["keyword_filter"] if "keyword_filter" in data else None
        presets = (
            [try_enum(KeywordPresetType, preset) for preset in data["presets"]]
            if "presets" in data
            else None
        )

        return cls(keyword_filter=keyword_filter, presets=presets)

    @property
    def payload(self) -> TriggerMetadataPayload:
        payload: TriggerMetadataPayload = {}

        if self.keyword_filter is not None:
            payload["keyword_filter"] = self.keyword_filter

        if self.presets is not None:
            payload["presets"] = [enum.value for enum in self.presets]

        return payload


class AutoModerationActionMetadata:
    """Represents additional data that is used when an action is executed.

    .. versionadded:: 2.1

    Attributes
    ----------
    channel_id: Optional[:class:`int`]
        The channel to which message content should be logged.

        .. note::

            This is ``None`` and cannot be provided if the action type of the rule is not
            :attr:`AutoModerationActionType.send_alert_message`.
    duration_seconds: Optional[:class:`int`]
        The duration of the timeout in seconds.

        .. note::

            This is ``None`` and cannot be provided if the action type of the rule is not
            :attr:`AutoModerationActionType.send_alert_message`.

        .. note::

            The maximum value that can be used is `2419200` seconds (4 weeks)
    """

    __slots__ = ("channel_id", "duration_seconds")

    def __init__(self, channel_id: Optional[int] = None, duration_seconds: Optional[int] = None):
        self.channel_id = channel_id
        self.duration_seconds = duration_seconds

    @classmethod
    def from_data(cls, data: ActionMetadataPayload):
        channel_id: Optional[int] = _get_as_snowflake(data, "channel_id")
        duration_seconds: Optional[int] = (
            data["duration_seconds"] if "duration_seconds" in data else None
        )

        return cls(channel_id=channel_id, duration_seconds=duration_seconds)

    @property
    def payload(self) -> ActionMetadataPayload:
        payload: ActionMetadataPayload = {}

        if self.channel_id is not None:
            payload["channel_id"] = self.channel_id

        if self.duration_seconds is not None:
            payload["duration_seconds"] = self.duration_seconds

        return payload
