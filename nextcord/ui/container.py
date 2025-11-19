# SPDX-License-Identifier: MIT

from __future__ import annotations

import copy
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

from ..colour import Color, Colour
from ..enums import ComponentType
from ..utils import get as _utils_get
from .item import ContainedItemCallbackType as ItemCallbackType, Item, _ItemCallback
from .text_display import TextDisplay
from .view import LayoutView, _component_to_item

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..components import Container as ContainerComponent

S_co = TypeVar("S_co", bound="Container", covariant=True)
V_co = TypeVar("V_co", bound="LayoutView", covariant=True)

__all__ = ("Container",)


class Container(Item[V_co]):
    r"""Represents a UI container.

    This is a top-level layout component that can only be used on :class:`LayoutView`
    and can contain :class:`ActionRow`\s, :class:`TextDisplay`\s, :class:`Section`\s,
    :class:`MediaGallery`\s, :class:`File`\s, and :class:`Separator`\s in it.

    This can be inherited.

        .. versionadded:: 3.12

    Parameters
    ----------
    \*children: :class:`Item`
        The initial children of this container.
    accent_colour: Optional[Union[:class:`.Colour`, :class:`int`]]
        The colour of the container. Defaults to ``None``.
    accent_color: Optional[Union[:class:`.Colour`, :class:`int`]]
        The color of the container. Defaults to ``None``.
    spoiler: :class:`bool`
        Whether to flag this container as a spoiler. Defaults
        to ``False``.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.

    Attributes
    ----------
    children: List[:class:`Item`]
        The children of this container.
    spoiler: :class:`bool`
        Whether this container is flagged as a spoiler.
    accent_colour: Optional[Union[:class:`Colour`, :class:`int`]]
        The colour of the container, or ``None``.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __container_children_items__: ClassVar[Dict[str, Union[ItemCallbackType[Self, Any], Item[Any]]]] = {}
    __discord_ui_container__: ClassVar[bool] = True
    __item_repr_attributes__ = (
        "accent_colour",
        "spoiler",
        "id",
    )

    def __init__(
        self,
        *children: Item[V_co],
        accent_colour: Optional[Union[Colour, int]] = None,
        accent_color: Optional[Union[Color, int]] = None,
        spoiler: bool = False,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._children: List[Item[V_co]] = self._init_children()
        for child in children:
            self.add_item(child)

        self.spoiler: bool = spoiler
        self._colour = accent_colour if accent_colour is not None else accent_color
        self.id = id

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} children={len(self._children)}>"

    def _init_children(self) -> List[Item[Any]]:
        children = []
        parents = {}

        for name, raw in self.__container_children_items__.items():
            if isinstance(raw, Item):
                item = raw.copy() if hasattr(raw, "copy") else copy.copy(raw)  # type: ignore
                item._parent = self
                setattr(self, name, item)
                children.append(item)
                parents[raw] = item
            else:
                item: Item = raw.__discord_ui_model_type__(**raw.__discord_ui_model_kwargs__)
                item.callback = _ItemCallback(raw, self, item)
                setattr(self, raw.__name__, item)
                parent = getattr(raw, "__discord_ui_parent__", None)
                if parent is None:
                    raise ValueError(f"{raw.__name__} is not a valid item for a Container")
                parents.get(parent, parent)._children.append(item)

        return children

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        children: Dict[str, Union[ItemCallbackType[Self, Any], Item[Any]]] = {}
        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if isinstance(member, Item):
                    children[name] = member
                if hasattr(member, "__discord_ui_model_type__") and getattr(member, "__discord_ui_parent__", None):
                    children[name] = copy.copy(member)

        cls.__container_children_items__ = children

    def _update_view(self, view) -> bool:
        self._view = view
        for child in self._children:
            child._update_view(view)
        return True

    def copy(self) -> Container[V_co]:
        new = copy.deepcopy(self)
        for child in new._children:
            newch = child.copy() if hasattr(child, "copy") else copy.copy(child)  # type: ignore
            newch._parent = new
        new._parent = self._parent
        new._update_view(self.view)
        return new

    def _has_children(self) -> bool:
        return True

    def _swap_item(self, base: Item, new: Item, custom_id: str) -> None:
        child_index = self._children.index(base)
        self._children[child_index] = new

    @property
    def children(self) -> List[Item[V_co]]:
        """List[:class:`Item`]: The children of this container."""
        return self._children.copy()

    @property
    def accent_colour(self) -> Optional[Union[Colour, Color, int]]:
        """Optional[Union[:class:`Colour`, :class:`int`]]: The colour of the container, or ``None``."""
        # Color is an alias for Colour, so no conversion needed
        return self._colour

    @accent_colour.setter
    def accent_colour(self, value: Optional[Union[Colour, int]]) -> None:
        if value is not None and not isinstance(value, (int, Colour)):
            raise TypeError(f"expected an int, or Colour, not {value.__class__.__name__!r}")

        self._colour = value

    accent_color = accent_colour

    @property
    def type(self) -> Literal[ComponentType.container]:
        return ComponentType.container

    @property
    def width(self) -> int:
        return 5

    @property
    def _total_count(self) -> int:
        return 1 + len(tuple(self.walk_children()))

    def _is_v2(self) -> bool:
        return True

    def to_components(self) -> List[Dict[str, Any]]:
        return [cast(Dict[str, Any], i.to_component_dict()) for i in self._children]

    def to_component_dict(self) -> Dict[str, Any]:
        components = self.to_components()

        colour = None
        if self._colour:
            colour = self._colour if isinstance(self._colour, int) else self._colour.value

        base = {
            "type": self.type.value,
            "accent_color": colour,
            "spoiler": self.spoiler,
            "components": components,
        }
        if self.id is not None:
            base["id"] = self.id
        return base

    @classmethod
    def from_component(cls, component: ContainerComponent) -> Self:
        self = cls(
            accent_colour=component.accent_colour,
            spoiler=component.spoiler,
            id=component.id,
        )
        self._children = [_component_to_item(cmp, self) for cmp in component.children]
        return self

    def walk_children(self) -> Generator[Item[V_co], None, None]:
        """An iterator that recursively walks through all the children of this container
        and its children, if applicable.

        Yields
        ------
        :class:`Item`
            An item in the container.
        """

        for child in self.children:
            yield child

            if child._has_children():
                yield from child.walk_children()  # type: ignore

    def content_length(self) -> int:
        """:class:`int`: Returns the total length of all text content in this container."""
        return sum(len(item.content) for item in self.walk_children() if isinstance(item, TextDisplay))

    def add_item(self, item: Item[Any]) -> Self:
        """Adds an item to this container.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: :class:`Item`
            The item to append.

        Raises
        ------
        TypeError
            An :class:`Item` was not passed.
        ValueError
            Maximum number of children has been exceeded (40) for the entire view.
        """
        if not isinstance(item, Item):
            raise TypeError(f"expected Item not {item.__class__.__name__}")

        if self._view:
            self._view._add_count(item._total_count)

        self._children.append(item)
        item._update_view(self.view)
        item._parent = self
        return self

    def remove_item(self, item: Item[Any]) -> Self:
        """Removes an item from this container.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: :class:`Item`
            The item to remove from the container.
        """

        try:
            self._children.remove(item)
        except ValueError:
            pass
        else:
            if self._view:
                self._view._add_count(-item._total_count)
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
        """Removes all the items from the container.

        This function returns the class instance to allow for fluent-style
        chaining.
        """

        if self._view:
            self._view._add_count(-len(tuple(self.walk_children())))
        self._children.clear()
        return self

