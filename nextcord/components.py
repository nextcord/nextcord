# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
from typing import TYPE_CHECKING, ClassVar, List, Literal, Optional, Tuple, TypeVar, Union, cast

from .channel import _threaded_channel_factory
from .enums import (
    ButtonStyle,
    ChannelType,
    ComponentType,
    InteractionType,
    SelectDefaultValueType,
    SeparatorSpacingSize,
    TextInputStyle,
    try_enum,
)
from .object import Object
from .partial_emoji import PartialEmoji, _EmojiTag
from .types import (
    components as comp_payloads,
    emoji as emoji_payloads,
    interactions as inter_payloads,
)
from .utils import MISSING, get_slots

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any, Coroutine, Literal

    from typing_extensions import Self

    from . import abc
    from .client import Client
    from .emoji import Emoji
    from .file import File as DiscordFile
    from .interactions import Interaction
    from .member import Member
    from .role import Role
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
    from .user import User

    DiscordChannel = abc.GuildChannel | abc.PrivateChannel


__all__ = (
    "OLDComponent",
    "OLDActionRow",
    "OLDButton",
    "OLDSelectMenu",
    "OLDSelectOption",
    "OLDTextInput",
    "ActionRow",
    "Button",
    "ChannelSelect",
    "ChannelSelectMenu",
    "Component",
    "Container",
    "File",
    "HolderComponent",
    "InteractiveComponent",
    "MediaGallery",
    "MediaGalleryItem",
    "MentionableSelect",
    "MentionableSelectMenu",
    "resolve_component",
    "RoleSelect",
    "RoleSelectMenu",
    "Section",
    "SelectDefaultValue",
    "SelectMenu",
    "SelectOption",
    "Separator",
    "StringSelect",
    "StringSelectMenu",
    "TextDisplay",
    "TextInput",
    "Thumbnail",
    "UnfurledMedia",
    "UserSelect",
    "UserSelectMenu",
)

C = TypeVar("C", bound="Component")


class _InteractiveComponentPayload(comp_payloads.BaseComponent):
    custom_id: str


class _HolderComponentPayload(comp_payloads.BaseComponent):
    components: list[comp_payloads.Component | comp_payloads.BaseComponent]


class OLDComponent:
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

    __slots__: Tuple[str, ...] = ()

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


class OLDActionRow(OLDComponent):
    """Represents a Discord Bot UI Kit Action Row.

    This is a component that holds up to 5 children components in a row.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    children: List[:class:`OLDComponent`]
        The children components that this holds, if any.
    """

    __slots__: Tuple[str, ...] = ("type", "children")

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ComponentPayload) -> None:
        self.type: ComponentType = try_enum(ComponentType, data["type"])
        self.children: List[OLDComponent] = [
            _OLDcomponent_factory(d) for d in data.get("components", [])
        ]

    def to_dict(self) -> ActionRowPayload:
        return {
            "type": cast(Literal[1], int(self.type)),
            "components": [child.to_dict() for child in self.children],
        }


class OLDButton(OLDComponent):
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
        "type",
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
        self.emoji: Optional[PartialEmoji] = None
        if "emoji" in data:
            self.emoji = PartialEmoji.from_dict(data["emoji"])

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


class OLDSelectMenuBase(OLDComponent):
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


