# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
from typing import TYPE_CHECKING, cast

from .application_command import (
    get_users_from_interaction,
)  # TODO: Move this somewhere else, this is dumb.
from .enums import ButtonStyle, ComponentType, InteractionType, try_enum
from .types import interactions as inter_payloads
from .utils import MISSING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Coroutine, Literal

    from .client import Client
    from .interactions import Interaction
    from .member import Member
    from .partial_emoji import PartialEmoji
    from .user import User


# TODO: This is just a draft, ignore the fact that it's not in the components file rn. I don't want to break views or
#  whatever else relies on v1/normal components


class Component:
    """Base class for components.

    This class is intended to be abstract and not instantiated.
    """

    type: ComponentType
    id: int  # Can be MISSING

    def __init__(self, *, component_type: int | ComponentType, component_id: int = MISSING) -> None:
        if isinstance(component_type, ComponentType):
            self.type = component_type
        else:
            self.type = try_enum(ComponentType, component_type)

        self.id = component_id

    def to_dict(self) -> dict:
        ret = {"type": self.type.value}
        if self.id is not MISSING:
            ret["id"] = self.id

        return ret


class InteractiveComponent(Component):
    """Base class for components that have a custom_id and should have callback-related helper funcs.

    This class is intended to be abstract and not instantiated.
    """

    custom_id: str  # Can be MISSING

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
        callback: Callable[..., Coroutine[None, None, Any]],
        timeout: float | None = 180.0,
    ):
        return await self._wait_for_interaction(
            bot, callback, timeout, _inter_arg_func=lambda i: (i,)
        )

    def to_dict(self) -> dict:
        ret = super().to_dict()
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


class HolderComponent(Component):
    """Base class for components with the "components" attribute that are designed to hold other components.

    This class is intended to be abstract and not instantiated.
    """

    components: list[Component]

    def __init__(
        self,
        components: list | None = None,
        *,
        component_type: ComponentType | int,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(component_type=component_type, component_id=component_id)
        if components is None:
            self.components = []
        else:
            self.components = components

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["components"] = [comp.to_dict() for comp in self.components]
        return ret

    def get_interactives(self) -> set[InteractiveComponent]:
        return get_interactive_components(self.components)


class ActionRow(HolderComponent):  # Component type 1
    components: list[Component]

    def __init__(self, components: list | None = None, *, component_id: int = MISSING) -> None:
        super().__init__(
            components, component_type=ComponentType.action_row, component_id=component_id
        )


# TODO: Think about moving Premium and Link buttons to a "NoninteractiveButtonComponent" thing?
class ButtonComponent(InteractiveComponent):  # Component type 2
    style: ButtonStyle
    label: str  # Can be MISSING
    emoji: PartialEmoji  # Can be MISSING
    sku_id: int  # Can be MISSING
    url: str  # Can be MISSING
    disabled: bool  # Can be MISSING

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

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["style"] = self.style.value
        if self.label is not MISSING:
            ret["label"] = self.label

        if self.emoji is not MISSING:
            ret["emoji"] = self.emoji.to_dict()

        if self.sku_id is not MISSING:
            ret["sku_id"] = self.sku_id

        if self.url is not MISSING:
            ret["url"] = self.url

        if self.disabled is not MISSING:
            ret["disabled"] = self.disabled

        return ret

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
        return cls(
            style=ButtonStyle.premium,
            sku_id=sku_id,
            disabled=disabled,
            component_id=component_id,
        )


class UserSelect(InteractiveComponent):
    placeholder: str  # Can be MISSING
    default_values: list  # Can be MISSING  # TODO: Fill the list part in.
    min_values: int  # Can be MISSING
    max_values: int  # Can be MISSING
    disabled: bool  # Can be MISSING

    def __init__(
        self,
        custom_id: str | None = None,
        *,
        placeholder: str = MISSING,
        default_values: list = MISSING,
        min_values: int = MISSING,
        max_values: int = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(
            custom_id, component_type=ComponentType.user_select, component_id=component_id
        )
        self.placeholder = placeholder
        self.default_values = default_values
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled

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
            resolved_peeps = get_users_from_interaction(inter._state, inter)
            resolved_dict = {peep.id: peep for peep in resolved_peeps}
            inter.data = cast(inter_payloads.ComponentInteractionData, inter.data)
            if "values" in inter.data:
                return inter, tuple([resolved_dict[int(val)] for val in inter.data["values"]])
            raise ValueError("Interaction data does not include values key.")

        return await super()._wait_for_interaction(
            bot, callback, timeout, _inter_arg_func=inter_arg_func
        )

    def to_dict(self) -> dict:
        ret = super().to_dict()
        if self.placeholder is not MISSING:
            ret["placeholder"] = self.placeholder

        # if self.default_values is not MISSING:  # TODO: Add this.

        if self.min_values is not MISSING:
            ret["min_values"] = self.min_values

        if self.max_values is not MISSING:
            ret["max_values"] = self.max_values

        if self.disabled is not MISSING:
            ret["disabled"] = self.disabled

        return ret


class Section(HolderComponent):  # Component type 9
    accessory: Component

    def __init__(
        self,
        accessory: Component,
        components: list[TextDisplay] | None = None,
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

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["accessory"] = self.accessory.to_dict()

        return ret


class TextDisplay(Component):  # Component type 10
    content: str

    def __init__(self, content: str, *, component_id: int = MISSING) -> None:
        super().__init__(component_type=ComponentType.text_display, component_id=component_id)
        self.content = content

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["content"] = self.content
        return ret


class Thumbnail(Component):  # Component type 11
    media: str  # TODO: Unfurled media + attachments support plz.
    description: str  # Can be MISSING
    spoiler: bool  # Can be MISSING

    def __init__(
        self,
        media: str,
        description: str = MISSING,
        spoiler: bool = MISSING,
        *,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(component_type=ComponentType.thumbnail, component_id=component_id)
        self.media = media
        self.description = description
        self.spoiler = spoiler

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["media"] = {"url": self.media}
        if self.description is not MISSING:
            ret["description"] = self.description

        if self.spoiler is not MISSING:
            ret["spoiler"] = self.spoiler

        return ret


class Separator(Component):
    divider: bool  # Can be MISSING
    spacing: Literal[1, 2]  # Can be MISSING  # TODO: Make enum for this?

    def __init__(
        self,
        divider: bool = MISSING,
        spacing: Literal[1, 2] = MISSING,
        *,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(component_type=ComponentType.separator, component_id=component_id)
        self.divider = divider
        self.spacing = spacing

    def to_dict(self) -> dict:
        ret = super().to_dict()
        if self.divider is not MISSING:
            ret["divider"] = self.divider

        if self.spacing is not MISSING:
            ret["spacing"] = self.spacing

        return ret


class Container(HolderComponent):  # Component type 17
    accent_color: int | None  # Can be MISSING
    spoiler: bool  # Can be MISSING

    def __init__(
        self,
        components: list[Component] | None = None,
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

    def to_dict(self) -> dict:
        ret = super().to_dict()
        if self.accent_color is not MISSING:
            ret["accent_color"] = self.accent_color

        if self.spoiler is not MISSING:
            ret["spoiler"] = self.spoiler

        return ret


class UnfurledMedia:
    pass
