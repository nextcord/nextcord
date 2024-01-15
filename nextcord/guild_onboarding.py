# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .enums import OnboardingMode, OnboardingPromptType, try_enum
from .partial_emoji import PartialEmoji

if TYPE_CHECKING:
    from .guild import Guild
    from .types.guild import (
        Onboarding as OnboardingPayload,
        OnboardingPrompt as OnboardingPromptPayload,
        OnboardingPromptOption as PromptOptionPayload,
    )

__all__ = (
    "OnboardingPromptOption",
    "OnboardingPrompt",
    "Onboarding",
)


class OnboardingPromptOption:
    """Represents an option in a guild's onboarding prompt.

    Attributes
    ----------
    id: :class:`int`
        The option's ID.
    channel_ids: List[:class:`int`]
        The IDs of the channels that the member will be added to when the option is selected.
    role_ids: List[:class:`int`]
        The IDs of the roles that the member will be assigned to when the option is selected.
    emoji: :class:`PartialEmoji`
        The option's emoji.
    title: :class:`str`
        The option's title.
    description: Optional[:class:`str`]
        The option's description.
    """

    __slots__ = (
        "id",
        "channel_ids",
        "role_ids",
        "emoji",
        "title",
        "description",
    )

    def __init__(self, *, data: PromptOptionPayload) -> None:
        self.id: int = int(data["id"])
        self.channel_ids: List[int] = [int(c) for c in data["channel_ids"]]
        self.role_ids: List[int] = [int(r) for r in data["role_ids"]]
        self.emoji: PartialEmoji = PartialEmoji.from_dict(data["emoji"])
        self.title: str = data["title"]
        self.description: Optional[str] = data.get("description")


class OnboardingPrompt:
    """Represents a prompt for a guild's onboarding screen.

    Attributes
    ----------
    id: :class:`int`
        The prompt's ID.
    type: :class:`OnboardingPromptType`
        The prompt's type.
    options: List[:class:`OnboardingPromptOption`]
        The prompt's options.
    title: :class:`str`
        The prompt's title.
    single_select: :class:`bool`
        Whether the user is restricted to selecting only one option.
    required: :class:`bool`
        Whether the prompt is required before a user completes the onboarding flow.
    in_onboarding: :class:`bool`
        Whether the prompt is present in the onboarding flow.
        If ``False``, the prompt will only appear in the Channels & Roles tab.
    """

    __slots__ = (
        "id",
        "type",
        "options",
        "title",
        "single_select",
        "required",
        "in_onboarding",
    )

    def __init__(self, *, data: OnboardingPromptPayload) -> None:
        self.id: int = int(data["id"])
        self.type: OnboardingPromptType = try_enum(OnboardingPromptType, data["type"])
        self.options: List[OnboardingPromptOption] = [
            OnboardingPromptOption(data=o) for o in data["options"]
        ]
        self.title: str = data["title"]
        self.single_select: bool = bool(data["single_select"])
        self.required: bool = bool(data["required"])
        self.in_onboarding: bool = bool(data["in_onboarding"])


class Onboarding:
    """Represents the onboarding screen for a guild.

    Attributes
    ----------
    guild: :class:`Guild`
        The guild this onboarding screen is on.
    guild_id: :class:`int`
        The ID of the guild this onboarding screen is on.
    prompts: List[:class:`OnboardingPrompt`]
        The screen's prompts.
    default_channel_ids: List[:class:`int`]
        The list of the IDs of channels that users are opted into immediately.
    enabled: :class:`bool`
        Whether this screen is enabled.
    mode: :class:`OnboardingMode`
        The criteria needed for onboarding to be enabled.
    """

    __slots__ = (
        "guild",
        "guild_id",
        "prompts",
        "default_channel_ids",
        "enabled",
        "mode",
    )

    def __init__(self, *, guild: Guild, data: OnboardingPayload) -> None:
        self.guild: Guild = guild
        self.guild_id: int = int(data["guild_id"])
        self.prompts: List[OnboardingPrompt] = [OnboardingPrompt(data=p) for p in data["prompts"]]
        self.default_channel_ids: list[int] = [int(c) for c in data["default_channel_ids"]]
        self.enabled: bool = bool(data["enabled"])
        self.mode: OnboardingMode = try_enum(OnboardingMode, data["mode"])