class StringOLDSelectMenu(OLDSelectMenuBase):
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
    options: List[:class:`OLDSelectOption`]
        A list of options that can be selected in this menu.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    """

    __slots__: Tuple[str, ...] = ("options",)
    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    type: Literal[ComponentType.select] = ComponentType.select

    def __init__(self, data: SelectMenuPayload) -> None:
        super().__init__(data)
        self.options: List[OLDSelectOption] = [
            OLDSelectOption.from_dict(option) for option in data.get("options", [])
        ]

    def to_dict(self) -> SelectMenuPayload:
        payload: SelectMenuPayload = {
            "type": self.type.value,
            "options": [op.to_dict() for op in self.options],
            **super().to_dict(),
        }

        return payload


OLDSelectMenu = StringOLDSelectMenu


class UserOLDSelectMenu(OLDSelectMenuBase):
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

    type: Literal[ComponentType.user_select] = ComponentType.user_select

    def __init__(self, data: UserSelectMenuPayload) -> None:
        super().__init__(data)

    def to_dict(self) -> UserSelectMenuPayload:
        payload: UserSelectMenuPayload = {"type": self.type.value, **super().to_dict()}

        return payload


class RoleOLDSelectMenu(OLDSelectMenuBase):
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

    type: Literal[ComponentType.role_select] = ComponentType.role_select

    def __init__(self, data: RoleSelectMenuPayload) -> None:
        super().__init__(data)

    def to_dict(self) -> RoleSelectMenuPayload:
        payload: RoleSelectMenuPayload = {"type": self.type.value, **super().to_dict()}

        return payload


class MentionableOLDSelectMenu(OLDSelectMenuBase):
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

    type: Literal[ComponentType.mentionable_select] = ComponentType.mentionable_select

    def __init__(self, data: MentionableSelectMenuPayload) -> None:
        super().__init__(data)

    def to_dict(self) -> MentionableSelectMenuPayload:
        payload: MentionableSelectMenuPayload = {"type": self.type.value, **super().to_dict()}

        return payload


class ChannelOLDSelectMenu(OLDSelectMenuBase):
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

    type: Literal[ComponentType.channel_select] = ComponentType.channel_select

    def __init__(self, data: ChannelSelectMenuPayload) -> None:
        super().__init__(data)
        self.channel_types: List[ChannelType] = [
            ChannelType(t) for t in data.get("channel_types", [])
        ]

    def to_dict(self) -> ChannelSelectMenuPayload:
        payload: ChannelSelectMenuPayload = {"type": self.type.value, **super().to_dict()}
        if self.channel_types:
            payload["channel_types"] = [t.value for t in self.channel_types]

        return payload


class OLDSelectOption:
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
        base = f"{self.emoji} {self.label}" if self.emoji else self.label

        if self.description:
            return f"{base}\n{self.description}"
        return base

    @classmethod
    def from_dict(cls, data: SelectOptionPayload) -> OLDSelectOption:
        emoji = PartialEmoji.from_dict(data["emoji"]) if "emoji" in data else None

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


class OLDTextInput(OLDComponent):
    __slots__: Tuple[str, ...] = (
        "type",
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


def _OLDcomponent_factory(data: ComponentPayload) -> OLDComponent:
    component_type = data["type"]
    if component_type == 1:
        return OLDActionRow(data)
    if component_type == 2:
        return OLDButton(data)  # type: ignore
    if component_type == 3:
        return OLDSelectMenu(data)  # type: ignore
    if component_type == 4:
        return OLDTextInput(data)  # type: ignore
    as_enum = try_enum(ComponentType, component_type)
    return OLDComponent._raw_construct(type=as_enum)


class Component:
    """Represents a basic component object.

    Base class for all components.
    Intended to be abstract and not instantiated by users, but will be used internally if no other component
    class is available.

    .. versionadded:: 2.0

    .. versionchanged:: 3.2

        - :class:`.Component` is now user init-able.
        - Added :attr:`~.Component.id` attribute.

    Parameters
    ----------
    component_type
        Type of the component.
    component_id
        Per-message unique ID of the component. If not provided, it will be generated by Discord when sent.
    """

    type: ComponentType
    """The type of component."""
    id: int  # Can be MISSING
    """ID of the component. Can be ``MISSING``."""

    def __init__(self, *, component_type: int | ComponentType, component_id: int = MISSING) -> None:
        if isinstance(component_type, ComponentType):
            self.type = component_type
        else:
            self.type = try_enum(ComponentType, component_type)

        self.id = component_id

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.type} id={self.id} at {hex(id(self))}>"

    def to_dict(self) -> comp_payloads.BaseComponent:
        ret = cast(comp_payloads.BaseComponent, {"type": self.type.value})
        if self.id is not MISSING:
            ret["id"] = self.id

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.BaseComponent):
        return cls(component_type=payload["type"], component_id=payload["id"])


class InteractiveComponent(Component):
    """Base class for components with the ``custom_id`` attribute and should have callback-related helper methods.

    This class is intended to be abstract and not instantiated by users.

    .. versionadded:: 3.2
    """

    custom_id: str  # Can be MISSING, specifically for link and premium buttons. If those 2 button types no longer
    """Custom ID of the component, received in :class:`.Interaction` data. Can be ``MISSING``"""
    #  subclass InteractiveComponent, this should no longer be set to missing.

    def __init__(
        self,
        custom_id: str | None = MISSING,
        *,
        component_type: int | ComponentType,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(component_type=component_type, component_id=component_id)
        if custom_id is None:
            self.custom_id = os.urandom(16).hex()  # TODO: Use UUID lib instead?
        else:
            self.custom_id = custom_id

    async def _wait_for_interaction[
        ClientT: Client, *T
    ](
        self,
        bot: ClientT,
        callback: Callable[[Interaction[ClientT], *T], Coroutine[None, None, Any]],
        timeout: float | None = 180.0,
        *,
        _inter_arg_func: Callable[[Interaction[ClientT]], tuple[Interaction[ClientT], *T]],
    ):
        if self.custom_id is MISSING:
            raise ValueError("Missing custom_id to match with interaction.")

        def inter_check(inter: Interaction[ClientT]) -> bool:
            return (
                inter.type == InteractionType.component
                and inter.data is not None
                and inter.data.get("custom_id", None) == self.custom_id
            )

        interaction: Interaction[ClientT] = await bot.wait_for(
            "interaction", check=inter_check, timeout=timeout
        )
        args = _inter_arg_func(interaction)
        return await callback(*args)

    async def wait_for_interaction(
        self,
        bot: Client,
        callback: Callable[[Interaction], Coroutine[None, None, Any]],
        timeout: float | None = 180.0,
    ):
        """|coro|

        Helper method, waits for an interaction with the matching :attr:`.custom_id` to be received by the
        given bot/:class:`.Client`.

        Parameters
        ----------
        bot
            Bot/Client object to listen for received interactions.
        callback
            Awaitable callback to execute when the custom ID is found.
        timeout
            Time in seconds to wait before timing out and raising :exc:`asyncio.TimeoutError`.

        Raises
        ------
        asyncio.TimeoutError
            If a timeout is provided and it was reached.

        Returns
        -------
        Any
            Returns the return value of the given callback.
        """
        return await self._wait_for_interaction(
            bot, callback, timeout, _inter_arg_func=lambda i: (i,)
        )

    def to_dict(self) -> _InteractiveComponentPayload:
        ret = cast(_InteractiveComponentPayload, super().to_dict())
        if self.custom_id is not MISSING:
            ret["custom_id"] = self.custom_id

        return ret


def get_interactive_components(components: list[Component]) -> set[InteractiveComponent]:
    ret = set()
    for comp in components:
        if isinstance(comp, HolderComponent):
            ret.update(comp.get_interactives())
        elif isinstance(comp, InteractiveComponent):
            ret.add(comp)

    return ret


class _SelectComponent(InteractiveComponent):
    """Base class for shared code between the User/Role/Mentionable/Channel Select components. Any
    additions/changes specific to a select type should be made to those specific subclasses, not this one.

    String select should not subclass this, as it is (currently) different enough.

    This class is intended to be abstract and not instantiated.

    .. versionadded:: 3.2
    """

    placeholder: str  # Can be MISSING
    """Placeholder text if nothing is selected. Can be ``MISSING``."""
    default_values: list[SelectDefaultValue]  # Can be MISSING
    """List of pre-populated values. Can be ``MISSING``."""
    min_values: int  # Can be MISSING
    """Minimum amount of chosen values. Can be ``MISSING``."""
    max_values: int  # Can be MISSING
    """Maximum amount of chosen values. Can be ``MISSING``."""
    disabled: bool  # Can be MISSING
    """If the menu is disabled. Can be ``MISSING``."""

    def __init__(
        self,
        component_type: ComponentType | int,
        custom_id: str | None = None,
        *,
        placeholder: str = MISSING,
        default_values: list[SelectDefaultValue] = MISSING,
        min_values: int = MISSING,
        max_values: int = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(custom_id, component_type=component_type, component_id=component_id)
        self.placeholder = placeholder
        self.default_values = default_values
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled

    def add_default_value(
        self,
        value_id: int,
        value_type: SelectDefaultValueType | str | Literal["user", "role", "channel"],
    ) -> None:
        """Adds a default value to be pre-populated in the Select dropdown of the given ID and type."""
        if self.default_values is MISSING:
            self.default_values = []

        self.default_values.append(SelectDefaultValue(value_id, value_type))

    def to_dict(self) -> comp_payloads.SelectMenuBase:
        ret = comp_payloads.SelectMenuBase(**super().to_dict())

        if self.placeholder is not MISSING:
            ret["placeholder"] = self.placeholder

        if self.default_values is not MISSING:
            ret["default_values"] = [def_val.to_dict() for def_val in self.default_values]

        if self.min_values is not MISSING:
            ret["min_values"] = self.min_values

        if self.max_values is not MISSING:
            ret["max_values"] = self.max_values

        if self.disabled is not MISSING:
            ret["disabled"] = self.disabled

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.SelectMenuBase):
        if "default_values" in payload:
            default_values = [
                SelectDefaultValue.from_dict(val_data) for val_data in payload["default_values"]
            ]
        else:
            default_values = MISSING

        return cls(
            component_type=payload["type"],
            custom_id=payload["custom_id"],
            placeholder=payload.get("placeholder", MISSING),
            default_values=default_values,
            min_values=payload.get("min_values", MISSING),
            max_values=payload.get("max_values", MISSING),
            disabled=payload.get("disabled", MISSING),
            component_id=payload["id"],
        )


class HolderComponent(Component):
    """Base class for components with the ``components`` attribute that are designed to hold other components.

    This class is intended to be abstract and not instantiated by users.

    .. versionadded:: 3.2
    """

    components: list[Component]
    """List of child components."""

    def __init__(
        self,
        components: list[Component],
        *,
        component_type: ComponentType | int,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(component_type=component_type, component_id=component_id)
        self.components = components

    def to_dict(self) -> _HolderComponentPayload:
        return _HolderComponentPayload(
            **super().to_dict(), components=[comp.to_dict() for comp in self.components]
        )

    def get_interactives(self) -> set[InteractiveComponent]:
        return get_interactive_components(self.components)


class ActionRow(HolderComponent):  # Component type 1
    """Represents an Action Row component object.

    This is a component that holds up to 5 children components in a row.

    .. versionadded:: 2.0

    .. versionchanged:: 3.2
        :class:`.ActionRow` is now user init-able.
    """

    def __init__(self, components: list[Component], *, component_id: int = MISSING) -> None:
        super().__init__(
            components, component_type=ComponentType.action_row, component_id=component_id
        )

    @property
    def children(self) -> list[Component]:
        """The children components that this holds, if any. Alias for :attr:`.components`."""
        return self.components

    @classmethod
    def from_dict(cls, payload: comp_payloads.ActionRow):
        return cls(
            components=[resolve_component(comp_data) for comp_data in payload["components"]],
            component_id=payload["id"],
        )

    def to_dict(self) -> comp_payloads.ActionRow:
        return cast(comp_payloads.ActionRow, super().to_dict())


# TODO: Think about moving Premium and Link buttons to a "NoninteractiveButton" thing?
class Button(InteractiveComponent):  # Component type 2
    """Represents a Button component object.

    .. note::
        Due to the conflicting options present in ``__init__``, it is recommended to use the various
        classmethods such as :meth:`.as_primary`, :meth:`.as_secondary`, etc.

    .. versionadded:: 2.0

    .. versionchanged:: 3.2
        :class:`.Button` is now user init-able.

    """

    style: ButtonStyle
    """The style of the button."""
    label: str  # Can be MISSING
    """The label of the button. Can be ``MISSING``."""
    emoji: PartialEmoji  # Can be MISSING
    """The emoji of the button. Can be ``MISSING``."""
    sku_id: int  # Can be MISSING
    """ID of a purchasable SKU, only for premium-style buttons. Can be ``MISSING``."""
    url: str  # Can be MISSING
    """The URL this button sends you to, only for link-style buttons. Can be ``MISSING``."""
    disabled: bool  # Can be MISSING
    """Whether the button is disabled or not. Can be ``MISSING``."""

    def __init__(
        self,
        style: ButtonStyle | int,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        custom_id: str | None = MISSING,
        sku_id: int = MISSING,
        url: str = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(custom_id, component_type=ComponentType.button, component_id=component_id)
        if isinstance(style, ButtonStyle):
            self.style = style
        else:
            self.style = try_enum(ButtonStyle, style)

        self.label = label
        self.emoji = emoji
        self.sku_id = sku_id
        self.url = url
        self.disabled = disabled

    def to_dict(self) -> comp_payloads.ButtonComponent:
        ret = cast(comp_payloads.ButtonComponent, super().to_dict())
        ret["style"] = self.style.value
        if self.label is not MISSING:
            ret["label"] = self.label

        if self.emoji is not MISSING:
            ret["emoji"] = cast(emoji_payloads.PartialEmoji, self.emoji.to_dict())

        if self.sku_id is not MISSING:
            ret["sku_id"] = self.sku_id

        if self.url is not MISSING:
            ret["url"] = self.url

        if self.disabled is not MISSING:
            ret["disabled"] = self.disabled

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.ButtonComponent):
        emoji = PartialEmoji.from_dict(payload["emoji"]) if "emoji" in payload else MISSING

        return cls(
            style=payload["style"],
            label=payload.get("label", MISSING),
            emoji=emoji,
            custom_id=payload.get(
                "custom_id", MISSING
            ),  # Marked as required in Discord docs, but Premium cant have it
            sku_id=payload.get("sku_id", MISSING),
            url=payload.get("url", MISSING),
            disabled=payload.get("disabled", MISSING),
            component_id=payload["id"],
        )

    async def wait_for_interaction[
        ClientT: Client
    ](
        self,
        bot: ClientT,
        callback: Callable[[Interaction[ClientT]], Coroutine[None, None, Any]],
        timeout: float | None = 180.0,
    ):
        return await super()._wait_for_interaction(
            bot, callback, timeout, _inter_arg_func=lambda i: (i,)
        )

    @classmethod
    def as_primary(  # Style 1
        cls,
        custom_id: str | None = None,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ):
        """Creates a primary-styled button.

        Unspecified parameters will use Discord defaults.

        Parameters
        ----------
        custom_id
            Optionally supplied custom ID for the button.
        label
            Text to display on the button. Required unless ``emoji`` is specified.
        emoji
            Emoji to display on the button. Required unless ``label`` is specified.
        disabled
            Whether the button should be disabled or not.
        component_id
            ID of the component.

        Returns
        -------
        :class:`.Button`
            Button with the primary style.
        """
        return cls(
            style=ButtonStyle.primary,
            custom_id=custom_id,
            label=label,
            emoji=emoji,
            disabled=disabled,
            component_id=component_id,
        )

    @classmethod
    def as_secondary(  # Style 2
        cls,
        custom_id: str | None = None,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ):
        """Creates a secondary-styled button.

        Unspecified parameters will use Discord defaults.

        Parameters
        ----------
        custom_id
            Optionally supplied custom ID for the button.
        label
            Text to display on the button. Required unless ``emoji`` is specified.
        emoji
            Emoji to display on the button. Required unless ``label`` is specified.
        disabled
            Whether the button should be disabled or not.
        component_id
            ID of the component.

        Returns
        -------
        :class:`.Button`
            Button with the secondary style.
        """
        return cls(
            style=ButtonStyle.secondary,
            custom_id=custom_id,
            label=label,
            emoji=emoji,
            disabled=disabled,
            component_id=component_id,
        )

    @classmethod
    def as_success(  # Style 3
        cls,
        custom_id: str | None = None,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ):
        """Creates a success-styled button.

        Unspecified parameters will use Discord defaults.

        Parameters
        ----------
        custom_id
            Optionally supplied custom ID for the button.
        label
            Text to display on the button. Required unless ``emoji`` is specified.
        emoji
            Emoji to display on the button. Required unless ``label`` is specified.
        disabled
            Whether the button should be disabled or not.
        component_id
            ID of the component.

        Returns
        -------
        :class:`.Button`
            Button with the success style.
        """
        return cls(
            style=ButtonStyle.success,
            custom_id=custom_id,
            label=label,
            emoji=emoji,
            disabled=disabled,
            component_id=component_id,
        )

    @classmethod
    def as_danger(  # Style 4
        cls,
        custom_id: str | None = None,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ):
        """Creates a danger-styled button.

        Unspecified parameters will use Discord defaults.

        Parameters
        ----------
        custom_id
            Optionally supplied custom ID for the button.
        label
            Text to display on the button. Required unless ``emoji`` is specified.
        emoji
            Emoji to display on the button. Required unless ``label`` is specified.
        disabled
            Whether the button should be disabled or not.
        component_id
            ID of the component.

        Returns
        -------
        :class:`.Button`
            Button with the danger style.
        """
        return cls(
            style=ButtonStyle.danger,
            custom_id=custom_id,
            label=label,
            emoji=emoji,
            disabled=disabled,
            component_id=component_id,
        )

    @classmethod
    def as_link(  # Style 5
        cls,
        url: str,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ):
        """Creates a link-styled button.

        Unspecified non-required parameters will use Discord defaults.

        Parameters
        ----------
        url
            The URL the button should send you to.
        label
            Text to display on the button. Required unless ``emoji`` is specified.
        emoji
            Emoji to display on the button. Required unless ``label`` is specified.
        disabled
            Whether the button should be disabled or not.
        component_id
            ID of the component.

        Returns
        -------
        :class:`.Button`
            Button with the link style.
        """
        return cls(
            style=ButtonStyle.link,
            url=url,
            label=label,
            emoji=emoji,
            disabled=disabled,
            component_id=component_id,
        )

    @classmethod
    def as_premium(
        cls, sku_id: int, *, disabled: bool = MISSING, component_id: int = MISSING
    ):  # Style 6
        """Creates a premium-styled button.

        Unspecified non-required parameters will use Discord defaults.

        Parameters
        ----------
        sku_id
            ID of a purchasable SKU.
        disabled
            Whether the button should be disabled or not.
        component_id
            ID of the component.

        Returns
        -------
        :class:`.Button`
            Button with the premium style.
        """
        return cls(
            style=ButtonStyle.premium,
            sku_id=sku_id,
            disabled=disabled,
            component_id=component_id,
        )


class StringSelect(InteractiveComponent):  # Component type 3
    """Represents a String Select component object.

    A select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    There are 2 aliases for this class. ``StringSelectMenu`` for compatibility purposes and ``SelectMenu``.

    .. versionadded:: 2.0

    .. versionchanged:: 3.2

        - :class:`.StringSelect` is now user init-able.
        - Renamed from ``StringSelectMenu`` to ``StringSelect`` to match Discord's name, and an alias for
          the old name added.

    """

    options: list[SelectOption]
    """A list of options that can be selected in this menu."""
    placeholder: str  # Can be MISSING
    """The placeholder text that is shown if nothing is selected, if any. Can be ``MISSING``"""
    min_values: int  # Can be MISSING
    """The minimum number of items that must be chosen for this select menu. Can be ``MISSING``"""
    max_values: int  # Can be MISSING
    """The maximum number of items that must be chosen for this select menu. Can be ``MISSING``"""
    disabled: bool  # Can be MISSING
    """Whether the select is disabled or not. Can be ``MISSING``"""

    def __init__(
        self,
        custom_id: str | None = None,
        options: list[SelectOption] | None = None,
        *,
        placeholder: str = MISSING,
        min_values: int = MISSING,
        max_values: int = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(
            custom_id, component_type=ComponentType.string_select, component_id=component_id
        )
        self.options = options if options is not None else []
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled

    def add_option(
        self,
        label: str,
        value: str = MISSING,
        *,
        description: str = MISSING,
        emoji: PartialEmoji | Emoji | str = MISSING,
        default: bool = MISSING,
    ) -> None:
        """Helper method to add an option to the :attr:`.options` list.

        Parameters
        ----------
        label
            User-facing name of the option.
        value
            Dev-defined/Bot-facing value of the option. Defaults to the value of ``label`` if unspecified.
        description
            Description for the option.
        emoji
            Emoji to display with the option.
        default
            If this option will be selected by default.
        Returns
        -------
        None
        """
        self.options.append(
            SelectOption(
                label=label, value=value, description=description, emoji=emoji, default=default
            )
        )

    async def wait_for_interaction(
        self,
        bot: Client,
        callback: Callable[[Interaction, tuple[str, ...]], Coroutine[None, None, Any]],
        timeout: float | None = 180.0,
    ):
        def inter_arg_func(inter: Interaction[Client]):
            data = cast(inter_payloads.ComponentInteractionData, inter.data)
            if "values" not in data:
                raise ValueError('Missing "values" key from interaction data.')

            return inter, tuple(data["values"])

        return await super()._wait_for_interaction(
            bot, callback, timeout, _inter_arg_func=inter_arg_func
        )

    def to_dict(self) -> comp_payloads.SelectMenu:
        ret = cast(comp_payloads.SelectMenu, super().to_dict())
        ret["options"] = [option.to_dict() for option in self.options]

        if self.placeholder is not MISSING:
            ret["placeholder"] = self.placeholder

        if self.min_values is not MISSING:
            ret["min_values"] = self.min_values

        if self.max_values is not MISSING:
            ret["max_values"] = self.max_values

        if self.disabled is not MISSING:
            ret["disabled"] = self.disabled

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.SelectMenu):
        return cls(
            custom_id=payload["custom_id"],
            options=[SelectOption.from_dict(opt_data) for opt_data in payload["options"]],
            placeholder=payload.get("placeholder", MISSING),
            min_values=payload.get("min_values", MISSING),
            max_values=payload.get("max_values", MISSING),
            disabled=payload.get("disabled", MISSING),
            component_id=payload.get("id", MISSING),
        )


StringSelectMenu = StringSelect
SelectMenu = StringSelect


class TextInput(InteractiveComponent):  # Component type 4
    """Represents a Text Input component object.

    Allows for users to enter free-form text responses, and supports both single-line and multi-line inputs. Can only
    be used within modals.

    .. versionadded:: 2.0

    .. versionchanged:: 3.2
        :class:`.TextInput` is now user init-able.

    """

    style: TextInputStyle
    """Style of the text input."""
    label: str
    """Label of the text input."""
    min_length: int  # Can be MISSING
    """The minimal length of the user's input. Can be ``MISSING``."""
    max_length: int  # Can be MISSING
    """The maximal length of the user's input. Can be ``MISSING``."""
    required: bool  # Can be MISSING
    """If ``True``, the user cannot send the form without filling this field. Can be ``MISSING``."""
    value: str  # Can be MISSING
    """Pre-filled value for the component. Can be ``MISSING``."""
    placeholder: str  # Can be MISSING
    """The text shown to the user when the text input is empty. Can be ``MISSING``."""

    def __init__(
        self,
        style: TextInputStyle | int,
        label: str,
        custom_id: str | None = None,
        *,
        min_length: int = MISSING,
        max_length: int = MISSING,
        required: bool = MISSING,
        value: str = MISSING,
        placeholder: str = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(
            custom_id, component_type=ComponentType.text_input, component_id=component_id
        )
        if isinstance(style, TextInputStyle):
            self.style = style
        else:
            self.style = try_enum(TextInputStyle, style)

        self.label = label
        self.min_length = min_length
        self.max_length = max_length
        self.required = required
        self.value = value
        self.placeholder = placeholder

    def to_dict(self) -> comp_payloads.TextInputComponent:
        ret = cast(comp_payloads.TextInputComponent, super().to_dict())
        ret["style"] = self.style.value
        ret["label"] = self.label

        if self.min_length is not MISSING:
            ret["min_length"] = self.min_length

        if self.max_length is not MISSING:
            ret["max_length"] = self.max_length

        if self.required is not MISSING:
            ret["required"] = self.required

        if self.value is not MISSING:
            ret["value"] = self.value

        if self.placeholder is not MISSING:
            ret["placeholder"] = self.placeholder

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.TextInputComponent):
        return cls(
            payload["style"],
            payload["label"],
            payload["custom_id"],
            min_length=payload.get("min_length", MISSING),
            max_length=payload.get("max_length", MISSING),
            required=payload.get("required", MISSING),
            value=payload.get("value", MISSING),
            placeholder=payload.get("placeholder", MISSING),
            component_id=payload.get("id", MISSING),
        )

    @classmethod
    def as_short(
        cls,
        label: str,
        custom_id: str | None = None,
        *,
        min_length: int = MISSING,
        max_length: int = MISSING,
        required: bool = MISSING,
        value: str = MISSING,
        placeholder: str = MISSING,
        component_id: int = MISSING,
    ):
        """Creates a short-styled, single-line text input.

        Unspecified non-required parameters will use Discord defaults.

        Parameters
        ----------
        label
            Label of the text input.
        custom_id
            Optionally supplied custom ID for the text input.
        min_length
            The minimal length of the user's input.
        max_length
            The maximal length of the user's input.
        required
            If ``True``, the user cannot send the form without filling this field.
        value
            Pre-filled value for the component.
        placeholder
            The text shown to the user when the text input is empty.
        component_id
            ID of the component.

        Returns
        -------
        :class:`.TextInput`
            Text input with the short style.
        """
        return cls(
            TextInputStyle.short,
            label,
            custom_id,
            min_length=min_length,
            max_length=max_length,
            required=required,
            value=value,
            placeholder=placeholder,
            component_id=component_id,
        )

    @classmethod
    def as_paragraph(
        cls,
        label: str,
        custom_id: str | None = None,
        *,
        min_length: int = MISSING,
        max_length: int = MISSING,
        required: bool = MISSING,
        value: str = MISSING,
        placeholder: str = MISSING,
        component_id: int = MISSING,
    ):
        """Creates a paragraph-styled, multi-line text input.

        Unspecified non-required parameters will use Discord defaults.

        Parameters
        ----------
        label
            Label of the text input.
        custom_id
            Optionally supplied custom ID for the text input.
        min_length
            The minimal length of the user's input.
        max_length
            The maximal length of the user's input.
        required
            If ``True``, the user cannot send the form without filling this field.
        value
            Pre-filled value for the component.
        placeholder
            The text shown to the user when the text input is empty.
        component_id
            ID of the component.

        Returns
        -------
        :class:`.TextInput`
            Text input with the paragraph style.
        """
        return cls(
            TextInputStyle.paragraph,
            label,
            custom_id,
            min_length=min_length,
            max_length=max_length,
            required=required,
            value=value,
            placeholder=placeholder,
            component_id=component_id,
        )


