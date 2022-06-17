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

if TYPE_CHECKING:
    from typing import List, Optional

    from .abc import MessageableChannel
    from .guild import Guild
    from .role import Role
    from .state import ConnectionState
    from .utils import MISSING
    from .types.automod import (
        ActionMetadata as ActionMetadataPayload,
        AutoModerationAction as AutoModerationActionPayload,
        AutoModerationRule as AutoModerationRulePayload,
        TriggerMetadata as TriggerMetadataPayload,
    )


class AutoModerationAction:
    """
    Represent an auto moderation action.

    Attributes
    -----------
    type: :class:`ActionType`
        The action type of this action.
    notify_channel_id: Optional[:class:`int`]
        The ID of the channel that this action will notify in.
    timeout_seconds: Optional[:class:`int`]
        The number of seconds this rule should timeout when someone breaks."""

    def __init__(self, data: AutoModerationActionPayload):
        self.type: ActionType = try_enum(ActionType, data["type"])
        if data.get("metadata"):
            self._unpack_metadata(data["metadata"])  # type: ignore

    def _unpack_metadata(self, action_metadata: ActionMetadataPayload):
        if action_metadata.get("channel_id") is not None:
            self.notify_channel_id = int(action_metadata.get("channel_id"))
        if action_metadata.get("duration_seconds") is not None:
            self.timeout_seconds: int = action_metadata.get("duration_seconds")  # type: ignore -- it was already fixed


class AutoModerationRule(Hashable):
    """
    Represent an auto moderation rule.

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
        The guild ID that this auto moderation rule active in.
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
    filter: Optional[List[str]]
        The custom filter for this auto moderation rule. `None` if not set.
    preset_type: Optional[:class:`KeywordPresetType`]
        The pre-set type of this auto moderation rule. `None` if not set.
    actions: List[:class:`AutoModerationAction`]
        The actions that this auto moderation rule will execute if triggered.
    """

    def __init__(self, *, state: ConnectionState, guild: Guild, data: AutoModerationRulePayload):
        self.id = int(data["id"])
        self.guild: Guild = guild
        self._state: ConnectionState = state
        self._from_payload(data)

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
        self.filter: Optional[List[str]] = None
        self.preset_type: Optional[KeywordPresetType] = None

        self._unpack_trigger_metadata(data["trigger_metadata"])
        self.actions: List[AutoModerationAction] = []

        for action in data["actions"]:
            self.actions.append(AutoModerationAction(action))

    def _unpack_trigger_metadata(self, trigger_metadata: TriggerMetadataPayload):
        self.filter = trigger_metadata.get("keyword_filter")  
        self.preset_types = [try_enum(KeywordPresetType, preset) for preset in trigger_metadata['presets']]  # type: ignore -- pylint messed up somehow

    async def delete(self):
        await self._state.http.delete_automod_rule(guild_id=self.guild.id, rule_id=self.id)

    @property
    def creator(self):
        """Optional[:class:`Member`] The member that created this rule."""
        return self.guild.get_member(self.creator_id)

    async def fetch_creator(self):
        """Optional[:class:`Member`] Retrieves the member that created this rule through Discord's API.

        .. note::
            This method is an API call. If you have :attr:`Intents.members` and member cache enabled, consider :attr:`creator` instead."""

    @property
    def exempt_roles(self) -> List[Role]:
        """List[:class:`Role`]: A list of role that will not be affected by this rule. `[]` if not set."""
        return [self.guild.get_role(exempt_role_id) for exempt_role_id in self.exempt_role_ids]  # type: ignore -- they can't be None.

    @property
    def exempt_channels(self) -> List[MessageableChannel]:
        """List[:class:`MessageableChannel`]: A list of channels that will not be affected by this rule. `[]` if not set."""
        return [self.guild.get_channel(exempt_channel_id) for exempt_channel_id in self.exempt_channel_ids]  # type: ignore -- same
    