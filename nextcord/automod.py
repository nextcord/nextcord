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

from typing import TYPE_CHECKING, overload

from .enums import ActionType, EventType, KeywordPresetType, TriggerType, try_enum
from .mixins import Hashable
from .utils import MISSING, snowflake_time

if TYPE_CHECKING:
    from datetime import datetime
    from typing import List, Optional, Union

    from .abc import GuildChannel
    from .errors import InvalidArgument
    from .guild import Guild
    from .member import Member
    from .role import Role
    from .state import ConnectionState
    from .types.automod import (
        AutoModerationAction as AutoModerationActionPayload,
        AutoModerationRule as AutoModerationRulePayload,
        TriggerMetadata as TriggerMetadataPayload,
    )
    from .types.snowflake import Snowflake


__all__ = ("AutoModerationRule", "AutoModerationAction")


class AutoModerationAction:
    """Represents an auto moderation action.

    Attributes
    -----------
    type: :class:`ActionType`
        The action type of this action.
    notify_channel_id: Optional[:class:`int`]
        The ID of the channel that this action will notify in.
    timeout_seconds: Optional[:class:`int`]
        The number of seconds this rule should timeout when someone triggered the rule.
    """

    def __init__(self, data: AutoModerationActionPayload):
        self.type: ActionType = try_enum(ActionType, data["type"])
        metadata = data.get("metadata", {})
        self.notify_channel_id: Optional[int] = (
            int(metadata.get("channel_id")) if metadata.get("channel_id") is not None else None
        )
        self.timeout_seconds: Optional[int] = metadata.get("duration_seconds")

    def __repr__(self):
        return f"<AutoModerationAction type={self.type}, notify_channel_id={self.notify_channel_id}, timeout_seconds={self.timeout_seconds}>"


