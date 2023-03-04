# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, List, Literal, Optional, Tuple, TypeVar, Union, cast

from .enums import ButtonStyle, ComponentType, TextInputStyle, try_enum
from .partial_emoji import PartialEmoji, _EmojiTag
from .utils import MISSING, get_slots

if TYPE_CHECKING:
    from typing_extensions import Self

    from .channel import ChannelType
    from .emoji import Emoji
    from .types.components import (
        ActionRow as ActionRowPayload,
        ButtonComponent as ButtonComponentPayload,
        ChannelSelectMenu as ChannelSelectMenuPayload,
        Component as ComponentPayload,
        MentionableSelectMenu as MentionableSelectMenuPayload,
        RoleSelectMenu as RoleSelectMenuPayload,
        SelectMenu as SelectMenuPayload,
        SelectMenuBase as SelectMenuBasePayload,
        SelectOption as SelectOptionPayload,
        TextInputComponent as TextInputComponentPayload,
        UserSelectMenu as UserSelectMenuPayload,
    )


__all__ = (
    "Component",
    "ActionRow",
    "Button",
    "SelectMenu",
    "SelectOption",
    "TextInput",
)

C = TypeVar("C", bound="Component")


class Component:
    """Represents a Discord Bot UI Kit Component.

    Currently, the only components supported by Discord are:

    - :class:`ActionRow`
    - :class:`Button`
    - :class:`SelectMenu`
    - :class:`TextInput`
    - :class:`UserSelectMenu`
    - :class:`ChannelSelectMenu`
    - :class:`RoleSelectMenu`
    - :class:`MentionableSelectMenu`

    This class is abstract and cannot be instantiated.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    """

    __slots__: Tuple[str, ...] = ("type",)

    __repr_info__: ClassVar[Tuple[str, ...]]
    type: ComponentType

    def __repr__(self) -> str:
        attrs = " ".join(f"{key}={getattr(self, key)!r}" for key in self.__repr_info__)
        return f"<{self.__class__.__name__} {attrs}>"

    @classmethod
    def _raw_construct(cls, **kwargs) -> Self:
        self = cls.__new__(cls)
        for slot in get_slots(cls):
            try:
                value = kwargs[slot]
            except KeyError:
                pass
            else:
                setattr(self, slot, value)
        return self

    def to_dict(self) -> ComponentPayload:
        raise NotImplementedError


class ActionRow(Component):
    """Represents a Discord Bot UI Kit Action Row.

    This is a component that holds up to 5 children components in a row.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    children: List[:class:`Component`]
        The children components that this holds, if any.
    """

    __slots__: Tuple[str, ...] = ("children",)

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ComponentPayload) -> None:
        self.type: ComponentType = try_enum(ComponentType, data["type"])
        self.children: List[Component] = [_component_factory(d) for d in data.get("components", [])]

    def to_dict(self) -> ActionRowPayload:
        return {
            "type": cast(Literal[1], int(self.type)),
            "components": [child.to_dict() for child in self.children],
        }


class Button(Component):
    """Represents a button from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a button is :class:`nextcord.ui.Button`
        not this one.

    .. versionadded:: 2.0

    Attributes
    ----------
    style: :class:`.ButtonStyle`
        The style of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        If this button is for a URL, it does not have a custom ID.
    url: Optional[:class:`str`]
        The URL this button sends you to.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    label: Optional[:class:`str`]
        The label of the button, if any.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji of the button, if available.
    """

    __slots__: Tuple[str, ...] = (
        "style",
        "custom_id",
        "url",
        "disabled",
        "label",
        "emoji",
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ButtonComponentPayload) -> None:
        self.type: ComponentType = try_enum(ComponentType, data["type"])
        self.style: ButtonStyle = try_enum(ButtonStyle, data["style"])
        self.custom_id: Optional[str] = data.get("custom_id")
        self.url: Optional[str] = data.get("url")
        self.disabled: bool = data.get("disabled", False)
        self.label: Optional[str] = data.get("label")
        self.emoji: Optional[PartialEmoji]
        try:
            self.emoji = PartialEmoji.from_dict(data["emoji"])
        except KeyError:
            self.emoji = None

    def to_dict(self) -> ButtonComponentPayload:
        payload = {
            "type": 2,
            "style": int(self.style),
            "label": self.label,
            "disabled": self.disabled,
        }
        if self.custom_id:
            payload["custom_id"] = self.custom_id

        if self.url:
            payload["url"] = self.url

        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()

        return payload  # type: ignore


