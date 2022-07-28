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
from .errors import InvalidArgument
from .mixins import Hashable
from .object import Object
from .utils import MISSING, _get_as_snowflake

if TYPE_CHECKING:
    from .abc import GuildChannel, Snowflake
    from .guild import Guild
    from .member import Member
    from .message import Message
    from .role import Role
    from .state import ConnectionState
    from .types.auto_moderation import (
        AutoModerationAction as AutoModerationActionPayload,
        AutoModerationActionExecution as ActionExecutionPayload,
        AutoModerationActionMetadata as ActionMetadataPayload,
        AutoModerationRule as AutoModerationRulePayload,
        AutoModerationRuleModify,
        AutoModerationTriggerMetadata as TriggerMetadataPayload,
    )

__all__ = (
    "AutoModerationTriggerMetadata",
    "AutoModerationActionMetadata",
    "AutoModerationAction",
    "AutoModerationRule",
    "AutoModerationActionExecution",
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
    allow_list: List[:class:`str`]
        A list of exempt strings that will not trigger the preset type.

        .. note::

            This is ``None`` and cannot be provided if the trigger type of the rule is not
            :attr:`AutoModerationTriggerType.keyword_preset`.

        .. warning::

            Wildcard syntax (`*`) is not supported here.
    """

    __slots__ = ("keyword_filter", "presets", "allow_list")

    def __init__(
        self,
        *,
        keyword_filter: Optional[List[str]] = None,
        presets: Optional[List[KeywordPresetType]] = None,
        allow_list: Optional[List[str]] = None,
    ) -> None:
        self.keyword_filter: Optional[List[str]] = keyword_filter
        self.presets: Optional[List[KeywordPresetType]] = presets
        self.allow_list: Optional[List[str]] = allow_list

    @classmethod
    def from_data(cls, data: TriggerMetadataPayload):
        keyword_filter = data.get("keyword_filter")
        presets = (
            [try_enum(KeywordPresetType, preset) for preset in data["presets"]]
            if "presets" in data
            else None
        )
        allow_list = data.get("allow_list")

        return cls(keyword_filter=keyword_filter, presets=presets, allow_list=allow_list)

    @property
    def payload(self) -> TriggerMetadataPayload:
        payload: TriggerMetadataPayload = {}

        if self.keyword_filter is not None:
            payload["keyword_filter"] = self.keyword_filter

        if self.presets is not None:
            payload["presets"] = [enum.value for enum in self.presets]

        if self.allow_list is not None:
            payload["allow_list"] = self.allow_list

        return payload


class AutoModerationActionMetadata:
    """Represents additional data that is used when an action is executed.

    .. versionadded:: 2.1

    Attributes
    ----------
    channel: Optional[:class:`abc.Snowflake`]
        The channel to which message content should be logged.

        .. note::

            This is ``None`` and cannot be provided if the action type of the rule is not
            :attr:`AutoModerationActionType.send_alert_message`.
    duration_seconds: Optional[:class:`int`]
        The duration of the timeout in seconds.

        .. note::

            This is ``None`` and cannot be provided if the action type of the rule is not
            :attr:`AutoModerationActionType.timeout`.

        .. note::

            The maximum value that can be used is `2419200` seconds (4 weeks)
    """

    __slots__ = ("channel_id", "duration_seconds")

    def __init__(
        self, *, channel: Optional[Snowflake] = None, duration_seconds: Optional[int] = None
    ):
        self.channel_id: Optional[int] = channel.id if channel is not None else None
        self.duration_seconds: Optional[int] = duration_seconds

    @classmethod
    def from_data(cls, data: ActionMetadataPayload):
        channel_id = _get_as_snowflake(data, "channel_id")
        channel = Object(id=channel_id) if channel_id is not None else None
        duration_seconds = data.get("duration_seconds")

        return cls(channel=channel, duration_seconds=duration_seconds)

    @property
    def payload(self) -> ActionMetadataPayload:
        payload: ActionMetadataPayload = {}

        if self.channel_id is not None:
            payload["channel_id"] = self.channel_id

        if self.duration_seconds is not None:
            payload["duration_seconds"] = self.duration_seconds

        return payload


class AutoModerationAction:
    """Represents an auto moderation action that will execute whenever a rule is triggered.

    .. versionadded:: 2.1

    Parameters
    ----------
    type: :class:`AutoModerationActionType`
        The type to use for this action.
    metadata: :class:`AutoModerationActionMetadata`
        The additional data to use during execution of this action.

    Attributes
    ----------
    type: :class:`AutoModerationActionType`
        The type of this action.
    metadata: :class:`AutoModerationActionMetadata`
        The additional metadata needed during execution for this specific action type.
    """

    __slots__ = ("type", "metadata")

    def __init__(
        self,
        *,
        type: AutoModerationActionType,
        metadata: Optional[AutoModerationActionMetadata] = None,
    ) -> None:
        self.type: AutoModerationActionType = type
        self.metadata: Optional[AutoModerationActionMetadata] = metadata

    @classmethod
    def from_data(cls, data: AutoModerationActionPayload) -> AutoModerationAction:
        type = try_enum(AutoModerationActionType, data["type"])
        metadata = AutoModerationActionMetadata.from_data(data.get("metadata", {}))
        return cls(type=type, metadata=metadata)

    @property
    def payload(self) -> AutoModerationActionPayload:
        data: AutoModerationActionPayload = {
            "type": self.type.value,
        }

        if self.metadata is not None:
            data["metadata"] = self.metadata.payload

        return data


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
    creator: Optional[:class:`Member`]
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
        self.id: int = int(data["id"])
        self.guild_id: int = int(data["guild_id"])
        self.guild: Optional[Guild] = state._get_guild(self.guild_id)
        self.name: str = data["name"]
        self.creator_id: int = int(data["creator_id"])
        self.creator: Optional[Member] = (
            self.guild.get_member(self.creator_id) if self.guild is not None else None
        )
        self.event_type: AutoModerationEventType = try_enum(
            AutoModerationEventType, data["event_type"]
        )
        self.trigger_type: AutoModerationTriggerType = try_enum(
            AutoModerationTriggerType, data["trigger_type"]
        )
        self.trigger_metadata: AutoModerationTriggerMetadata = (
            AutoModerationTriggerMetadata.from_data(data["trigger_metadata"])
        )
        self.actions: List[AutoModerationAction] = [
            AutoModerationAction.from_data(data=action) for action in data["actions"]
        ]
        self.enabled: bool = data["enabled"]
        self.exempt_role_ids: List[int] = [int(role_id) for role_id in data["exempt_roles"]]
        self.exempt_channel_ids: List[int] = [
            int(channel_id) for channel_id in data["exempt_channels"]
        ]
        self.exempt_roles: List[Optional[Role]] = (
            [self.guild.get_role(role_id) for role_id in self.exempt_role_ids]
            if self.guild is not None
            else []
        )
        self.exempt_channels: List[Optional[GuildChannel]] = (
            [self.guild.get_channel(channel_id) for channel_id in self.exempt_channel_ids]
            if self.guild is not None
            else []
        )

    def __str__(self) -> str:
        return self.name

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Delete the current rule from its guild.

        Requires the :attr:`~Permissions.manage_guild` permission.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for deleting this rule. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have permission to delete this rule.
        HTTPException
            Deleting the rule failed.
        """

        await self._state.http.delete_auto_moderation_rule(self.guild_id, self.id, reason=reason)

    async def edit(
        self,
        *,
        name: str = MISSING,
        event_type: AutoModerationEventType = MISSING,
        trigger_metadata: AutoModerationTriggerMetadata = MISSING,
        actions: List[AutoModerationAction] = MISSING,
        enabled: bool = MISSING,
        exempt_roles: List[Snowflake] = MISSING,
        exempt_channels: List[Snowflake] = MISSING,
        reason: Optional[str] = None,
    ) -> AutoModerationRule:
        """Modify the current auto moderation rule.

        Requires the :attr:`~Permissions.manage_guild` permission.

        Parameters
        ----------
        name: :class:`str`
            The new name for this rule.
        event_type: :class:`AutoModerationEventType`
            The new event context in which this rule is checked.
        trigger_metadata: :class:`AutoModerationTriggerMetadata`
            The new additional data that is used when checking if this rule is triggered.
        actions: List[:class:`AutoModerationAction`]
            The new actions which will execute when the rule is triggered.
        enabled: :class:`bool`
            Whether the rule is enabled.
        exempt_roles: List[:class:`abc.Snowflake`]
            The new roles that should not be affected by the rule.
        exempt_channels: List[:class:`abc.Snowflake`]
            The new channels that should not be affected by the rule.
        reason: Optional[:class:`str`]
            The reason for editing this rule. Shows in the audit log.

        Raises
        ------
        Forbidden
            You do not have permission to edit this rule.
        HTTPException
            Editing the rule failed.
        InvalidArgument
            An incorrect type was passed.

        Returns
        -------
        :class:`AutoModerationRule`
            The newly edited auto moderation rule.
        """

        payload: AutoModerationRuleModify = {}

        if name is not MISSING:
            payload["name"] = name

        if event_type is not MISSING:
            if not isinstance(event_type, AutoModerationEventType):
                raise InvalidArgument("event_type must be of type AutoModerationEventType")

            payload["event_type"] = event_type.value

        if trigger_metadata is not MISSING:
            if not isinstance(trigger_metadata, AutoModerationTriggerMetadata):
                raise InvalidArgument(
                    "trigger_metadata must be of type AutoModerationTriggerMetadata"
                )

            payload["trigger_metadata"] = trigger_metadata.payload

        if actions is not MISSING:
            payload["actions"] = [action.payload for action in actions]

        if enabled is not MISSING:
            payload["enabled"] = enabled

        if exempt_roles is not MISSING:
            payload["exempt_roles"] = [str(role.id) for role in exempt_roles]

        if exempt_channels is not MISSING:
            payload["exempt_channels"] = [str(channel.id) for channel in exempt_channels]

        data = await self._state.http.modify_auto_moderation_rule(
            self.guild_id, self.id, data=payload, reason=reason
        )
        return AutoModerationRule(data=data, state=self._state)


class AutoModerationActionExecution:
    """Represents the execution of an auto moderation action

    .. versionadded:: 2.1

    Attributes
    ----------
    guild_id: :class:`int`
        The guild ID where this action was executed.
    guild: Optional[:class:`Guild`]
        The guild where this action was executed, if it was found in cache.
    channel_id: Optional[:class:`int`]
        The channel ID where this action was executed, if applicable.
    channel: Optional[:class:`abc.GuildChannel`]
        The channel where this action was executed, if applicable and found in cache.
    message_id: Optional[:class:`int`]
        The message ID that executed this action, if it was not blocked.
    message: Optional[:class:`Message`]
        The message that executed this action, if it was not blocked and found in cache.
    alert_system_message_id: Optional[:class:`int`]
        The ID of the system alert message, if sent.
    alert_system_message: Optional[:class:`Message`]
        The system alert message, if sent and found in cache.
    action: :class:`AutoModerationAction`
        The action that was executed.
    rule_id: :class:`int`
        The id of the rule that was executed.
    rule_trigger_type: :class:`AutoModerationTriggerType`
        The type of rule that was executed.
    member_id: :class:`int`
        The ID of the user that triggered this action.
    member: Optional[:class:`Member`]
        The member that triggered this action, if found in cache.
    content: :class:`str`
        The content the user sent in the message

        .. note::

            This requires :attr:`Intents.message_content` to not be empty.
    matched_keyword: Optional[:class:`str`]
        The keyword configured in the rule that matched this message, if applicable.
    matched_content: Optional[:class:`str`]
        The content in the message that matched the keyword, if applicable.

        .. note::

            This requires :attr:`Intents.message_conrent` to not be empty.
    """

    def __init__(self, *, data: ActionExecutionPayload, state: ConnectionState) -> None:
        self.guild_id: int = int(data["guild_id"])
        self.guild: Optional[Guild] = state._get_guild(self.guild_id)
        self.channel_id: Optional[int] = _get_as_snowflake(data, "channel_id")
        if self.guild is not None and self.channel_id is not None:
            self.channel: Optional[GuildChannel] = self.guild.get_channel(self.channel_id)
        else:
            self.channel: Optional[GuildChannel] = None
        self.message_id: Optional[int] = _get_as_snowflake(data, "message_id")
        self.message: Optional[Message] = state._get_message(self.message_id)
        self.alert_system_message_id: Optional[int] = _get_as_snowflake(
            data, "alert_system_message_id"
        )
        self.alert_system_message: Optional[Message] = state._get_message(
            self.alert_system_message_id
        )
        self.action: AutoModerationAction = AutoModerationAction.from_data(data=data["action"])
        self.rule_id: int = int(data["rule_id"])
        self.rule_trigger_type: AutoModerationTriggerType = try_enum(
            AutoModerationTriggerType, data["rule_trigger_type"]
        )
        self.member_id: int = int(data["user_id"])
        self.member: Optional[Member] = (
            self.guild.get_member(self.member_id) if self.guild is not None else None
        )
        self.content: str = data.get("content", "")
        self.matched_keyword: Optional[str] = data["matched_keyword"]
        self.matched_content: Optional[str] = data.get("matched_content", "")
