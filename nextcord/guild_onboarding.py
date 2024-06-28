# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .abc import Snowflake
from .enums import OnboardingMode, OnboardingPromptType, try_enum
from .mixins import Hashable
from .object import Object
from .partial_emoji import PartialEmoji

if TYPE_CHECKING:
    from .guild import Guild
    from .types.guild import (
        ModifiedOnboardingPrompt as ModifiedPromptPayload,
        ModifiedOnboardingPromptOption as ModifiedPromptOptionPayload,
        Onboarding as OnboardingPayload,
        OnboardingPrompt as PromptPayload,
        OnboardingPromptOption as PromptOptionPayload,
    )

__all__ = (
    "OnboardingPromptOption",
    "OnboardingPrompt",
    "Onboarding",
)


class OnboardingPromptOption(Hashable):
    """Represents an option in a guild's onboarding prompt.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: :class:`int`
        The option's ID.
    channels: List[:class:`int`]
        The list of channels that the member will be added to when the option is selected.
    roles: List[:class:`int`]
        The list of roles that the member will be assigned to when the option is selected.
    emoji: :class:`PartialEmoji`
        The option's emoji.
    title: :class:`str`
        The option's title.
    description: Optional[:class:`str`]
        The option's description.
    """

    __slots__ = (
        "id",
        "channels",
        "roles",
        "emoji",
        "title",
        "description",
    )

    def __init__(
        self,
        *,
        channels: List[Snowflake],
        roles: List[Snowflake],
        title: str,
        description: Optional[str] = None,
        emoji: Optional[PartialEmoji] = None,
    ) -> None:
        self.id: int = 0
        self.channels: List[Snowflake] = channels
        self.roles: List[Snowflake] = roles
        self.title: str = title
        self.description: Optional[str] = description
        self.emoji: Optional[PartialEmoji] = emoji

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} channels={self.channels} roles={self.roles} title={self.title}>"

    @classmethod
    def from_dict(cls, data: PromptOptionPayload) -> OnboardingPromptOption:
        channels: List[Snowflake] = [Object(id=o) for o in data["channel_ids"]]
        roles: List[Snowflake] = [Object(id=o) for o in data["channel_ids"]]
        title: str = data["title"]
        description: Optional[str] = data.get("description")
        raw_emoji = data.get("emoji")
        emoji: Optional[PartialEmoji] = (
            PartialEmoji.from_dict(raw_emoji) if raw_emoji is not None else None
        )

        self = cls(
            channels=channels, roles=roles, title=title, description=description, emoji=emoji
        )
        self.id = int(data["id"])
        return self

    def to_dict(self) -> ModifiedPromptOptionPayload:
        ret: ModifiedPromptOptionPayload = {
            "id": self.id,
            "channel_ids": [o.id for o in self.channels],
            "role_ids": [o.id for o in self.roles],
            "title": self.title,
            "description": self.description,
        }

        if self.emoji is not None:
            ret["emoji_id"] = self.emoji.id
            ret["emoji_name"] = self.emoji.name
            ret["emoji_animated"] = self.emoji.animated

        return ret


class OnboardingPrompt(Hashable):
    """Represents a prompt for a guild's onboarding screen.

    .. versionadded:: 3.0

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

    def __init__(
        self,
        *,
        type: OnboardingPromptType,
        options: List[OnboardingPromptOption],
        title: str,
        single_select: bool,
        required: bool,
        in_onboarding: bool,
    ) -> None:
        self.id: int = 0
        self.type: OnboardingPromptType = type
        self.options: List[OnboardingPromptOption] = options
        self.title: str = title
        self.single_select: bool = single_select
        self.required: bool = required
        self.in_onboarding: bool = in_onboarding

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} type={self.type} title={self.title}>"

    @classmethod
    def from_dict(cls, data: PromptPayload) -> OnboardingPrompt:
        type = try_enum(OnboardingPromptType, data["type"])
        options = [OnboardingPromptOption.from_dict(o) for o in data["options"]]
        title = data["title"]
        single_select = bool(data["single_select"])
        required = bool(data["required"])
        in_onboarding = bool(data["in_onboarding"])

        self = cls(
            type=type,
            options=options,
            title=title,
            single_select=single_select,
            required=required,
            in_onboarding=in_onboarding,
        )
        self.id = int(data["id"])
        return self

    def to_dict(self) -> ModifiedPromptPayload:
        return {
            "id": self.id,
            "type": self.type.value,
            "options": [o.to_dict() for o in self.options],
            "title": self.title,
            "single_select": self.single_select,
            "required": self.required,
            "in_onboarding": self.in_onboarding,
        }


class Onboarding:
    """Represents the onboarding screen for a guild.

    .. versionadded:: 3.0

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
        self.prompts: List[OnboardingPrompt] = [
            OnboardingPrompt.from_dict(p) for p in data["prompts"]
        ]
        self.default_channel_ids: list[int] = [int(c) for c in data["default_channel_ids"]]
        self.enabled: bool = bool(data["enabled"])
        self.mode: OnboardingMode = try_enum(OnboardingMode, data["mode"])

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} guild={self.guild} mode={self.mode} prompts={self.prompts}>"
