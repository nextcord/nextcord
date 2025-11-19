# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, TypeVar

from ..components import TextDisplay as TextDisplayComponent
from ..enums import ComponentType
from .item import Item

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView

V_co = TypeVar("V_co", bound="LayoutView", covariant=True)

__all__ = ("TextDisplay",)


class TextDisplay(Item[V_co]):
    """Represents a UI text display.

    This is a top-level layout component that can only be used on :class:`LayoutView`,
    :class:`Section`, :class:`Container`, or :class:`Modal`.

        .. versionadded:: 3.12

    Parameters
    ----------
    content: :class:`str`
        The content of this text display. Up to 4000 characters.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.

    Attributes
    ----------
    content: :class:`str`
        The content that this display shows.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __item_repr_attributes__ = ("content", "id")

    def __init__(self, content: str, *, id: Optional[int] = None) -> None:
        super().__init__()
        self.content: str = content
        self.id = id

    def to_component_dict(self) -> Dict[str, Any]:
        base = {
            "type": self.type.value,
            "content": self.content,
        }
        if self.id is not None:
            base["id"] = self.id
        return base

    @property
    def width(self) -> int:
        return 5

    @property
    def type(self) -> Literal[ComponentType.text_display]:
        return ComponentType.text_display

    def _is_v2(self) -> bool:
        return True

    @classmethod
    def from_component(cls, component: TextDisplayComponent) -> Self:
        return cls(
            content=component.content,
            id=component.id,
        )

