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

from typing import TYPE_CHECKING

from .enums import EventType, KeywordPresetType, TriggerType, try_enum
from .mixins import Hashable

if TYPE_CHECKING:
    from typing import List, Optional

    from .guild import Guild
    from .state import ConnectionState
    from .role import Role
    from .abc import MessageableChannel
    from .types.automod import (
        ActionMetadata as ActionMetadataPayload,
        AutoModerationRule as AutoModerationRulePayload,
        TriggerMetadata as TriggerMetadataPayload,
    )


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
    id :class:`int`
        The auto moderation rule's ID.
    guild :class:`Guild`
        The guild that this auto moderation rule active in.
    name :class:`str`
        The name of this auto moderation rule.
    event_type :class:`EventType`
        The type of the event that the rule should execute when this event is called.
    trigger_type :class:`TriggerType`
        The trigger type of this auto moderation rule.
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
        self.event_type: EventType = try_enum(
            EventType, data["event_type"]
        )
        self.trigger_type: TriggerType = try_enum(TriggerType, data["trigger_type"])  # same
        self.enabled: bool = data["enabled"]
        self.exempt_role_ids: List[int] = [
            int(exempt_role) for exempt_role in data["exempt_roles"]
        ]
        self.exempt_channel_ids: List[int] = [
            int(exempt_channel) for exempt_channel in data["exempt_channels"]
        ]
        self.notify_channel_id: Optional[int] = None
        self.filter: Optional[List[str]] = None
        self.timeout_seconds: int = 0
        self.preset_type: Optional[KeywordPresetType] = None

        self._unpack_trigger_metadata(data["trigger_metadata"])

        for action in data["actions"]:
            if action.get("metadata") is not None:
                self._unpack_action_metadata(action["metadata"])  # type: ignore -- last line already fixed it

    def _unpack_trigger_metadata(self, trigger_metadata: TriggerMetadataPayload):
        self.filter = trigger_metadata.get("keyword_filter")
        self.preset_type = try_enum(KeywordPresetType, trigger_metadata.get("presets"))

    def _unpack_action_metadata(self, action_metadata: ActionMetadataPayload):
        if action_metadata.get("channel_id") is not None:
            self.notify_channel_id = int(action_metadata.get("channel_id"))
        if action_metadata.get("duration_seconds") is not None:
            self.timeout_seconds: int = action_metadata.get("duration_seconds")  # type: ignore -- it was already fixed

    async def delete(self):
        await self._state.http.delete_automod_rule(guild_id=self.guild.id, rule_id=self.id)

    @property
    def creator(self):
        """Optional[:class:`Member`] The member that created this rule."""
        return self.guild.get_member(self.creator_id)
    
    @property
    def exempt_roles(self) -> List[Role]:
        return [self.guild.get_role(exempt_role_id) for exempt_role_id in self.exempt_role_ids]  # type: ignore -- they can't be None.
    
    @property
    def exempt_channels(self) -> List[MessageableChannel]:
        return [self.guild.get_channel(exempt_channel_id) for exempt_channel_id in self.exempt_channel_ids]  # type: ignore -- same

