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
        AutoModerationAction as AutoModerationActionPayload,
        AutoModerationRule as AutoModerationRulePayload,
        TriggerMetadata as TriggerMetadataPayload,
        AutoModerationActionExecution as AutoModerationActionExecutionPayload
    )
    from .message import Message


__all__ = ("AutoModerationRule", "AutoModerationAction", "AutoModerationActionExecution")

class AutoModerationActionExecution:
    """Represent the payload that is sent when an auto moderation rule was triggered and the action was triggered.

    .. versionadded:: 2.1

    Attributes
    -----------
    guild_id: int
        The ID of the guild where the auto moderation action was triggered.
    guild: :class:`Guild`
        The guild where the auto moderation action was triggered.
    action: :class:`AutoModerationRuleAction`
        The auto moderation action associated with this execution.
    rule_id: :class:`int`
        The auto moderation rule associated with this execution's ID.
    trigger_type :class:`TriggerType`
        The trigger type of this execution.
    member_id: :class:`int`
        The user that triggered this execution's ID.
    channel_id: Optional[:class:`int`]
        The ID of the channel that was executed.
    message_id: Optional[:class:`int`]
        The ID of the message that triggered the action. ``None`` if the message was blocked by AutoMod.
    alert_message_id: Optional[:class:`int`]
        The system's alert message ID. ``None`` if not configured.
    content: :class:`str`
        The full content of the <?> that triggered this execution.
    matched_keyword: :class:`str`
        The keyword that matched the violated content.
    matched_content: :class:`str`
        The content that triggered this execution. `""` if :attr:`Intents.message_content` is not enabled.
    """
    # TODO: fix docstring in the <?> if you're reading this pls suggest smth, it can be something rather than msg.
    __slots__ = (
        "guild_id",
        "guild",
        "_state",
        "action",
        "rule_id",
        "trigger_type",
        "member_id",
        "channel_id",
        "message_id",
        "alert_message_id",
        "content",
        "matched_keyword",
        "matched_content"
    )
    def __init__(self, state: ConnectionState, guild: Guild, data: AutoModerationActionExecutionPayload):
        self.guild: Guild = guild
        self._state: ConnectionState = state
        self.guild_id: int = int(data['guild_id'])
        self.action: AutoModerationAction = AutoModerationAction(data=data['action'], guild=guild, state=state)
        self.rule_id: int = int(data['rule_id'])
        self.trigger_type: TriggerType = try_enum(TriggerType, data['rule_trigger_type'])
        self.member_id: int = int(data['user_id'])
        self.channel_id: Optional[int] = int(data.get("channel_id")) if "channel_id" in data else None
        self.message_id: Optional[int] = int(data['message_id']) if "message_id" in data else None
        self.alert_message_id: Optional[int] = int(data['alert_system_message_id']) if "alert_system_message_id" in data else None
        self.content: str = data['content']
        self.matched_keyword: str = data['matched_keyword']
        self.matched_content: str = data['matched_content']

    @property
    def channel(self) -> Optional[GuildChannel]:
        """Optional[:class:`abc.GuildChannel`] The channel that the content that triggered this execution is in."""
        return self.guild.get_channel(self.channel_id)

    @property
    def member(self) -> Optional[Member]:
        """Optional[:class:`Member`:] The member that triggered this execution."""
        return self.guild.get_member(self.member_id)

    async def fetch_member(self) -> Member:
        """
        Retrieves the member that triggered this execution from Discord.

        Returns
        --------
        :class:`Member`
            The member triggered this execution.

        Raises
        -------
        HTTPException
            Fetching the member failed.
        Forbidden
            You do not have access to the guild where this member is in.
        NotFound
            The member wasn't found.
        """
        return await self.guild.fetch_member(self.member_id)

    async def fetch_channel(self) -> GuildChannel:
        """
        Retrieves the channel that the content that triggered this rule is in from Discord.

        Returns
        --------
        :class:`abc.GuildChannel`
            The channel that the content that triggered this rule is in.

        Raises
        -------
        HTTPException
            Fetching the channel failed.
        Forbidden
            You're not a member of the guild that this execution was executed.
        """
        return await self.guild.fetch_channel(self.channel_id)

    async def fetch_alert_message(self) -> Optional[Message]:
        """
        Retrieves the system alert message associated with this execution.

        Returns
        -------
        Optional[:class:`Message`]
            The system alert message, or ``None`` if not configured.

        Raises
        -------
        HTTPException
            Fetching the message failed.
        Forbidden
            You do not have proper permissions to do this.
        """
        return await self.channel.fetch_message(self.alert_message_id)


    async def fetch_message(self) -> Optional[Message]:
        """
        Retrieves the message that triggered this execution.

        Returns
        --------
        Optional[:class:`Message`]
            The message, or ``None`` if the message was automatically blocked by AutoMod.

        Raises
        -------
        HTTPException
            Fetching the message failed.
        Forbidden
            You don't have proper permissions to do this.
        NotFound
            The message wasn't found, i.e. deleted.
        """
        return await self.channel.fetch_message(self.message_id)

    async def fetch_rule(self) -> AutoModerationRule:
        """
        Retrieves this execution's associated rule's info from Discord.

        Requires :attr:`~Permissions.manage_guild`.

        Returns
        --------
        :class:`AutoModerationRule`
            The auto moderation rule.

        Raises
        -------
        Forbidden
            You don't have proper permissions to do this.
        HTTPException
            Fetching the rule failed.
        """
        return self._state.http.get_automod_rule(self.rule_id)





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
    guild: :class:`Guild`
        The guild that this auto moderation action's rule is in.
    """

    __slots__ = ("type", "notify_channel_id", "timeout_seconds", "guild")

    def __init__(self, data: AutoModerationActionPayload, guild: Guild):
        self.type: ActionType = try_enum(ActionType, data["type"])
        metadata = data.get("metadata", {})
        self.notify_channel_id: Optional[int] = (
            int(metadata.get("channel_id")) if metadata.get("channel_id") is not None else None
        )
        self.timeout_seconds: Optional[int] = metadata.get("duration_seconds")
        self.guild: Guild = guild

    def __repr__(self):
        return f"<AutoModerationAction type={self.type}, notify_channel_id={self.notify_channel_id}, timeout_seconds={self.timeout_seconds}, guild={self.guild}, rule={self.rule}>"

    @property
    def notify_channel(self) -> Optional[GuildChannel]:
        "Optional[:class:`abc.GuildChannel`]: The channel that the system message will send a notification in when this action is executed."
        return self.guild.get_channel(self.notify_channel_id) if self.notify_channel_id is not None else None




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
        The guild that this auto moderation rule is active in.
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
        The custom filters for this auto moderation rule. ``None`` if not set.
    presets: Optional[List[:class:`KeywordPresetType`]]
        The pre-set types of this auto moderation rule. ``None`` if not set.
    actions: List[:class:`AutoModerationAction`]
        The actions that this auto moderation rule will execute if triggered.
    """

    __slots__ = (
        "id",
        "guild",
        "_state",
        "guild_id",
        "name",
        "creator_id",
        "event_type",
        "trigger_type",
        "enabled",
        "exempt_role_ids",
        "exempt_channel_ids",
        "keyword_filters",
        "actions",
        "presets",
    )

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
        trigger_metadata: TriggerMetadataPayload = data["trigger_metadata"]
        self.keyword_filters: Optional[List[str]] = trigger_metadata.get("keyword_filter")
        self.actions: List[AutoModerationAction] = [
            AutoModerationAction(data=action, rule=self, guild=self.guild) for action in data["actions"]
        ]
        self.presets: Optional[List[KeywordPresetType]] = (
            [try_enum(KeywordPresetType, preset) for preset in trigger_metadata["presets"]]  # type: ignore
            if "presets" in trigger_metadata
            else None
        )

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

    async def fetch_creator(self) -> Member:
        """
        |coro|

        Retrieves the creator of this auto moderation rule from Discord.

        .. note::

            This method is an API call. If you have :attr:`Intents.members` and member cache enabled, consider :attr:`creator` instead.

        Returns
        --------
        :class:`Member`
            The creator of this rule.

        Raises
        -------
        Forbidden
            You do not have access to the guild that this auto moderation rule is in.
        HTTPException
            Fetching this member failed.
        """
        return await self.guild.fetch_member(self.creator_id)

    @property
    def exempt_roles(self) -> List[Role]:
        """List[:class:`Role`]: A list of roles that will not be affected by this rule. ``[]`` if not set."""
        return [self.guild.get_role(exempt_role_id) for exempt_role_id in self.exempt_role_ids]  # type: ignore # they can't be None.

    @property
    def exempt_channels(self) -> List[GuildChannel]:
        """List[:class:`GuildChannel`]: A list of channels that will not be affected by this rule. ``[]`` if not set."""
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
            Either this or ``presets`` must be passed.

            .. note::

                This will only work if the rule's ``trigger_type`` is :attr:`TriggerType.keyword`.
        presets: List[:class:`KeywordPresetType`]
            The keyword presets that the filter should match.
            Either this or ``keyword_filters` must be passed.

            .. note::

                This will only work if the rule's ``trigger_type`` is :attr:`TriggerType.keyword_presets`
        notify_channel: :class:`abc.GuildChannel`
            The channel that will receive the notification when this rule is triggered.
        timeout_seconds: :class:`int`
            The seconds to timeout the person that triggered this rule.

            .. note::

                To be able to set this you must have :attr:`~Permissions.moderate_members` permissions.
        block_message: :class:`bool`
            Whether or not this rule should block the message which triggered the rule.
        enabled: :class:`bool`
            Whether or not if this rule is enabled.
        exempt_roles: List[:class:`Role`]
            A list of roles that should not be affected by this rule.

            .. note::

                Bots are always not affected by any rule.
        exempt_channels: List[:class:`abc.GuildChannel`]
            A list of channels that should not be affected by this rule.

            .. note::

                Bots are always not affected by any rule.

        Raises
        -------
        InvalidArgument
            - You specified both ``keyword_filters`` and ``presets``.
            - You didn't specify either ``keyword_filters`` or ``presets``.
        HTTPException
            Editing the rule failed.
        Forbidden
            You do not have proper permissions to edit this rule.
        """
        payload = {}
        if name is not MISSING:
            payload["name"] = name

        if event_type is not MISSING:
            payload["event_type"] = event_type.value

        if keyword_filters is MISSING and presets is MISSING:
            raise InvalidArgument("Either keyword_filters or presets must be passed")

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

        if notify_channel is not MISSING and timeout_seconds is MISSING:
            payload["actions"].append({"type": 2, "metadata": {"channel_id": notify_channel.id}})
            for action in self.actions:
                if action.timeout_seconds is not None:
                    payload["actions"].append(
                        {"type": 3, "metadata": {"duration_seconds": action.timeout_seconds}}
                    )

        if timeout_seconds is not MISSING and notify_channel is MISSING:
            payload["actions"].append(
                {"type": 3, "metadata": {"duration_seconds": timeout_seconds}}
            )
            for action in self.actions:
                if action.notify_channel_id is not None:
                    payload["actions"].append(
                        {"type": 2, "metadata": {"channel_id": action.notify_channel_id}}
                    )

        if timeout_seconds is not MISSING and notify_channel is not MISSING:
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

        new_data = await self._state.http.modify_automod_rule(
            guild_id=self.guild.id, rule_id=self.id, **payload
        )

        rule = self._state.add_automod_rule(data=new_data)
        return rule

    @property
    def created_at(self) -> datetime:
        """:class:`~datetime.datetime`: The time when this rule was created."""
        return snowflake_time(self.id)
