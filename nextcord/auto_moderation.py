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

from .enums import (
    AutoModerationActionType,
    AutoModerationEventType,
    AutoModerationTriggerType,
    KeywordPresetType,
    try_enum,
)
from .mixins import Hashable
from .utils import _get_as_snowflake

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.auto_moderation import (
        AutoModerationAction as AutoModerationActionPayload,
        AutoModerationActionMetadata as ActionMetadataPayload,
        AutoModerationRule as AutoModerationRulePayload,
        AutoModerationTriggerMetadata as TriggerMetadataPayload,
    )

__all__ = (
    "AutoModerationTriggerMetadata",
    "AutoModerationActionMetadata",
    "AutoModerationAction",
    "AutoModerationRule",
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
        keyword_filter = data.get("keyword_filter")
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
        channel_id = _get_as_snowflake(data, "channel_id")
        duration_seconds = data.get("duration_seconds")

        return cls(channel_id=channel_id, duration_seconds=duration_seconds)

    @property
    def payload(self) -> ActionMetadataPayload:
        payload: ActionMetadataPayload = {}

        if self.channel_id is not None:
            payload["channel_id"] = self.channel_id

        if self.duration_seconds is not None:
            payload["duration_seconds"] = self.duration_seconds

        return payload


class AutoModerationAction:
    """Represents an auto moderation action which will execute whenever a rule is triggered.

    .. versionadded:: 2.1

    Attributes
    ----------
    type: :class:`AutoModerationActionType`
        The type of this action.
    metadata: :class:`AutoModerationActionMetadata`
        The additional metadata needed during execution for this specific action type.
    """

    __slots__ = ("type", "metadata")

    def __init__(self, data: AutoModerationActionPayload) -> None:
        self.type = try_enum(AutoModerationActionType, data["type"])
        self.metadata = AutoModerationActionMetadata.from_data(data.get("metadata", {}))


class AutoModerationRule(Hashable):
    """Represents a Discord auto moderation rule.

    .. versionadded:: 2.1

    .. container:: operations

        .. describe:: x == y

            Checks if two rules are equal.

        .. describe:: x != y

            Checks if two rules are not equal.

        .. describe:: hash(x)

            Returns the rules's hash.

        .. describe:: str(x)

            Returns the rules's name.

    Attributes
    ----------
    id: :class:`int`
        The rule's unique ID.
    guild_id: :class:`int`
        The guild's unique ID which this rule belongs to.
    guild: Optional[:class:`Guild`]
        The guild which this rule belongs to, if found in cache.
    name: :class:`str`
        The rule's name.
    creator_id: :class:`int`
        The user's unique ID which first created this rule.
    creator: :class:`Member`
        The member which first created this rule, if found in cache.
    event_type: :class:`AutoModerationEventType`
        The event context in which this rule is checked.
    trigger_type: :class:`AutoModerationTriggerType`
        The type of content that can trigger this rule.
    trigger_metadata: :class:`AutoModerationTriggerMetadata`
        Additional data that is used when checking if this rule is triggered.
    actions: List[:class:`AutoModerationAction`]
        The actions which will execute when the rule is triggered.
    enabled: :class:`bool`
        Whether the rule is enabled.
    exempt_role_ids: List[:class:`int`]
        The role ids that should not be affected by the rule.
    exempt_channel_ids: List[:class:`int`]
        The channel ids that should not be affected by the rule.
    exempt_roles: List[:class:`Role`]
        The roles that should not be affected by the rule, if found in cache.
    exempt_channels: List[:class:`abc.GuildChannel`]
        The channels that should not be affected by the rule, if found in cache.
    """

    __slots__ = (
        "_state",
        "id",
        "guild_id",
        "guild",
        "name",
        "creator_id",
        "creator",
        "event_type",
        "trigger_type",
        "trigger_metadata",
        "actions",
        "enabled",
        "exempt_role_ids",
        "exempt_channel_ids",
        "exempt_roles",
        "exempt_channels",
    )

    def __init__(self, *, data: AutoModerationRulePayload, state: ConnectionState):
        self._state = state
        self.id = int(data["id"])
        self.guild_id = int(data["guild_id"])
        self.guild = state._get_guild(self.guild_id)
        self.name = data["name"]
        self.creator_id = int(data["creator_id"])
        self.creator = self.guild.get_member(self.creator_id) if self.guild is not None else None
        self.event_type = try_enum(AutoModerationEventType, data["event_type"])
        self.trigger_type = try_enum(AutoModerationTriggerType, data["trigger_type"])
        self.trigger_metadata = AutoModerationTriggerMetadata.from_data(data["trigger_metadata"])
        self.actions = [AutoModerationAction(data=action) for action in data["actions"]]
        self.enabled = data["enabled"]
        self.exempt_role_ids = [int(role_id) for role_id in data["exempt_roles"]]
        self.exempt_channel_ids = [int(channel_id) for channel_id in data["exempt_channels"]]
        self.exempt_roles = (
            [self.guild.get_role(role_id) for role_id in self.exempt_role_ids]
            if self.guild is not None
            else []
        )
        self.exempt_channels = (
            [self.guild.get_channel(channel_id) for channel_id in self.exempt_channel_ids]
            if self.guild is not None
            else []
        )

    def __str__(self) -> str:
        return self.name
