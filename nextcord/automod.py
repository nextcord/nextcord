# TODO: add license
from __future__ import annotations

from typing import TYPE_CHECKING

from .enums import EventType, KeywordPresetType, TriggerType, try_enum
from .mixins import Hashable

if TYPE_CHECKING:
    from typing import List, Optional

    from .guild import Guild
    from .state import ConnectionState
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
        self.event_type = try_enum(
            EventType, data["event_type"]
        )  # left becuz idk what does it return so h
        self.trigger_type = try_enum(TriggerType, data["trigger_type"])  # same
        self.enabled: bool = data["enabled"]
        self.exempt_roles_ids: List[int] = [
            int(exempt_role) for exempt_role in data["exempt_roles"]
        ]
        self.exempt_channels_ids: List[int] = [
            int(exempt_channel) for exempt_channel in data["exempt_channels"]
        ]
        self.notify_channel_id: Optional[int] = None
        self.filter = None
        self.timeout_seconds = 0

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
