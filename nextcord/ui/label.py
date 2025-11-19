# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Generator, Literal, Optional, Tuple, TypeVar

from ..components import LabelComponent
from ..enums import ComponentType
from ..utils import MISSING
from .item import Item
from .view import View as BaseView, _component_to_item

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = ("Label",)

V_co = TypeVar("V_co", bound="BaseView", covariant=True)


class Label(Item[V_co]):
    """Represents a UI label within a modal.

    This is a top-level layout component that can only be used on :class:`Modal`.

        .. versionadded:: 3.12

    Parameters
    ----------
    text: :class:`str`
        The text to display above the input field.
        Can only be up to 45 characters.
    description: Optional[:class:`str`]
        The description text to display right below the label text.
        Can only be up to 100 characters.
    component: :class:`Item`
        The component to display below the label.
    id: Optional[:class:`int`]
        The ID of the component. This must be unique across the view.

    Attributes
    ----------
    text: :class:`str`
        The text to display above the input field.
    description: Optional[:class:`str`]
        The description text to display right below the label text.
    component: :class:`Item`
        The component to display below the label.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        "text",
        "description",
        "component",
    )

    def __init__(
        self,
        *,
        text: str,
        component: Item[V_co],
        description: Optional[str] = None,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.component: Item[V_co] = component
        self.text: str = text
        self.description: Optional[str] = description
        self.id = id

    @property
    def width(self) -> int:
        return 5

    def _has_children(self) -> bool:
        return True

    def walk_children(self) -> Generator[Item[V_co], None, None]:
        yield self.component

    def to_component_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "type": ComponentType.label.value,
            "label": self.text,
            "component": self.component.to_component_dict(),
        }
        if self.description:
            payload["description"] = self.description
        if self.id is not None:
            payload["id"] = self.id
        return payload

    @classmethod
    def from_component(cls, component: LabelComponent) -> Self:
        self = cls(
            text=component.label,
            component=MISSING,
            description=component.description,
        )
        if component.component:
            self.component = _component_to_item(component.component, self)
        return self

    @property
    def type(self) -> Literal[ComponentType.label]:
        return ComponentType.label

    def is_dispatchable(self) -> bool:
        return False

    @property
    def _total_count(self) -> int:
        return 2
