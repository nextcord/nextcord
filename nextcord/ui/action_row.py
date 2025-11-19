# SPDX-License-Identifier: MIT

from __future__ import annotations

import copy
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
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

from ..components import ActionRow as ActionRowComponent
from ..enums import ButtonStyle, ComponentType
from ..utils import MISSING, get as _utils_get
from .button import button as _button
from .item import ContainedItemCallbackType as ItemCallbackType, Item, _ItemCallback
from .select import select as _select
from .view import _component_to_item

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..components import SelectOption
    from ..emoji import Emoji
    from .container import Container
    from .select.base import SelectBase
    from .view import LayoutView

    BaseSelectT = TypeVar("BaseSelectT", bound=SelectBase)
    SelectCallbackDecorator = Callable[[ItemCallbackType["S_co", BaseSelectT]], BaseSelectT]

S_co = TypeVar("S_co", bound=Union["ActionRow", "Container", "LayoutView"], covariant=True)
V_co = TypeVar("V_co", bound="LayoutView", covariant=True)

__all__ = ("ActionRow",)


class ActionRow(Item[V_co]):
    r"""Represents a UI action row.

    This is a top-level layout component that can only be used on :class:`LayoutView`
    and can contain :class:`Button`\s and :class:`Select`\s in it.

    Action rows can only have 5 children. This can be inherited.

        .. versionadded:: 3.12

    Parameters
    ----------
    \*children: :class:`Item`
        The initial children of this action row.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.

    Attributes
    ----------
    children: List[:class:`Item`]
        The list of children attached to this action row.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __action_row_children_items__: ClassVar[List[ItemCallbackType[Self, Any]]] = []
    __discord_ui_action_row__: ClassVar[bool] = True
    __item_repr_attributes__ = ("id",)

    def __init__(
        self,
        *children: Item[V_co],
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.id: Optional[int] = id
        self._children: List[Item[V_co]] = self._init_children()
        self._weight: int = sum(i.width for i in self._children)
        for child in children:
            self.add_item(child)

        if self._weight > 5:
            raise ValueError("maximum number of children exceeded")

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        children: Dict[str, ItemCallbackType[Self, Any]] = {
            name: member
            for base in reversed(cls.__mro__)
            for name, member in base.__dict__.items()
            if hasattr(member, "__discord_ui_model_type__")
        }

        if len(children) > 5:
            raise TypeError("ActionRow cannot have more than 5 children")

        cls.__action_row_children_items__ = list(children.values())

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} children={len(self._children)}>"

    def _init_children(self) -> List[Item[Any]]:
        children = []

        for func in self.__action_row_children_items__:
            item: Item = func.__discord_ui_model_type__(**func.__discord_ui_model_kwargs__)
            item.callback = _ItemCallback(func, self, item)
            item._parent = self
            setattr(self, func.__name__, item)
            children.append(item)
        return children

    def _update_view(self, view) -> None:
        self._view = view
        for child in self._children:
            child._view = view

    def copy(self) -> ActionRow[V_co]:
        new = copy.copy(self)
        children = []
        for child in new._children:
            newch = child.copy() if hasattr(child, "copy") else copy.copy(child)  # type: ignore
            newch._parent = new
            if isinstance(newch.callback, _ItemCallback):
                newch.callback.parent = new
            children.append(newch)
        new._children = children
        new._parent = self._parent
        new._update_view(self.view)
        return new

    def __deepcopy__(self, memo) -> ActionRow[V_co]:
        return self.copy()

    def _has_children(self) -> bool:
        return True

    def _is_v2(self) -> bool:
        return True

    def _swap_item(self, base: Item, new: Item, custom_id: str) -> None:
        child_index = self._children.index(base)
        self._children[child_index] = new

    @property
    def width(self) -> int:
        return 5

    @property
    def _total_count(self) -> int:
        return 1 + len(self._children)

    @property
    def type(self) -> Literal[ComponentType.action_row]:
        return ComponentType.action_row

    @property
    def children(self) -> List[Item[V_co]]:
        """List[:class:`Item`]: The list of children attached to this action row."""
        return self._children.copy()

    def walk_children(self) -> Generator[Item[V_co], Any, None]:
        """An iterator that recursively walks through all the children of this action row
        and its children, if applicable.

        Yields
        ------
        :class:`Item`
            An item in the action row.
        """

        yield from self.children

    def content_length(self) -> int:
        """:class:`int`: Returns the total length of all text content in this action row."""
        from .text_display import TextDisplay

        return sum(len(item.content) for item in self._children if isinstance(item, TextDisplay))

    def add_item(self, item: Item[Any]) -> Self:
        """Adds an item to this action row.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: :class:`Item`
            The item to add to the action row.

        Raises
        ------
        TypeError
            An :class:`Item` was not passed.
        ValueError
            Maximum number of children has been exceeded (5)
            or (40) for the entire view.
        """

        if (self._weight + item.width) > 5:
            raise ValueError("maximum number of children exceeded")

        if len(self._children) >= 5:
            raise ValueError("maximum number of children exceeded")

        if not isinstance(item, Item):
            raise TypeError(f"expected Item not {item.__class__.__name__}")

        if self._view:
            self._view._add_count(1)

        item._update_view(self.view)
        item._parent = self
        self._weight += 1
        self._children.append(item)

        return self

    def remove_item(self, item: Item[Any]) -> Self:
        """Removes an item from the action row.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: :class:`Item`
            The item to remove from the action row.
        """

        try:
            self._children.remove(item)
        except ValueError:
            pass
        else:
            if self._view:
                self._view._add_count(-1)
            self._weight -= item.width
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
        """Removes all the items from the action row.

        This function returns the class instance to allow for fluent-style
        chaining.
        """

        if self._view:
            self._view._add_count(-len(self._children))
        self._children.clear()
        self._weight = 0
        return self

    @classmethod
    def from_component(cls, component: ActionRowComponent) -> Self:
        self = cls(id=component.id)  # type: ignore
        self._children = [_component_to_item(c, self) for c in component.children]
        return self

    def to_components(self) -> List[Dict[str, Any]]:
        return [cast(Dict[str, Any], component.to_component_dict()) for component in self._children]

    def to_component_dict(self) -> Dict[str, Any]:
        data = {
            "type": self.type.value,
            "components": self.to_components(),
        }
        if self.id is not None:
            data["id"] = self.id
        return data

    def button(
        self,
        *,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        disabled: bool = False,
        style: ButtonStyle = ButtonStyle.secondary,
        emoji: Optional[Union[str, Emoji]] = None,
        row: Optional[int] = None,
    ):
        return _button(
            label=label,
            custom_id=custom_id,
            disabled=disabled,
            style=style,
            emoji=emoji,
            row=row,
        )

    def select(
        self,
        *,
        placeholder: Optional[str] = None,
        custom_id: Any = MISSING,
        min_values: int = 1,
        max_values: int = 1,
        options: List[SelectOption] = MISSING,
        disabled: bool = False,
        row: Optional[int] = None,
    ):
        return _select(
            placeholder=placeholder,
            custom_id=custom_id,
            min_values=min_values,
            max_values=max_values,
            options=options,
            disabled=disabled,
            row=row,
        )
