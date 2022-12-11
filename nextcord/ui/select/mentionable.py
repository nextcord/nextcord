# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Generic, List, Optional, Tuple, TypeVar

from ...components import MentionableSelectMenu
from ...enums import ComponentType
from ...interactions import ClientT
from ...member import Member
from ...role import Role
from ...user import User
from ...utils import MISSING
from ..item import ItemCallbackType
from ..view import View
from .base import SelectBase, SelectValuesBase

if TYPE_CHECKING:
    from typing_extensions import Self

    from ...guild import Guild
    from ...state import ConnectionState
    from ...types.components import MentionableSelectMenu as MentionableSelectMenuPayload
    from ...types.interactions import ComponentInteractionData

__all__ = ("MentionableSelect", "mentionable_select", "MentionableSelectValues")

V = TypeVar("V", bound="View", covariant=True)


class MentionableSelectValues(SelectValuesBase):
    """Represents the values of a :class:`.ui.MentionableSelect`."""

    @property
    def members(self) -> List[Member]:
        """List[:class:`.Member`]: A list of members that were selected."""
        return [v for v in self.data if isinstance(v, Member)]

    @property
    def users(self) -> List[User]:
        """List[:class:`.User`]: A list of users that were selected."""
        return [v for v in self.data if isinstance(v, User)]

    @property
    def roles(self) -> List[Role]:
        """List[:class:`.Role`]: A list of roles that were selected."""
        return [v for v in self.data if isinstance(v, Role)]


class MentionableSelect(SelectBase, Generic[V]):

    """Represents a UI mentionable select menu.

    This is usually represented as a drop down menu.

    In order to get the selected items that the user has chosen,
    use :attr:`MentionableSelect.values`.

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
        self._selected_values: MentionableSelectValues = MentionableSelectValues()
        self._underlying = MentionableSelectMenu._raw_construct(
            custom_id=self.custom_id,
            type=ComponentType.mentionable_select,
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
        )

    @property
    def values(self) -> MentionableSelectValues:
        """:class:`.ui.MentionableSelectValues`: A list of Union[:class:`.Member`, :class:`.User`, :class:`.Role`] that have been selected by the user."""
        return self._selected_values

    def to_component_dict(self) -> MentionableSelectMenuPayload:
        return self._underlying.to_dict()

    @classmethod
    def from_component(cls, component: MentionableSelectMenu) -> Self:
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
        self._selected_values = MentionableSelectValues.construct(
            data.get("values", []),
            data.get("resolved", {}),
            state,
            guild,
        )


def mentionable_select(
    *,
    placeholder: Optional[str] = None,
    custom_id: str = MISSING,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: Optional[int] = None,
) -> Callable[
    [ItemCallbackType[MentionableSelect[V], ClientT]],
    ItemCallbackType[MentionableSelect[V], ClientT],
]:
    """A decorator that attaches a mentionable select menu to a component.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`.ui.View`, the :class:`.ui.MentionableSelect` being pressed and
    the :class:`.Interaction` you receive.

    In order to get the selected items that the user has chosen within the callback
    use :attr:`MentionableSelect.values`.

    .. versionadded:: 2.3

    Parameters
    ------------
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

        func.__discord_ui_model_type__ = MentionableSelect
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