class AutoModerationRule(Hashable):
    """Represents an auto moderation rule.

    .. container:: operations
        .. describe:: x == y
            Check if two auto moderation rules are equal.
        .. describe:: x != y
            Check if two auto moderation rules are not equal.

    Attributes
    -----------
    id: :class:`int`
        The auto moderation rule's ID.
    guild: :class:`Guild`
        The guild that this auto moderation rule active in.
    name: :class:`str`
        The name of this auto moderation rule.
    event_type: :class:`EventType`
        The type of the event that the rule should execute when this event is called.
    trigger_type: :class:`TriggerType`
        The trigger type of this auto moderation rule.
    guild_id: :class:`int`
        The guild ID that this auto moderation rule is active in.
    creator_id: :class:`int`
        The creator of this auto moderation rule's ID.
    enabled: :class:`bool`
        Whether this rule is enabled or not.
    exempt_role_ids: List[:class:`int`]
        A list of roles that will not be affected by this rule.
        .. note::
            Bots are always not affected by any rule.
    exempt_channel_ids: List[:class:`int`]
        A list of channels that will not be affected by this rule.
    keyword_filters: Optional[List[:class:`str`]]
        The custom filters for this auto moderation rule. `None` if not set.
    presets: Optional[List[:class:`KeywordPresetType`]]
        The pre-set types of this auto moderation rule. `None` if not set.
    actions: List[:class:`AutoModerationAction`]
        The actions that this auto moderation rule will execute if triggered.
    """

    def __init__(self, *, state: ConnectionState, guild: Guild, data: AutoModerationRulePayload):
        self.id: int = int(data["id"])
        self.guild: Guild = guild
        self._state: ConnectionState = state
        self.guild_id: int = int(data["guild_id"])
        self.name: str = data["name"]
        self.creator_id: int = int(data["creator_id"])
        self.event_type: EventType = try_enum(EventType, data["event_type"])
        self.trigger_type: TriggerType = try_enum(TriggerType, data["trigger_type"])
        self.enabled: bool = data["enabled"]
        self.exempt_role_ids: List[int] = [int(exempt_role) for exempt_role in data["exempt_roles"]]
        self.exempt_channel_ids: List[int] = [
            int(exempt_channel) for exempt_channel in data["exempt_channels"]
        ]
        self.keyword_filters: Optional[List[str]] = None
        self.presets: Optional[List[KeywordPresetType]] = None

        trigger_metadata: TriggerMetadataPayload = data["trigger_metadata"]

        self.keyword_filters: Optional[List[str]] = trigger_metadata.get("keyword_filter")

        self.actions: List[AutoModerationAction] = []
        self.presets: Optional[List[KeywordPresetType]] = [try_enum(KeywordPresetType, preset) for preset in trigger_metadata["presets"]] if trigger_metadata.get("presets") is not None else None  # type: ignore

        for action in data["actions"]:
            self.actions.append(AutoModerationAction(data=action))

    def __repr__(self):
        attrs = (
            ("id", self.id),
            ("guild", self.guild),
            ("guild_id", self.guild_id),
            ("name", self.name),
            ("creator_id", self.creator_id),
            ("event_type", self.event_type),
            ("trigger_type", self.trigger_type),
            ("enabled", self.enabled),
            ("exempt_role_ids", self.exempt_role_ids),
            ("exempt_channel_ids", self.exempt_channel_ids),
            ("keyword_filters", self.keyword_filters),
            ("presets", self.presets),
            ("actions", self.actions),
        )
        inner = " ".join("%s=%r" % t for t in attrs)
        return f"<AutoModerationRule {inner}>"

    async def delete(self):
        """|coro|

        Delete this auto moderation rule.
        """
        await self._state.http.delete_automod_rule(guild_id=self.guild.id, rule_id=self.id)

    @property
    def creator(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member that created this rule."""
        return self.guild.get_member(self.creator_id)

    @property
    def exempt_roles(self) -> List[Role]:
        """List[:class:`Role`]: A list of roles that will not be affected by this rule. `[]` if not set."""
        return [self.guild.get_role(exempt_role_id) for exempt_role_id in self.exempt_role_ids]  # type: ignore # they can't be None.

    @property
    def exempt_channels(self) -> List[GuildChannel]:
        """List[:class:`GuildChannel`]: A list of channels that will not be affected by this rule. `[]` if not set."""
        return [self.guild.get_channel(exempt_channel_id) for exempt_channel_id in self.exempt_channel_ids]  # type: ignore # same

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        event_type: EventType = ...,
        keyword_filters: List[str] = ...,
        notify_channel: GuildChannel = ...,
        timeout_seconds: int = ...,
        block_message: bool = ...,
        enabled: bool = ...,
        exempt_roles: List[Role] = ...,
        exempt_channels: List[GuildChannel] = ...,
        reason: str = ...,
    ) -> AutoModerationRule:
        ...

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        event_type: EventType = ...,
        presets: List[KeywordPresetType] = ...,
        notify_channel: GuildChannel = ...,
        timeout_seconds: int = ...,
        block_message: bool = ...,
        enabled: bool = ...,
        exempt_roles: List[Role] = ...,
        exempt_channels: List[GuildChannel] = ...,
        reason: str = ...,
    ) -> AutoModerationRule:
        ...

    async def edit(
        self,
        *,
        name: str = MISSING,
        event_type: EventType = MISSING,
        keyword_filters: List[str] = MISSING,
        presets: List[KeywordPresetType] = MISSING,
        notify_channel: GuildChannel = MISSING,
        timeout_seconds: int = MISSING,
        block_message: bool = MISSING,
        enabled: bool = MISSING,
        exempt_roles: List[Role] = MISSING,
        exempt_channels: List[GuildChannel] = MISSING,
        reason: str = MISSING,
    ) -> AutoModerationRule:
        """|coro|

        Edit this auto moderation rule.

        You must have the :attr:`~Permissions.manage_guild` to be able to do this.

        Parameters
        -----------
        name: :class:`str`
            The new name of this auto moderation rule.
        event_type: :class:`EventType`
            The new trigger event type of this auto moderation rule.
        keyword_filters: List[:class:`str`]
            The keywords that the filter should match.

            .. note::

                This will only work if the rule's ``trigger_type`` is :attr:`TriggerType.keyword`.
        presets: List[:class:`KeywordPresetType`]
            The keyword presets that the filter should match.

            .. note::

                This will only work if the rule's ``trigger_type`` is :attr:`TriggerType.keyword_presets`
        notify_channel: :class:`abc.GuildChannel`
            The channel that will receive the notification when this rule is triggered. Cannot be mixed with ``notify_channels``.
        timeout_seconds: :class:`int`
            The seconds to timeout the person triggered this rule.
        block_message: :class:`bool`
            Whether or not this rule should block the message which triggered the rule.
        enabled: :class:`bool`
            Whether if this rule is enabled.
        exempt_roles: :class:`Role`
            A list of roles that should not be affected by this rule.
        exempt_channels: :class:`abc.GuildChannel`
            A list of channels that should not be affected by this rule.
        reason: :class:`str`
            The reason why is this auto moderation rule edited.

        Raises
        -------
        InvalidArgument
            You specified both ``keyword_filters`` and ``presets``.
        """
        payload = {}
        if name is not MISSING:
            payload["name"] = name

        if event_type is not MISSING:
            payload["event_type"] = event_type.value

        if keyword_filters is not MISSING and presets is not MISSING:
            raise InvalidArgument("Cannot pass keyword_filters and presets to edit()")

        if keyword_filters is not MISSING and self.trigger_type != TriggerType.keyword:
            raise InvalidArgument(
                "trigger_type must be TriggerType.keyword to pass keyword_filters"
            )

        if keyword_filters is not MISSING:
            payload["trigger_metadata"]["keyword_filter"] = keyword_filters

        if presets is not MISSING and self.trigger_type != TriggerType.keyword_presets:
            raise InvalidArgument(
                "trigger_type must be TriggerType.keyword_presets to pass presets"
            )

        if presets is not MISSING:
            payload["trigger_metadata"]["presets"] = [preset.value for preset in presets]

        if (
            notify_channel is not MISSING
            or timeout_seconds is not MISSING
            or block_message is not MISSING
        ):
            payload["actions"] = []
            if block_message is not MISSING:
                if block_message:
                    payload["actions"].append({"type": 1})
            else:
                for action in self.actions:
                    if action.type is ActionType.block:
                        payload["actions"].append({"type": 1})

        if (notify_channel is not MISSING) and (timeout_seconds is MISSING):
            payload["actions"].append({"type": 2, "metadata": {"channel_id": notify_channel.id}})
            for action in self.actions:
                if action.timeout_seconds is not None:
                    payload["actions"].append(
                        {"type": 3, "metadata": {"duration_seconds": action.timeout_seconds}}
                    )

        if (timeout_seconds is not MISSING) and (notify_channel is MISSING):
            payload["actions"].append(
                {"type": 3, "metadata": {"duration_seconds": timeout_seconds}}
            )
            for action in self.actions:
                if action.notify_channel_id is not None:
                    payload["actions"].append(
                        {"type": 2, "metadata": {"channel_id": notify_channel.id}}
                    )

        if (timeout_seconds is not MISSING) and (notify_channel is not MISSING):
            payload["actions"].append({"type": 2, "metadata": {"channel_id": notify_channel.id}})
            payload["actions"].append(
                {"type": 3, "metadata": {"duration_seconds": timeout_seconds}}
            )

        if enabled is not MISSING:
            payload["enabled"] = enabled

        if exempt_roles is not MISSING:
            payload["exempt_roles"] = [role.id for role in exempt_roles]

        if exempt_channels is not MISSING:
            payload["exempt_channels"] = [exempt_channel.id for exempt_channel in exempt_channels]

        if reason is not MISSING:
            payload["reason"] = reason

        new_data = await self._state.http.modify_automod_rule(
            guild_id=self.guild.id, rule_id=self.id, **payload
        )

        rule = self._state.add_automod_rule(data=new_data)
        return rule

    @property
    def created_at(self) -> datetime:
        """:class:`~datetime.datetime`: The time when this rule is created."""
        return snowflake_time(self.id)