class UserSelect(_SelectComponent):  # Component type 5
    """Represents a User Select component object.

    A user select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. versionadded:: 2.3

    .. versionchanged:: 3.2

        - :class:`.UserSelect` is now user init-able.
        - Renamed from ``UserSelectMenu`` to ``UserSelect`` to match Discord's name, and an alias for the old name added.
        - Added :attr:`.default_values` attribute.
    """

    def __init__(
        self,
        custom_id: str | None = None,
        *,
        placeholder: str = MISSING,
        default_values: list[SelectDefaultValue] = MISSING,
        min_values: int = MISSING,
        max_values: int = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(
            component_type=ComponentType.user_select,
            custom_id=custom_id,
            placeholder=placeholder,
            default_values=default_values,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            component_id=component_id,
        )

    def add_default_value(
        self, value_id: int, value_type: SelectDefaultValueType | str = SelectDefaultValueType.user
    ):
        return super().add_default_value(value_id, value_type)

    async def wait_for_interaction[
        ClientT: Client
    ](
        self,
        bot: ClientT,
        callback: Callable[
            [Interaction[ClientT], tuple[User | Member, ...]], Coroutine[None, None, Any]
        ],
        timeout: float | None = 180.0,
    ):
        def inter_arg_func(inter: Interaction[ClientT]):
            resolved_peeps = inter._resolve_users()
            resolved_dict = {peep.id: peep for peep in resolved_peeps}
            inter.data = cast(inter_payloads.ComponentInteractionData, inter.data)
            if "values" in inter.data:
                return inter, tuple([resolved_dict[int(val)] for val in inter.data["values"]])
            raise ValueError("Interaction data does not include values key.")

        return await super()._wait_for_interaction(
            bot, callback, timeout, _inter_arg_func=inter_arg_func
        )

    @classmethod
    def from_dict(cls, payload: comp_payloads.UserSelectMenu):
        if "default_values" in payload:
            default_values = [
                SelectDefaultValue.from_dict(val_data) for val_data in payload["default_values"]
            ]
        else:
            default_values = MISSING

        return cls(
            custom_id=payload["custom_id"],
            placeholder=payload.get("placeholder", MISSING),
            default_values=default_values,
            min_values=payload.get("min_values", MISSING),
            max_values=payload.get("max_values", MISSING),
            disabled=payload.get("disabled", MISSING),
            component_id=payload["id"],
        )

    def to_dict(self) -> comp_payloads.UserSelectMenu:
        return cast(comp_payloads.UserSelectMenu, super().to_dict())


UserSelectMenu = UserSelect


class RoleSelect(_SelectComponent):  # Component type 6
    """Represents a Role Select component object.

    A role select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. versionadded:: 2.3

    .. versionchanged:: 3.2

        - :class:`.RoleSelect` is now user init-able.
        - Renamed from ``RoleSelectMenu`` to ``RoleSelect`` to match Discord's name, and an alias for the old name added.
        - Added :attr:`.default_values` attribute.
    """

    def __init__(
        self,
        custom_id: str | None = None,
        *,
        placeholder: str = MISSING,
        default_values: list[SelectDefaultValue] = MISSING,
        min_values: int = MISSING,
        max_values: int = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(
            component_type=ComponentType.role_select,
            custom_id=custom_id,
            placeholder=placeholder,
            default_values=default_values,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            component_id=component_id,
        )

    def add_default_value(
        self, value_id: int, value_type: SelectDefaultValueType | str = SelectDefaultValueType.role
    ):
        return super().add_default_value(value_id, value_type)

    async def wait_for_interaction(
        self,
        bot: Client,
        callback: Callable[[Interaction, tuple[Role, ...]], Coroutine[None, None, Any]],
        timeout: float | None = 180.0,
    ):
        def inter_arg_func(inter: Interaction[Client]):
            resolved_roles = inter._resolve_roles()
            resolved_dict = {role.id: role for role in resolved_roles}
            inter.data = cast(inter_payloads.ComponentInteractionData, inter.data)
            if "values" in inter.data:
                return inter, tuple([resolved_dict[int(val)] for val in inter.data["values"]])
            raise ValueError("Interaction data does not include values key.")

        return await super()._wait_for_interaction(
            bot, callback, timeout, _inter_arg_func=inter_arg_func
        )

    @classmethod
    def from_dict(cls, payload: comp_payloads.RoleSelectMenu):
        if "default_values" in payload:
            default_values = [
                SelectDefaultValue.from_dict(val_data) for val_data in payload["default_values"]
            ]
        else:
            default_values = MISSING

        return cls(
            custom_id=payload["custom_id"],
            placeholder=payload.get("placeholder", MISSING),
            default_values=default_values,
            min_values=payload.get("min_values", MISSING),
            max_values=payload.get("max_values", MISSING),
            disabled=payload.get("disabled", MISSING),
            component_id=payload["id"],
        )

    def to_dict(self) -> comp_payloads.RoleSelectMenu:
        return cast(comp_payloads.RoleSelectMenu, super().to_dict())


RoleSelectMenu = RoleSelect


class MentionableSelect(_SelectComponent):  # Component type 7
    """Represents a Mentionable Select componeont object.

    A mentionable select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. versionadded:: 2.3

    .. versionchanged:: 3.2

        - :class:`.MentionableSelect` is now user init-able.
        - Renamed from ``MentionableSelectMenu`` to ``MentionableSelect`` to match Discord's name, and an alias
          for the old name added.
        - Added :attr:`.default_values` attribute.
    """

    def __init__(
        self,
        custom_id: str | None = None,
        *,
        placeholder: str = MISSING,
        default_values: list[SelectDefaultValue] = MISSING,
        min_values: int = MISSING,
        max_values: int = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(
            component_type=ComponentType.mentionable_select,
            custom_id=custom_id,
            placeholder=placeholder,
            default_values=default_values,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            component_id=component_id,
        )

    def add_default_value(
        self, value_id: int, value_type: SelectDefaultValueType | str | Literal["user", "role"]
    ):
        return super().add_default_value(value_id, value_type)

    async def wait_for_interaction(
        self,
        bot: Client,
        callback: Callable[
            [Interaction, tuple[User | Member | Role, ...]], Coroutine[None, None, Any]
        ],
        timeout: float | None = 180.0,
    ):
        def inter_arg_func(inter: Interaction):
            resolved_peeps = inter._resolve_users()
            resolved_dict: dict[int, User | Member | Role] = {
                peep.id: peep for peep in resolved_peeps
            }
            resolved_roles = inter._resolve_roles()
            resolved_dict.update({role.id: role for role in resolved_roles})
            inter.data = cast(inter_payloads.ComponentInteractionData, inter.data)
            if "values" in inter.data:
                return inter, tuple([resolved_dict[int(val)] for val in inter.data["values"]])
            raise ValueError("Interaction data does not include values key.")

        return await self._wait_for_interaction(
            bot, callback, timeout, _inter_arg_func=inter_arg_func
        )

    @classmethod
    def from_dict(cls, payload: comp_payloads.MentionableSelectMenu):
        if "default_values" in payload:
            default_values = [
                SelectDefaultValue.from_dict(val_data) for val_data in payload["default_values"]
            ]
        else:
            default_values = MISSING

        return cls(
            custom_id=payload["custom_id"],
            placeholder=payload.get("placeholder", MISSING),
            default_values=default_values,
            min_values=payload.get("min_values", MISSING),
            max_values=payload.get("max_values", MISSING),
            disabled=payload.get("disabled", MISSING),
            component_id=payload["id"],
        )

    def to_dict(self) -> comp_payloads.MentionableSelectMenu:
        return cast(comp_payloads.MentionableSelectMenu, super().to_dict())


MentionableSelectMenu = MentionableSelect


class ChannelSelect(_SelectComponent):  # Component type 8
    """Represents a Channel Select component object.

    A channel select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. versionadded:: 2.3

    .. versionchanged:: 3.2

        - :class:`.ChannelSelect` is now user init-able.
        - Renamed from ``ChannelSelectMenu`` to ``ChannelSelect`` to match Discord's name, and an alias for the
          old name added.
        - Added :attr:`.default_values` attribute.
    """

    channel_types: list[ChannelType]  # Can be MISSING
    """The types of channels that can be selected. If ``MISSING``, all channel types are allowed."""

    def __init__(
        self,
        custom_id: str | None = None,
        *,
        channel_types: Sequence[ChannelType | int] = MISSING,
        placeholder: str = MISSING,
        default_values: list[SelectDefaultValue] = MISSING,
        min_values: int = MISSING,
        max_values: int = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(
            component_type=ComponentType.channel_select,
            custom_id=custom_id,
            placeholder=placeholder,
            default_values=default_values,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            component_id=component_id,
        )
        if channel_types is not MISSING:
            self.channel_types = []
            for channel_type in channel_types:
                if isinstance(channel_type, ChannelType):
                    self.channel_types.append(channel_type)
                else:
                    self.channel_types.append(try_enum(ChannelType, channel_type))
        else:
            self.channel_types = MISSING

    def add_default_value(
        self,
        value_id: int,
        value_type: SelectDefaultValueType | str = SelectDefaultValueType.channel,
    ) -> None:
        return super().add_default_value(value_id, value_type)

    async def wait_for_interaction(
        self,
        bot: Client,
        callback: Callable[[Interaction, tuple[DiscordChannel, ...]], Coroutine[None, None, Any]],
        timeout: float | None = 180.0,
    ):
        def inter_arg_func(inter: Interaction):
            resolved_channels = get_channels_from_interaction(inter)
            resolved_dict = {channel.id: channel for channel in resolved_channels}
            inter.data = cast(inter_payloads.ComponentInteractionData, inter.data)
            if "values" in inter.data:
                return inter, tuple([resolved_dict[int(val)] for val in inter.data["values"]])
            raise ValueError("Interaction data does not include values key.")

        return await self._wait_for_interaction(
            bot, callback, timeout, _inter_arg_func=inter_arg_func
        )

    def to_dict(self) -> comp_payloads.ChannelSelectMenu:
        ret = cast(comp_payloads.ChannelSelectMenu, super().to_dict())
        if self.channel_types is not MISSING:
            ret["channel_types"] = [channel_type.value for channel_type in self.channel_types]

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.ChannelSelectMenu):
        if "default_values" in payload:
            default_values = [
                SelectDefaultValue.from_dict(val_data) for val_data in payload["default_values"]
            ]
        else:
            default_values = MISSING

        return cls(
            custom_id=payload["custom_id"],
            channel_types=payload.get("channel_types", MISSING),
            placeholder=payload.get("placeholder", MISSING),
            default_values=default_values,
            min_values=payload.get("min_values", MISSING),
            max_values=payload.get("max_values", MISSING),
            disabled=payload.get("disabled", MISSING),
            component_id=payload["id"],
        )


ChannelSelectMenu = ChannelSelect


class Section(HolderComponent):  # Component type 9
    """Represents a Section component object.

    Holds up to 3 :class:`.TextDisplay` components, with a single :class:`.Button` or :class:`.Thumbnail` accessory
    displayed to the side.

    .. versionadded:: 3.2

    Parameters
    ----------
    accessory
        Component to display on the side. Currently, Discord only supports :class:`.Button` or :class:`.Thumbnail`
        components to be used as accessories.
    components
        List of components to be primarily displayed. Currently, Discord only supports up to 3 :class:`.TextDisplay`
        components to be used.
    component_id
        Per-message unique ID of the component. If not provided, it will be generated by Discord when sent.
    """

    accessory: Component
    """Component displayed to the side."""
    components: list[TextDisplay | Component]
    """List of components to be primarily displayed."""

    def __init__(
        self,
        accessory: Component,
        components: list[TextDisplay | Component],
        *,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(
            components, component_type=ComponentType.section, component_id=component_id
        )
        self.accessory = accessory

    def get_interactives(self) -> set[InteractiveComponent]:
        ret = super().get_interactives()
        if isinstance(self.accessory, InteractiveComponent):
            ret.add(self.accessory)

        return ret

    def to_dict(self) -> comp_payloads.Section:
        ret = cast(comp_payloads.Section, super().to_dict())
        ret["accessory"] = cast(comp_payloads.Component, self.accessory.to_dict())

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.Section):
        return cls(
            accessory=resolve_component(payload["accessory"]),
            components=[resolve_component(comp_data) for comp_data in payload["components"]],
            component_id=payload["id"],
        )


class TextDisplay(Component):  # Component type 10
    """Represents a Text Display component object.

    Allows you to add text to your component message, supporting markdown and user + role mentions.

    .. versionadded:: 3.2

    Parameters
    ----------
    content
        Text to be displayed.
    component_id
        Per-message unique ID of the component. If not provided, it will be generated by Discord when sent.
    """

    content: str
    """Text to be displayed."""

    def __init__(self, content: str, *, component_id: int = MISSING) -> None:
        super().__init__(component_type=ComponentType.text_display, component_id=component_id)
        self.content = content

    def to_dict(self) -> comp_payloads.TextDisplay:
        ret = cast(comp_payloads.TextDisplay, super().to_dict())
        ret["content"] = self.content
        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.TextDisplay):
        return cls(content=payload["content"], component_id=payload["id"])


class Thumbnail(Component):  # Component type 11
    """Represents a Thumbnail component object.

    Displays a small image, currently only usable in a :class:`.Section` component as the accessory.

    .. versionadded:: 3.2

    Parameters
    ----------
    media
        Media to be displayed.
    description
        Alt text for the media.
    spoiler
        Whether the media should be spoilered/blurred out.
    component_id
        Per-message unique ID of the component. If not provided, it will be generated by Discord when sent.
    """

    media: UnfurledMedia
    """Media to be displayed."""
    description: str  # Can be MISSING
    """Alt text for the media. Can be ``MISSING``"""
    spoiler: bool  # Can be MISSING
    """Whether the media should be spoilered/blurred out. Can be ``MISSING``"""

    def __init__(
        self,
        media: UnfurledMedia,
        *,
        description: str = MISSING,
        spoiler: bool = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(component_type=ComponentType.thumbnail, component_id=component_id)
        self.media = media
        self.description = description
        self.spoiler = spoiler

    def to_dict(self) -> comp_payloads.Thumbnail:
        ret = cast(comp_payloads.Thumbnail, super().to_dict())
        ret["media"] = self.media.to_dict()
        if self.description is not MISSING:
            ret["description"] = self.description

        if self.spoiler is not MISSING:
            ret["spoiler"] = self.spoiler

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.Thumbnail):
        return cls(
            media=UnfurledMedia.from_dict(payload["media"]),
            description=payload.get("description", MISSING),
            spoiler=payload.get("spoiler", MISSING),
            component_id=payload["id"],
        )

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        description: str = MISSING,
        spoiler: bool = MISSING,
        component_id: int = MISSING,
    ):
        """Simple helper method, inits this with an UnfurledMedia set to the given url."""
        return cls(
            media=UnfurledMedia(url),
            description=description,
            spoiler=spoiler,
            component_id=component_id,
        )


class MediaGallery(Component):  # Component type 12
    """Represents a Media Gallery component object.

    Allows displaying between 1 and 10 :class:`.MediaGalleryItem` attachments in an organized gallery format.

    .. versionadded:: 3.2

    Parameters
    ----------
    items
        List of items to display in the gallery.
    component_id
        Per-message unique ID of the component. If not provided, it will be generated by Discord when sent.
    """

    items: list[MediaGalleryItem]
    """List of ``MediaGalleryItem`` objects to display."""

    def __init__(self, items: list[MediaGalleryItem], *, component_id: int = MISSING) -> None:
        super().__init__(component_type=ComponentType.media_gallery, component_id=component_id)
        self.items = items

    def to_dict(self) -> comp_payloads.MediaGallery:
        ret = cast(comp_payloads.MediaGallery, super().to_dict())
        ret["items"] = [media_item.to_dict() for media_item in self.items]
        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.MediaGallery):
        return cls(
            items=[MediaGalleryItem.from_dict(media_data) for media_data in payload["items"]],
            component_id=payload["id"],
        )