class SelectMenuBase(Component):
    """Represents a Discord Bot UI Kit Select Menu.

    This is the base class for all select menus.

    .. versionadded:: 2.3

    Attributes
    ----------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
    disabled: :class:`bool`
        Whether the select menu is disabled or not. Defaults to ``False``.
    placeholder: Optional[:class:`str`]
        The placeholder of the select menu, if any.
    min_values: :class:`int`
        The minimum number of values that must be chosen. Defaults to 1.
    max_values: :class:`int`
        The maximum number of values that can be chosen. Defaults to 1.
    """

    __slots__: Tuple[str, ...] = (
        "custom_id",
        "disabled",
        "placeholder",
        "min_values",
        "max_values",
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: SelectMenuBasePayload) -> None:
        self.custom_id: str = data["custom_id"]
        self.disabled: bool = data.get("disabled", False)
        self.placeholder: Optional[str] = data.get("placeholder")
        self.min_values: int = data.get("min_values", 1)
        self.max_values: int = data.get("max_values", 1)

    def to_dict(self) -> SelectMenuBasePayload:
        payload: SelectMenuBasePayload = {
            "custom_id": self.custom_id,
            "disabled": self.disabled,
            "min_values": self.min_values,
            "max_values": self.max_values,
        }

        if self.placeholder:
            payload["placeholder"] = self.placeholder

        return payload


class StringSelectMenu(SelectMenuBase):
    """Represents a string select menu from the Discord Bot UI Kit.

    A select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    There is an alias for this class called ``SelectMenu``.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`nextcord.ui.Select` not this one.

    .. versionadded:: 2.0

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    options: List[:class:`SelectOption`]
        A list of options that can be selected in this menu.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    """

    __slots__: Tuple[str, ...] = ("options",)

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: SelectMenuPayload) -> None:
        super().__init__(data)
        self.type = ComponentType.select
        self.options: List[SelectOption] = [
            SelectOption.from_dict(option) for option in data.get("options", [])
        ]

    def to_dict(self) -> SelectMenuPayload:
        payload: SelectMenuPayload = {
            "type": self.type.value,
            "options": [op.to_dict() for op in self.options],
            **super().to_dict(),
        }

        return payload


SelectMenu = StringSelectMenu


class UserSelectMenu(SelectMenuBase):
    """Represents a user select menu from the Discord Bot UI Kit.

    A user select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`nextcord.ui.UserSelect` not this one.

    .. versionadded:: 2.3

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    """

    __slots__: Tuple[str, ...] = ()

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: UserSelectMenuPayload) -> None:
        super().__init__(data)
        self.type = ComponentType.user_select

    def to_dict(self) -> UserSelectMenuPayload:
        payload: UserSelectMenuPayload = {"type": self.type.value, **super().to_dict()}

        return payload


class RoleSelectMenu(SelectMenuBase):
    """Represents a role select menu from the Discord Bot UI Kit.

    A role select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`nextcord.ui.RoleSelect` not this one.

    .. versionadded:: 2.3

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    """

    __slots__: Tuple[str, ...] = ()

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: RoleSelectMenuPayload) -> None:
        super().__init__(data)
        self.type = ComponentType.role_select

    def to_dict(self) -> RoleSelectMenuPayload:
        payload: RoleSelectMenuPayload = {"type": self.type.value, **super().to_dict()}

        return payload


class MentionableSelectMenu(SelectMenuBase):
    """Represents a mentionable select menu from the Discord Bot UI Kit.

    A mentionable select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`nextcord.ui.MentionableSelect` not this one.

    .. versionadded:: 2.3

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    """

    __slots__: Tuple[str, ...] = ()

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: MentionableSelectMenuPayload) -> None:
        super().__init__(data)
        self.type = ComponentType.mentionable_select

    def to_dict(self) -> MentionableSelectMenuPayload:
        payload: MentionableSelectMenuPayload = {"type": self.type.value, **super().to_dict()}

        return payload


class ChannelSelectMenu(SelectMenuBase):
    """Represents a mentionable select menu from the Discord Bot UI Kit.

    A mentionable select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`nextcord.ui.ChannelSelect` not this one.

    .. versionadded:: 2.3

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    channel_types: List[:class:`ChannelType`]
        The types of channels that can be selected. If not given, all channel types are allowed.
    """

    __slots__: Tuple[str, ...] = ("channel_types",)

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ChannelSelectMenuPayload) -> None:
        super().__init__(data)
        self.type = ComponentType.channel_select
        self.channel_types: List[ChannelType] = [
            ChannelType(t) for t in data.get("channel_types", [])
        ]

    def to_dict(self) -> ChannelSelectMenuPayload:
        payload: ChannelSelectMenuPayload = {"type": self.type.value, **super().to_dict()}
        if self.channel_types:
            payload["channel_types"] = [t.value for t in self.channel_types]

        return payload


