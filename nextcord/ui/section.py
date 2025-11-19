# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    TypeVar,
    Union,
    cast,
)

from ..enums import ComponentType
from ..utils import get as _utils_get
from .item import Item
from .text_display import TextDisplay
from .view import LayoutView, _component_to_item

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..components import SectionComponent

V_co = TypeVar("V_co", bound="LayoutView", covariant=True)

__all__ = ("Section",)


class Section(Item[V_co]):
    r"""Represents a UI section.

    This is a top-level layout component that can only be used on :class:`LayoutView`.

        .. versionadded:: 3.12

    Parameters
    ----------
    \*children: Union[:class:`str`, :class:`TextDisplay`]
        The text displays of this section. Up to 3.
    accessory: :class:`Item`
        The section accessory. This is usually either a :class:`Button` or :class:`Thumbnail`.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.

    Attributes
    ----------
    children: List[:class:`Item`]
        The list of children attached to this section.
    accessory: :class:`Item`
        The section's accessory.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __item_repr_attributes__ = (
        "accessory",
        "id",
    )

    __discord_ui_section__: ClassVar[bool] = True

    def __init__(
        self,
        *children: Union[Item[V_co], str],
        accessory: Item[V_co],
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._children: List[Item[V_co]] = []
        for child in children:
            self.add_item(child)

        accessory._parent = self
        self._accessory: Item[V_co] = accessory
        self.id = id

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} children={len(self._children)} accessory={self._accessory!r}>"

    @property
    def type(self) -> Literal[ComponentType.section]:
        return ComponentType.section

    @property
    def children(self) -> List[Item[V_co]]:
        """List[:class:`Item`]: The list of children attached to this section."""
        return self._children.copy()

    @property
    def width(self) -> int:
        return 5

    @property
    def _total_count(self) -> int:
        return 2 + len(self._children)

    @property
    def accessory(self) -> Item[V_co]:
        """:class:`Item`: The section's accessory."""
        return self._accessory

    @accessory.setter
    def accessory(self, value: Item[V_co]) -> None:
        if not isinstance(value, Item):
            raise TypeError(f"Expected an Item, got {value.__class__.__name__!r} instead")

        value._update_view(self.view)
        value._parent = self
        self._accessory = value

    def _is_v2(self) -> bool:
        return True

    def _swap_item(self, base: Item, new: Item, custom_id: str) -> None:
        if self.accessory.is_dispatchable() and getattr(self.accessory, "custom_id", None) == custom_id:
            self.accessory = new

    def walk_children(self) -> Generator[Item[V_co], None, None]:
        """An iterator that recursively walks through all the children of this section
        and its children, if applicable. This includes the `accessory`.

        Yields
        ------
        :class:`Item`
            An item in this section.
        """

        yield from self.children
        yield self.accessory

    def _update_view(self, view) -> None:
        self._view = view
        self.accessory._view = view
        for child in self._children:
            child._view = view

    def _has_children(self) -> bool:
        return True

    def content_length(self) -> int:
        """:class:`int`: Returns the total length of all text content in this section."""
        return sum(len(item.content) for item in self._children if isinstance(item, TextDisplay))

    def add_item(self, item: Union[str, Item[Any]]) -> Self:
        """Adds an item to this section.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: Union[:class:`str`, :class:`Item`]
            The item to append, if it is a string it automatically wrapped around
            :class:`TextDisplay`.

        Raises
        ------
        TypeError
            An :class:`Item` or :class:`str` was not passed.
        ValueError
            Maximum number of children has been exceeded (3) or (40)
            for the entire view.
        """

        if len(self._children) >= 3:
            raise ValueError("maximum number of children exceeded (3)")

        if not isinstance(item, (Item, str)):
            raise TypeError(f"expected Item or str not {item.__class__.__name__}")

        if self._view:
            self._view._add_count(1)

        item = item if isinstance(item, Item) else TextDisplay(item)
        item._update_view(self.view)
        item._parent = self
        self._children.append(item)

        return self

    def remove_item(self, item: Item[Any]) -> Self:
        """Removes an item from this section.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: :class:`Item`
            The item to remove from the section.
        """

        try:
            self._children.remove(item)
        except ValueError:
            pass
        else:
            if self._view:
                self._view._add_count(-1)

        return self

    def find_item(self, id: int, /) -> Optional[Item[V_co]]:
        """Gets an item with :attr:`Item.id` set as ``id``, or ``None`` if
        not found.

        .. warning::

            This is **not the same** as ``custom_id``.

        Parameters
        ----------
        id: :class:`int`
            The ID of the component.

        Returns
        -------
        Optional[:class:`Item`]
            The item found, or ``None``.
        """
        return _utils_get(self.walk_children(), id=id)

    def clear_items(self) -> Self:
        """Removes all the items from the section.

        This function returns the class instance to allow for fluent-style
        chaining.
        """
        if self._view:
            self._view._add_count(-len(self._children))

        self._children.clear()
        return self

    @classmethod
    def from_component(cls, component: SectionComponent) -> Self:
        if component.accessory is None:
            raise ValueError("Section component must have an accessory")
        accessory = _component_to_item(component.accessory, None)
        self = cls(id=component.id, accessory=accessory)
        self.id = component.id
        self._children = [_component_to_item(c, self) for c in component.children]

        return self

    def to_components(self) -> List[Dict[str, Any]]:
        return [cast(Dict[str, Any], component.to_component_dict()) for component in self._children]

    def to_component_dict(self) -> Dict[str, Any]:
        data = {
            "type": self.type.value,
            "components": self.to_components(),
            "accessory": self.accessory.to_component_dict(),
        }
        if self.id is not None:
            data["id"] = self.id
        return data