class File(Component):
    """Represents a File component object.

    Allows referencing/displaying a file that was uploaded as an attachment to the message.

    .. versionadded:: 3.2

    Parameters
    ----------
    file
        Attachment/media to be displayed, only supports ``attachment://<filename>`` style references.
    spoiler
        Whether the media should be spoilered/blurred out.
    component_id
        Per-message unique ID of the component. If not provided, it will be generated by Discord when sent.
    """

    file: UnfurledMedia
    """Attachment to be displayed."""
    spoiler: bool  # Can be MISSING
    """Whether the attachment should be spoilered/blurred out. Can be ``MISSING``"""

    def __init__(
        self, file: UnfurledMedia, *, spoiler: bool = MISSING, component_id: int = MISSING
    ) -> None:
        super().__init__(component_type=ComponentType.file, component_id=component_id)
        self.file = file
        self.spoiler = spoiler

    def to_dict(self) -> comp_payloads.File:
        ret = cast(comp_payloads.File, super().to_dict())
        ret["file"] = self.file.to_dict()
        if self.spoiler is not MISSING:
            ret["spoiler"] = self.spoiler

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.File):
        return cls(
            file=UnfurledMedia.from_dict(payload["file"]),
            spoiler=payload.get("spoiler", MISSING),
            component_id=payload["id"],
        )

    @classmethod
    def from_url(cls, url: str, *, spoiler: bool = MISSING, component_id: int = MISSING):
        """Simple helper method, inits this with an UnfurledMedia set to the given url.

        Must use the ``attachment://<filename>`` syntax
        """
        return cls(file=UnfurledMedia(url), spoiler=spoiler, component_id=component_id)

    @classmethod
    def from_file(cls, file: DiscordFile, *, spoiler: bool = MISSING, component_id: int = MISSING):
        """Simple helper method. inits this with a DiscordFile."""
        media_name = f"attachment://{file.filename}"
        return cls(file=UnfurledMedia(media_name), spoiler=spoiler, component_id=component_id)


