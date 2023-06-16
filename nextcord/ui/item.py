# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Generic,
    Literal,
    Optional,
    Tuple,
    TypeVar,
)

from ..interactions import ClientT, Interaction

__all__ = (
    "ViewItem",
    "ModalItem",
)

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..components import Component
    from ..enums import ComponentType
    from ..guild import Guild
    from ..state import ConnectionState
    from ..types.components import Component as ComponentPayload
    from ..types.interactions import ComponentInteractionData
    from .modal import Modal
    from .view import View

I = TypeVar("I", bound="BaseItem")
VI = TypeVar("VI", bound="ViewItem", covariant=True)
V = TypeVar("V", bound="View", covariant=True)
M = TypeVar("M", bound="Modal", covariant=True)

ViewItemCallbackType = Callable[[Any, VI, Interaction[ClientT]], Coroutine[Any, Any, Any]]


class BaseItem:
    """Represents the base UI item that all UI components inherit from."""

    __item_repr_attributes__: Tuple[str, ...] = ("row",)

    def __init__(self) -> None:
        self._row: Optional[int] = None
        self._rendered_row: Optional[int] = None
        # This works mostly well but there is a gotcha with
        # the interaction with from_component, since that technically provides
        # a custom_id most dispatchable items would get this set to True even though
        # it might not be provided by the library user. However, this edge case doesn't
        # actually affect the intended purpose of this check because from_component is
        # only called upon edit and we're mainly interested during initial creation time.
        self._provided_custom_id: bool = False

    def to_component_dict(self) -> ComponentPayload:
        raise NotImplementedError

    def refresh_component(self, component: Component) -> None:
        return None

    def refresh_state(
        self, data: ComponentInteractionData, state: ConnectionState, guild: Optional[Guild]
    ) -> None:
        return None

    @classmethod
    def from_component(cls, component: Component) -> Self:
        return cls()

    @property
    def type(self) -> ComponentType:
        raise NotImplementedError

    def is_dispatchable(self) -> bool:
        return False

    def is_persistent(self) -> bool:
        return self._provided_custom_id

    def __repr__(self) -> str:
        attrs = " ".join(f"{key}={getattr(self, key)!r}" for key in self.__item_repr_attributes__)
        return f"<{self.__class__.__name__} {attrs}>"

    @property
    def row(self) -> Optional[int]:
        return self._row

    @row.setter
    def row(self, value: Optional[int]) -> None:
        if value is None:
            self._row = None
        elif 5 > value >= 0:
            self._row = value
        else:
            raise ValueError("row cannot be negative or greater than or equal to 5")

    @property
    def width(self) -> int:
        return 1


class ViewItem(BaseItem, Generic[V]):
    """Represents the View UI item that all UI components supporting :class:`View` inherit from.

    The current UI items supported for View are:

    - :class:`nextcord.ui.Button`
    - :class:`nextcord.ui.StringSelect`
    - :class:`nextcord.ui.UserSelect`
    - :class:`nextcord.ui.ChannelSelect`
    - :class:`nextcord.ui.RoleSelect`
    - :class:`nextcord.ui.MentionableSelect`

    .. versionadded:: 2.0
    """

    def __init__(self) -> None:
        super().__init__()
        self._view: Optional[V] = None

    @property
    def view(self) -> Optional[V]:
        """Optional[:class:`View`]: The underlying view for this item."""
        return self._view

    async def callback(self, interaction: Interaction) -> None:
        """|coro|

        The callback associated with this UI item.

        This can be overridden by subclasses.

        Parameters
        ----------
        interaction: :class:`.Interaction`
            The interaction that triggered this UI item.
        """
        pass


class ModalItem(BaseItem, Generic[M]):
    """Represents the Modal UI item that all UI components supporting :class:`Modal` inherit from.

    The current UI items supported for Modal are:

    - :class:`nextcord.ui.TextInput`

    .. versionadded:: 2.6
    """

    def __init__(self) -> None:
        super().__init__()
        self._modal: Optional[M] = None

        # backwards compatibility
        self.callback: Literal[None] = None

    @property
    def modal(self) -> Optional[M]:
        """Optional[:class:`Modal`]: The underlying modal for this item."""
        return self._modal

    @property
    def view(self) -> Optional[M]:
        """Optional[:class:`Modal`]: Alias for :attr:`modal` for backwards compatibility."""
        return self._modal


# backwards compatiable
Item = ViewItem
"""Alias for :class:ViewItem`"""
