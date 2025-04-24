# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

from .enums import ButtonStyle, ComponentType, InteractionType, try_enum
from .utils import MISSING

if TYPE_CHECKING:
    from typing import Any, Awaitable, Callable, Literal

    from .client import Client
    from .interactions import Interaction
    from .partial_emoji import PartialEmoji


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
    """Base class for components that should have an async callback associated with them.

    This class is intended to be abstract and not instantiated.
    """

    callback: Callable[[Interaction], Awaitable[Any]] | None
    custom_id: str  # Can be MISSING

    def __init__(
        self,
        callback: Callable[[Interaction], Awaitable[Any]] | None,
        custom_id: str | None = MISSING,
        *,
        component_type: int | ComponentType,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(component_type=component_type, component_id=component_id)
        self.callback = callback
        if custom_id is None:
            self.custom_id = os.urandom(16).hex()  # TODO: Use UUID lib instead?
        else:
            self.custom_id = custom_id

    # TODO: I'm vaguely unhappy with this entire thing. I'm not sure if "InteractiveComponent" should even exist, but
    #  not having some sort of callback-able class seems too low level/simple IMO.
    async def _wait_for_interaction(self, bot: Client, timeout: float | None = 180.0) -> None:
        if self.callback is None:
            raise ValueError("Missing callback to trigger on matching interaction.")
        if self.custom_id is MISSING:
            raise ValueError("Missing custom_id to match with interaction.")

        def inter_check(inter: Interaction[Client]) -> bool:
            return (
                inter.type == InteractionType.component
                and inter.data
                and inter.data.get("custom_id", None) == self.custom_id
            )

        try:
            interaction = await bot.wait_for("interaction", check=inter_check, timeout=timeout)
        except asyncio.TimeoutError:
            pass
        else:
            await self.callback(interaction)


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
class ButtonComponent(InteractiveComponent):
    style: ButtonStyle
    label: str  # Can be MISSING
    emoji: PartialEmoji  # Can be MISSING
    sku_id: int  # Can be MISSING
    url: str  # Can be MISSING
    disabled: bool  # Can be MISSING

    def __init__(
        self,
        style: ButtonStyle | int,
        callback: Callable[[Interaction], Awaitable[Any]] | None = None,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        custom_id: str | None = MISSING,
        sku_id: int = MISSING,
        url: str = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(
            callback, custom_id, component_type=ComponentType.button, component_id=component_id
        )
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

        # Normally custom_id is required, but Link (style 5) and Premium (style 6) buttons are not allowed to have it.
        if self.custom_id is not MISSING:
            ret["custom_id"] = self.custom_id

        if self.sku_id is not MISSING:
            ret["sku_id"] = self.sku_id

        if self.url is not MISSING:
            ret["url"] = self.url

        if self.disabled is not MISSING:
            ret["disabled"] = self.disabled

        return ret

    @classmethod
    def as_primary(  # Style 1
        cls,
        custom_id: str | None = None,
        callback: Callable[[Interaction], Awaitable[Any]] | None = None,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ):
        return cls(
            style=ButtonStyle.primary,
            callback=callback,
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
        callback: Callable[[Interaction], Awaitable[Any]] | None = None,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ):
        return cls(
            style=ButtonStyle.secondary,
            callback=callback,
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
        callback: Callable[[Interaction], Awaitable[Any]] | None = None,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ):
        return cls(
            style=ButtonStyle.success,
            callback=callback,
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
        callback: Callable[[Interaction], Awaitable[Any]] | None = None,
        *,
        label: str = MISSING,
        emoji: PartialEmoji = MISSING,
        disabled: bool = MISSING,
        component_id: int = MISSING,
    ):
        return cls(
            style=ButtonStyle.danger,
            callback=callback,
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
            callback=None,
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
            callback=None,
            sku_id=sku_id,
            disabled=disabled,
            component_id=component_id,
        )


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