class Separator(Component):  # Component type 14
    """Represents a Separator component object.

    Adds vertical padding and optionally a visual divider between components.

    .. versionadded:: 3.2

    Parameters
    ----------
    divider
        Whether a visual divider should be displayed.
    spacing
        Size of the separator padding.
    component_id
        Per-message unique ID of the component. If not provided, it will be generated by Discord when sent.
    """

    divider: bool  # Can be MISSING
    """Whether a visual divider should be displayed. Can be ``MISSING``"""
    spacing: SeparatorSpacingSize  # Can be MISSING
    """Size of the separator padding. Can be ``MISSING``"""

    def __init__(
        self,
        divider: bool = MISSING,
        spacing: SeparatorSpacingSize | Literal[1, 2] = MISSING,
        *,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(component_type=ComponentType.separator, component_id=component_id)

        self.divider = divider
        if spacing is not MISSING:
            if isinstance(spacing, SeparatorSpacingSize):
                self.spacing = spacing
            else:
                self.spacing = try_enum(SeparatorSpacingSize, spacing)
        else:
            self.spacing = MISSING

    def to_dict(self) -> comp_payloads.Separator:
        ret = cast(comp_payloads.Separator, super().to_dict())
        if self.divider is not MISSING:
            ret["divider"] = self.divider

        if self.spacing is not MISSING:
            ret["spacing"] = self.spacing.value

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.Separator):
        return cls(
            divider=payload.get("divider", MISSING),
            spacing=payload.get("spacing", MISSING),
            component_id=payload["id"],
        )


