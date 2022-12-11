# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Generic, List, Optional, Tuple, TypeVar

from ...components import RoleSelectMenu
from ...enums import ComponentType
from ...interactions import ClientT
from ...role import Role
from ...state import ConnectionState
from ...utils import MISSING
from ..item import ItemCallbackType
from ..view import View
from .base import SelectBase, SelectValuesBase

if TYPE_CHECKING:
    from typing_extensions import Self

    from ...guild import Guild
    from ...types.components import RoleSelectMenu as RoleSelectMenuPayload
    from ...types.interactions import ComponentInteractionData

__all__ = ("RoleSelect", "role_select", "RoleSelectValues")

V = TypeVar("V", bound="View", covariant=True)


class RoleSelectValues(SelectValuesBase):
    """Represents the values of a :class:`.ui.RoleSelect`."""

    @property
    def roles(self) -> List[Role]:
        """List[:class:`.Role`]: The roles that were selected."""
        return [v for v in self.data if isinstance(v, Role)]


class RoleSelect(SelectBase, Generic[V]):

    """Represents a UI role select menu.

    This is usually represented as a drop down menu.

    In order to get the selected items that the user has chosen,
    use :attr:`RoleSelect.values`.

    .. versionadded:: 2.3

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        If not given then one is generated for you.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        "placeholder",
        "min_values",
        "max_values",
        "disabled",
    )

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            placeholder=placeholder,
        )
        self._selected_values: RoleSelectValues = RoleSelectValues()
        self._underlying = RoleSelectMenu._raw_construct(
            custom_id=self.custom_id,
            type=ComponentType.role_select,
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
        )

    @property
    def values(self) -> RoleSelectValues:
        """:class:`.ui.RoleSelectValues`: A list of :class:`.Role` that have been selected by the user."""
        return self._selected_values

    def to_component_dict(self) -> RoleSelectMenuPayload:
        return self._underlying.to_dict()

    @classmethod
    def from_component(cls, component: RoleSelectMenu) -> Self:
        return cls(
            custom_id=component.custom_id,
            placeholder=component.placeholder,
            min_values=component.min_values,
            max_values=component.max_values,
            disabled=component.disabled,
            row=None,
        )

    def refresh_state(
        self, data: ComponentInteractionData, state: ConnectionState, guild: Optional[Guild]
    ) -> None:
        self._selected_values = RoleSelectValues.construct(
            data.get("values", []),
            data.get("resolved", {}),
            state,
            guild,
        )


def role_select(
    *,
    placeholder: Optional[str] = None,
    custom_id: str = MISSING,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: Optional[int] = None,
) -> Callable[[ItemCallbackType[RoleSelect[V], ClientT]], ItemCallbackType[RoleSelect[V], ClientT]]:
    """A decorator that attaches a role select menu to a component.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`.ui.View`, the :class:`.ui.RoleSelect` being pressed and
    the :class:`.Interaction` you receive.

    In order to get the selected items that the user has chosen within the callback
    use :attr:`RoleSelect.values`.

    .. versionadded:: 2.3

    Parameters
    ----------
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        It is recommended not to set this parameter to prevent conflicts.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    """

    def decorator(func: ItemCallbackType) -> ItemCallbackType:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Select function must be a coroutine function")

        func.__discord_ui_model_type__ = RoleSelect
        func.__discord_ui_model_kwargs__ = {
            "placeholder": placeholder,
            "custom_id": custom_id,
            "row": row,
            "min_values": min_values,
            "max_values": max_values,
            "disabled": disabled,
        }
        return func

    return decorator
