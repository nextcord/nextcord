# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING

from .enums import ComponentType
from .utils import MISSING

if TYPE_CHECKING:
    from typing import Literal


# TODO: This is just a draft, ignore the fact that it's not in the components file rn. I don't want to break views or
#  whatever else relies on v1/normal components


class Component:
    type: int
    id: int

    def __init__(self, *, component_type: int | ComponentType, component_id: int = MISSING) -> None:
        if isinstance(component_type, ComponentType):
            self.type = component_type.value
        else:
            self.type = component_type

        self.id = component_id

    def to_dict(self) -> dict:
        ret = {"type": self.type}
        if self.id is not MISSING:
            ret["id"] = self.id

        return ret


class ActionRow(Component):  # Component type 1
    components: list[Component]

    def __init__(self, components: list | None = None, *, component_id: int = MISSING) -> None:
        super().__init__(component_type=ComponentType.action_row, component_id=component_id)
        if components is not None:
            self.components = components
        else:
            self.components = []

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["components"] = [comp.to_dict() for comp in self.components]
        return ret


class Section(Component):  # Component type 9
    accessory: Component
    components: list[TextDisplay]

    def __init__(
        self,
        accessory: Component,
        components: list[TextDisplay] | None = None,
        *,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(component_type=ComponentType.section, component_id=component_id)
        self.accessory = accessory
        if components is None:
            self.components = []
        else:
            self.components = components

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["components"] = [comp.to_dict() for comp in self.components]
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
    media: str  # Unfurled media + attachments support plz.
    description: str
    spoiler: bool

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
    divider: bool
    spacing: Literal[1, 2]

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


class Container(Component):  # Component type 17
    components: list[Component]
    accent_color: int | None
    spoiler: bool

    def __init__(
        self,
        components: list[Component] | None = None,
        accent_color: int | None = MISSING,
        spoiler: bool = MISSING,
        *,
        component_id: int = MISSING,
    ) -> None:
        super().__init__(component_type=ComponentType.container, component_id=component_id)
        if components is None:
            self.components = []
        else:
            self.components = components

        self.accent_color = accent_color
        self.spoiler = spoiler

    def to_dict(self) -> dict:
        ret = super().to_dict()
        ret["components"] = [comp.to_dict() for comp in self.components]
        if self.accent_color is not MISSING:
            ret["accent_color"] = self.accent_color

        if self.spoiler is not MISSING:
            ret["spoiler"] = self.spoiler

        return ret


class UnfurledMedia:
    pass