class Container(HolderComponent):  # Component type 17
    """Represents a Container component object.

    Holds other components with a visually distinct background and can have an accent color on the side, similar
    to :class:`.Embed` objects.

    .. versionadded:: 3.2

    Parameters
    ----------
    components
        List of components to display.
    accent_color
        Accent color to display on the side.
    spoiler
        Whether the container should be spoilered/blurred out.
    component_id
        Per-message unique ID of the component. If not provided, it will be generated by Discord when sent.
    """

    accent_color: int | None  # Can be MISSING
    """Accent color displayed on the side. Can be ``MISSING``"""
    spoiler: bool  # Can be MISSING
    """Whether the container should be spoilered/blurred out. Can be ``MISSING``"""

    def __init__(
        self,
        components: list[Component],
        accent_color: int | None = MISSING,
        spoiler: bool = MISSING,
        *,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(
            components, component_type=ComponentType.container, component_id=component_id
        )
        self.accent_color = accent_color
        self.spoiler = spoiler

    def to_dict(self) -> comp_payloads.Container:
        ret = cast(comp_payloads.Container, super().to_dict())
        if self.accent_color is not MISSING:
            ret["accent_color"] = self.accent_color

        if self.spoiler is not MISSING:
            ret["spoiler"] = self.spoiler

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.Container):
        return cls(
            components=[resolve_component(comp_data) for comp_data in payload["components"]],
            accent_color=payload.get("accent_color", MISSING),
            spoiler=payload.get("spoiler", MISSING),
            component_id=payload["id"],
        )


