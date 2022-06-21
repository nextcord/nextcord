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
    from typing import List, Optional

    from .abc import GuildChannel
    from .errors import InvalidArgument
    from .guild import Guild
    from .member import Member
    from .role import Role
    from .state import ConnectionState
    from .types.automod import (
        ActionMetadata as ActionMetadataPayload,
        AutoModerationAction as AutoModerationActionPayload,
        AutoModerationRule as AutoModerationRulePayload,
        TriggerMetadata as TriggerMetadataPayload,
    )


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
        self.notify_channel_id: Optional[int] = None
        self.timeout_seconds: Optional[int] = None
        if data.get("metadata"):
            self._unpack_metadata(data["metadata"])  # type: ignore

    def __repr__(self):
        attrs = (
            ("type", self.type),
            ("notify_channel_id", self.notify_channel_id),
            ("timeout_seconds", self.timeout_seconds),
        )
        inner = " ".join("%s=%r" % t for t in attrs)
        return f"<AutoModerationAction {inner}>"

    def _unpack_metadata(self, action_metadata: ActionMetadataPayload):

        if action_metadata.get("channel_id") is not None:
            self.notify_channel_id: Optional[int] = int(action_metadata.get("channel_id"))
        if action_metadata.get("duration_seconds") is not None:
            self.timeout_seconds: Optional[int] = action_metadata.get("duration_seconds")


class AutoModerationRule(Hashable):
    """Represents an auto moderation rule.

    .. container:: operations
        .. describe:: x == y
            Check if two auto moderation rule are equal.
        .. describe:: x != y
            Check if two auto moderation rule are not equal.

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
        Whether is this rule enabled or not.
    exempt_role_ids: List[:class:`int`]
        A list of roles that will not be affected by this rule.
        .. note::
            Bots are always not affected by any rule.
    exempt_channel_ids: List[:class:`int`]
        A list of channels that will not be affected by this rule.
    keyword_filters: Optional[List[str]]
        The custom filter for this auto moderation rule. `None` if not set.
    presets: Optional[List[:class:`KeywordPresetType`]]
        The pre-set type of this auto moderation rule. `None` if not set.
    actions: List[:class:`AutoModerationAction`]
        The actions that this auto moderation rule will execute if triggered.
    """

    def __init__(self, *, state: ConnectionState, guild: Guild, data: AutoModerationRulePayload):
        self.id: int = int(data["id"])
        self.guild: Guild = guild
        self._state: ConnectionState = state
        self._from_payload(data)

    def __int__(self):
        return self.id

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

    def _from_payload(self, data: AutoModerationRulePayload):
        self.guild_id: int = int(data["guild_id"])
        self.name: str = data["name"]
        self.creator_id: int = int(data["creator_id"])
        self.event_type: EventType = try_enum(EventType, data["event_type"])
        self.trigger_type: TriggerType = try_enum(TriggerType, data["trigger_type"])  # same
        self.enabled: bool = data["enabled"]
        self.exempt_role_ids: List[int] = [int(exempt_role) for exempt_role in data["exempt_roles"]]
        self.exempt_channel_ids: List[int] = [
            int(exempt_channel) for exempt_channel in data["exempt_channels"]
        ]
        self.keyword_filters: Optional[List[str]] = None
        self.presets: Optional[List[KeywordPresetType]] = None

        self._unpack_trigger_metadata(data["trigger_metadata"])
        self.actions: List[AutoModerationAction] = []

        for action in data["actions"]:
            self.actions.append(AutoModerationAction(data=action))

    def _unpack_trigger_metadata(self, trigger_metadata: TriggerMetadataPayload):
        if trigger_metadata.get("keyword_filter") is not None:
            self.keyword_filters = trigger_metadata["keyword_filter"]  # type: ignore
        if trigger_metadata.get("presets") is not None:
            self.presets = [try_enum(KeywordPresetType, preset) for preset in trigger_metadata["presets"]]  # type: ignore -- pylint messed up somehow

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
        """List[:class:`Role`]: A list of role that will not be affected by this rule. `[]` if not set."""
        return [self.guild.get_role(exempt_role_id) for exempt_role_id in self.exempt_role_ids]  # type: ignore -- they can't be None.

    @property
    def exempt_channels(self) -> List[GuildChannel]:
        """List[:class:`GuildChannel`]: A list of channels that will not be affected by this rule. `[]` if not set."""
        return [self.guild.get_channel(exempt_channel_id) for exempt_channel_id in self.exempt_channel_ids]  # type: ignore -- same

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        event_type: EventType = ...,
        keyword_filters: List[str] = ...,
        notify_channel: GuildChannel = ...,
        timeout_seconds: int = ...,
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

                This will only work if the rule's ``trigger_type`` is :attr:`TriggerType.keyword_preset`
        notify_channel: :class:`abc.GuildChannel`
            The channel that will receive the notification when this rule is triggered. Cannot be mixed with ``notify_channels``.
        timeout_seconds: :class:`int`
            The seconds to timeout the person triggered this rule.
        enabled: :class:`bool`
            Whether if this rule is enabled.
        exempt_roles: :class:`Role`
            A list of roles that should not be affected by this rule.
        exempt_channels: :class:`abc.GuildChannel`
            A list of channels that should not be affected by this rule.
        reason: :class:`str`
            The reason why is this auto moderation rule edited.
        """
        payload = {}
        if name is not MISSING:
            payload["name"] = name

        if event_type is not MISSING:
            payload["event_type"] = event_type

        if keyword_filters is not MISSING and self.trigger_type != TriggerType.keyword:
            raise InvalidArgument(
                "trigger_type must be TriggerType.keyword to pass keyword_filters"
            )

        if keyword_filters is not MISSING:
            payload["trigger_metadata"]["keyword_filters"] = keyword_filters

        if presets is not MISSING and self.trigger_type != TriggerType.keyword_preset:
            raise InvalidArgument("trigger_type must be TriggerType.keyword_preset to pass presets")

        if presets is not MISSING:
            payload["trigger_metadata"]["presets"] = presets

        if notify_channel is not MISSING or timeout_seconds is not MISSING:
            payload["actions"] = []

        if notify_channel is not MISSING and timeout_seconds is MISSING:
            payload["actions"].append(
                {"type": 1, "notify_channel_id": notify_channel.id}
            )

        if timeout_seconds is not MISSING and notify_channel is MISSING:
            payload["actions"].append({"type": 2, "timeout_seconds": timeout_seconds})

        if timeout_seconds is not MISSING and notify_channel is not MISSING:
            payload["actions"].append(
                {"type": 1, "notify_channel_id": notify_channel.id}
            )
            payload["actions"].append({"type": 2, "duration_seconds": timeout_seconds})

        if enabled is not MISSING:
            payload["enabled"] = enabled

        if exempt_roles is not MISSING:
            payload["exempt_roles"] = [role.id for role in exempt_roles]

        if exempt_channels is not MISSING:
            payload["exempt_channels"] = [
                exempt_channel.id for exempt_channel in exempt_channels
            ]

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
