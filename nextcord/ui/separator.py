# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, TypeVar

from ..components import SeparatorComponent
from ..enums import ComponentType, SeparatorSpacing
from .item import Item

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView

V_co = TypeVar("V_co", bound="LayoutView", covariant=True)

__all__ = ("Separator",)


class Separator(Item[V_co]):
    """Represents a UI separator.

    This is a top-level layout component that can only be used on :class:`LayoutView`.

        .. versionadded:: 3.12

    Parameters
    ----------
    visible: :class:`bool`
        Whether this separator is visible. On the client side this
        is whether a divider line should be shown or not. Defaults to ``True``.
    spacing: :class:`.SeparatorSpacing`
        The spacing of this separator. Defaults to :attr:`.SeparatorSpacing.small`.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.

    Attributes
    ----------
    visible: :class:`bool`
        Whether this separator is visible.
    spacing: :class:`.SeparatorSpacing`
        The spacing of this separator.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __item_repr_attributes__ = (
        "visible",
        "spacing",
        "id",
    )

    def __init__(
        self,
        *,
        visible: bool = True,
        spacing: SeparatorSpacing = SeparatorSpacing.small,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._underlying = SeparatorComponent._raw_construct(
            spacing=spacing,
            visible=visible,
            id=id,
        )
        self.id = id

    def _is_v2(self) -> bool:
        return True

    @property
    def visible(self) -> bool:
        """:class:`bool`: Whether this separator is visible.

        On the client side this is whether a divider line should
        be shown or not.
        """
        return self._underlying.visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._underlying.visible = value

    @property
    def spacing(self) -> SeparatorSpacing:
        """:class:`.SeparatorSpacing`: The spacing of this separator."""
        return self._underlying.spacing

    @spacing.setter
    def spacing(self, value: SeparatorSpacing) -> None:
        self._underlying.spacing = value

    @property
    def width(self) -> int:
        return 5

    @property
    def type(self) -> Literal[ComponentType.separator]:
        return self._underlying.type

    def to_component_dict(self) -> Dict[str, Any]:
        return self._underlying.to_dict()  # type: ignore

    @classmethod
    def from_component(cls, component: SeparatorComponent) -> Self:
        return cls(
            visible=component.visible,
            spacing=component.spacing,
            id=component.id,
        )