class SelectOption:
    """Represents an option for the selects that use it.

    Currently only used by :class:`.StringSelect`.

    .. versionadded:: 2.0

    Parameters
    ----------
    label
        The label of the option. This is displayed to users.
        Can only be up to 100 characters.
    value
        The value of the option. This is not displayed to users.
        If not provided when constructed then it defaults to the
        label. Can only be up to 100 characters.
    description
        An additional description of the option, if any.
        Can only be up to 100 characters.
    emoji
        The emoji of the option, if available.
    default
        Whether this option is selected by default.
    """

    label: str
    """User-facing name of the option."""
    value: str
    """Dev-defined/Bot-facing value of the option."""
    description: str  # Can be MISSING
    """Description of the option. Can be ``MISSING``"""
    emoji: PartialEmoji  # Can be MISSING
    """The emoji of the option. Can be ``MISSING``"""
    default: bool  # Can be MISSING
    """Whether this option is selected by default. Can be ``MISSING``"""

    def __init__(
        self,
        label: str,
        value: str = MISSING,  # This is to prevent breaking changes.
        *,
        description: str = MISSING,
        emoji: PartialEmoji | Emoji | str = MISSING,
        default: bool = MISSING,
    ) -> None:
        self.label = label
        self.value = value if value is not MISSING else label
        self.description = description

        if isinstance(emoji, str):
            self.emoji = PartialEmoji.from_str(emoji)
        elif isinstance(emoji, _EmojiTag):
            self.emoji = emoji._to_partial()
        else:
            self.emoji = emoji

        self.default = default

    def to_dict(self) -> comp_payloads.SelectOption:
        ret: comp_payloads.SelectOption = {"label": self.label, "value": self.value}
        if self.description is not MISSING:
            ret["description"] = self.description

        if self.emoji is not MISSING:
            emoji_payload = cast(emoji_payloads.PartialEmoji, self.emoji.to_dict())
            ret["emoji"] = emoji_payload

        if self.default is not MISSING:
            ret["default"] = self.default

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.SelectOption):
        emoji = PartialEmoji.from_dict(payload["emoji"]) if "emoji" in payload else MISSING
        return cls(
            payload["label"],
            payload["value"],
            description=payload.get("description", MISSING),
            emoji=emoji,
            default=payload.get("default", MISSING),
        )