class SelectOption:
    """Represents a select menu's option.

    These can be created by users.

    .. versionadded:: 2.0

    Attributes
    ----------
    label: :class:`str`
        The label of the option. This is displayed to users.
        Can only be up to 100 characters.
    value: :class:`str`
        The value of the option. This is not displayed to users.
        If not provided when constructed then it defaults to the
        label. Can only be up to 100 characters.
    description: Optional[:class:`str`]
        An additional description of the option, if any.
        Can only be up to 100 characters.
    emoji: Optional[Union[:class:`str`, :class:`Emoji`, :class:`PartialEmoji`]]
        The emoji of the option, if available.
    default: :class:`bool`
        Whether this option is selected by default.
    """

    __slots__: Tuple[str, ...] = (
        "label",
        "value",
        "description",
        "emoji",
        "default",
    )

    def __init__(
        self,
        *,
        label: str,
        value: str = MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        default: bool = False,
    ) -> None:
        self.label: str = label
        self.value: str = label if value is MISSING else value
        self.description: Optional[str] = description

        if emoji is not None:
            if isinstance(emoji, str):
                emoji = PartialEmoji.from_str(emoji)
            elif isinstance(emoji, _EmojiTag):
                emoji = emoji._to_partial()
            else:
                raise TypeError(
                    f"Expected emoji to be str, Emoji, or PartialEmoji not {emoji.__class__}"
                )

        self.emoji: Optional[PartialEmoji] = emoji
        self.default: bool = default

    def __repr__(self) -> str:
        return (
            f"<SelectOption label={self.label!r} value={self.value!r} description={self.description!r} "
            f"emoji={self.emoji!r} default={self.default!r}>"
        )

    def __str__(self) -> str:
        if self.emoji:
            base = f"{self.emoji} {self.label}"
        else:
            base = self.label

        if self.description:
            return f"{base}\n{self.description}"
        return base

    @classmethod
    def from_dict(cls, data: SelectOptionPayload) -> SelectOption:
        try:
            emoji = PartialEmoji.from_dict(data["emoji"])
        except KeyError:
            emoji = None

        return cls(
            label=data["label"],
            value=data["value"],
            description=data.get("description"),
            emoji=emoji,
            default=data.get("default", False),
        )

    def to_dict(self) -> SelectOptionPayload:
        payload: SelectOptionPayload = {
            "label": self.label,
            "value": self.value,
            "default": self.default,
        }

        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()  # type: ignore

        if self.description:
            payload["description"] = self.description

        return payload


class TextInput(Component):
    __slots__: Tuple[str, ...] = (
        "style",
        "custom_id",
        "label",
        "min_length",
        "max_length",
        "required",
        "value",
        "placeholder",
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: TextInputComponentPayload) -> None:
        self.type: ComponentType = try_enum(ComponentType, data["type"])
        self.style: TextInputStyle = try_enum(
            TextInputStyle,
            data.get("style", 1),
        )
        self.custom_id: str = data.get("custom_id")
        self.label: str = data.get("label")
        self.min_length: Optional[int] = data.get("min_length")
        self.max_length: Optional[int] = data.get("max_length")
        self.required: Optional[bool] = data.get("required")
        self.value: Optional[str] = data.get("value")
        self.placeholder: Optional[str] = data.get("placeholder")

    def to_dict(self) -> TextInputComponentPayload:
        payload = {
            "type": 4,
            "custom_id": self.custom_id,
            "style": int(self.style.value),
            "label": self.label,
        }

        if self.min_length:
            payload["min_length"] = self.min_length

        if self.max_length:
            payload["max_length"] = self.max_length

        if self.required is not None:
            payload["required"] = self.required

        if self.value:
            payload["value"] = self.value

        if self.placeholder:
            payload["placeholder"] = self.placeholder

        return payload  # type: ignore


def _component_factory(data: ComponentPayload) -> Component:
    component_type = data["type"]
    if component_type == 1:
        return ActionRow(data)
    elif component_type == 2:
        return Button(data)  # type: ignore
    elif component_type == 3:
        return SelectMenu(data)  # type: ignore
    elif component_type == 4:
        return TextInput(data)  # type: ignore
    else:
        as_enum = try_enum(ComponentType, component_type)
        return Component._raw_construct(type=as_enum)