class SelectDefaultValue:
    """Represents a default value for the selects that use it.

    Used in :class:`.UserSelect`, :class:`.RoleSelect`, :class:`.MentionableSelect`, and :class:`.ChannelSelect`.

    .. versionadded:: 3.2

    Parameters
    ----------
    value_id
        ID/Snowflake of the default value.
    value_type
        Type of object the ``value_id`` corresponds to.
    """

    id: int
    """ID/Snowflake"""
    type: SelectDefaultValueType
    """Type of object that :attr:`.id` refers to."""

    def __init__(
        self,
        value_id: int,
        value_type: SelectDefaultValueType | Literal["user", "role", "channel"] | str,
    ) -> None:
        self.id = value_id
        if isinstance(value_type, SelectDefaultValueType):
            self.type = value_type
        else:
            self.type = try_enum(SelectDefaultValueType, value_type)

    def to_dict(self) -> comp_payloads.SelectDefaultValue:
        return {"id": self.id, "type": self.type.value}

    @classmethod
    def from_dict(cls, payload: comp_payloads.SelectDefaultValue):
        return cls(value_id=int(payload["id"]), value_type=payload["type"])


class UnfurledMedia:
    """Represents a reference to some media.

    The referenced media can either be an external link or an attachment included in the message.

    .. versionadded:: 3.2

    Parameters
    ----------
    url
        Source of the media. Can either be an arbitrary URL, or use the ``attachment://<filename>`` syntax to
        reference an included attachment.
    """

    url: str
    """Source of the media."""
    proxy_url: str  # Can be MISSING
    """Proxy URL of the media, provided by Discord. Can be ``MISSING``"""
    height: int | None  # Can be MISSING
    """Height of the media, provided by Discord. Can be ``MISSING``"""
    width: int | None  # Can be MISSING
    """Width of the media, provided by Discord. Can be ``MISSING``"""
    content_type: str  # Can be MISSING
    """Type of the media, provided by Discord. Can be ``MISSING``"""
    attachment_id: int
    """ID of the referenced attachment, provided by Discord if the media references an attachment. Can be ``MISSING``"""

    def __init__(
        self,
        url: str,
        *,
        proxy_url: str = MISSING,
        height: int | None = MISSING,
        width: int | None = MISSING,
        content_type: str = MISSING,
        attachment_id: int = MISSING,
    ) -> None:
        self.url = url
        self.proxy_url = proxy_url
        self.height = height
        self.width = width
        self.content_type = content_type
        self.attachment_id = attachment_id

    def to_dict(self) -> comp_payloads.UnfurledMedia:
        # Currently, the 4 other attributes are all ignored by the API, but provided in responses.
        return {"url": self.url}

    @classmethod
    def from_dict(cls, payload: comp_payloads.UnfurledMedia):
        if (attachment_id := payload.get("attachment_id", MISSING)) is not MISSING:
            attachment_id = int(attachment_id)

        return cls(
            url=payload["url"],
            proxy_url=payload.get("proxy_url", MISSING),
            height=payload.get("height", MISSING),
            width=payload.get("width", MISSING),
            content_type=payload.get("content_type", MISSING),
            attachment_id=attachment_id,
        )


class MediaGalleryItem:
    """Represents an item in a :class:`MediaGallery` component.

    Essentially acts as a wrapper around :class:`UnfurledMedia` with the ability to add a description and/or
    spoiler it.

    .. versionadded:: 3.2

    Parameters
    ----------
    media
        Media to be displayed.
    description
        Alt text for the media.
    spoiler
        Whether the media should be spoilered/blurred out.
    """

    media: UnfurledMedia
    """Media to be displayed."""
    description: str  # Can be MISSING
    """Alt text for the media. Can be ``MISSING``"""
    spoiler: bool  # Can be MISSING
    """Whether the media should be spoilered/blurred out. Can be ``MISSING``"""

    def __init__(
        self, media: UnfurledMedia, *, description: str = MISSING, spoiler: bool = MISSING
    ) -> None:
        self.media = media
        self.description = description
        self.spoiler = spoiler

    def to_dict(self) -> comp_payloads.MediaGalleryItem:
        ret: comp_payloads.MediaGalleryItem = {"media": self.media.to_dict()}
        if self.description is not MISSING:
            ret["description"] = self.description

        if self.spoiler is not MISSING:
            ret["spoiler"] = self.spoiler

        return ret

    @classmethod
    def from_dict(cls, payload: comp_payloads.MediaGalleryItem):
        return cls(
            media=UnfurledMedia.from_dict(payload["media"]),
            description=payload.get("description", MISSING),
            spoiler=payload.get("spoiler", MISSING),
        )

    @classmethod
    def from_url(cls, url: str, *, description: str = MISSING, spoiler: bool = MISSING):
        """Simple helper method, inits this with an UnfurledMedia set to the given url."""
        return cls(media=UnfurledMedia(url), description=description, spoiler=spoiler)


def resolve_component(payload: comp_payloads.Component) -> Component:
    match payload["type"]:
        case 1:
            return ActionRow.from_dict(payload)
        case 2:
            return Button.from_dict(payload)
        case 3:
            return StringSelect.from_dict(payload)
        case 4:
            return TextInput.from_dict(payload)
        case 5:
            return UserSelect.from_dict(payload)
        case 6:
            return RoleSelect.from_dict(payload)
        case 7:
            return MentionableSelect.from_dict(payload)
        case 8:
            return ChannelSelect.from_dict(payload)
        case 9:
            return Section.from_dict(payload)
        case 10:
            return TextDisplay.from_dict(payload)
        case 11:
            return Thumbnail.from_dict(payload)
        case 12:
            return MediaGallery.from_dict(payload)
        case 13:
            return File.from_dict(payload)
        case 14:
            return Separator.from_dict(payload)
        case 17:
            return Container.from_dict(payload)
        case _:  # Just in case new components are added that we don't have yet.
            return Component.from_dict(payload)


def get_channels_from_interaction(
    interaction: Interaction,
) -> list[DiscordChannel]:
    ret = []
    state = interaction._state
    data = cast(inter_payloads.ApplicationCommandInteractionData, interaction.data)
    if "resolved" in data and "channels" in data["resolved"]:
        channel_payloads = data["resolved"]["channels"]
        for ch_id, ch_data in channel_payloads.items():
            if channel := state.get_channel(int(ch_id)):
                ret.append(channel)
                continue

            # Attempt to actually resolve the channels
            ch_class, ch_type = _threaded_channel_factory(ch_data["type"])
            if ch_class is not None:
                if ch_type in (ChannelType.group, ChannelType.private):
                    # the factory will be a DMChannel or GroupChannel here
                    channel = ch_class(me=interaction.client.user, data=ch_data, state=state)  # type: ignore
                else:
                    guild_id = int(ch_data["guild_id"])  # type: ignore
                    guild = state._get_guild(guild_id) or Object(id=guild_id)
                    channel = ch_class(guild=guild, state=state, data=ch_data)  # type: ignore

                ret.append(channel)
            else:
                pass  # TODO: Raise error? Log.warn?

    return ret
