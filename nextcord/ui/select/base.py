# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
from collections import UserList
from typing import TYPE_CHECKING, List, Optional, Tuple, TypeVar, Union

from ...components import SelectMenu
from ...enums import ComponentType
from ...guild import Guild
from ...member import Member
from ...role import Role
from ...state import ConnectionState
from ...user import User
from ...utils import MISSING
from ..item import Item

__all__ = ("SelectBase",)

if TYPE_CHECKING:
    from typing_extensions import Self

    from ...abc import GuildChannel
    from ...types.components import SelectMenu as SelectMenuPayload
    from ...types.interactions import ComponentInteractionData, ComponentInteractionResolved
    from ..view import View

V = TypeVar("V", bound="View", covariant=True)


class SelectValuesBase(UserList):
    def __init__(self) -> None:
        self.data: List[Union[Member, User, Role, GuildChannel]] = []

    @classmethod
    def construct(
        cls,
        values: List[str],
        resolved: ComponentInteractionResolved,
        state: ConnectionState,
        guild: Optional[Guild],
    ):
        instance = cls()
        users = resolved.get("users", {})
        members = resolved.get("members", {})
        roles = resolved.get("roles", {})
        channels = resolved.get("channels", {})
        for value in values:
            if members.get(value) and guild:
                members[value]["user"] = users[value]
                instance.append(Member(data=members[value], state=state, guild=guild))
            elif users.get(value):
                instance.append(User(data=users[value], state=state))
            elif roles.get(value) and guild:
                instance.append(Role(data=roles[value], state=state, guild=guild))
            elif channels.get(value) and guild:
                channel = state.get_channel(int(value))
                instance.append(channel)
        return instance

    @property
    def ids(self) -> List[int]:
        return [o.id for o in self.data]


class SelectBase(Item[V]):
    """Represents a UI select menu without any options.

    This is usually represented as a drop down menu.

    In order to get the selected items that the user has chosen, use :attr:`Select.values`.

    .. warning:: This class is not meant to be instantiated by the user. In order to create a select menu, use :class:`Select` instead.

    .. versionadded:: 2.3

    Parameters
    ----------
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
        Whether the select is disabled or not.
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
        "options",
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
        super().__init__()
        self._selected_values: List[str] = []
        self._provided_custom_id = custom_id is not MISSING
        custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        self._underlying = SelectMenu._raw_construct(
            custom_id=custom_id,
            type=ComponentType.select,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
        )
        self.row = row

    @property
    def custom_id(self) -> str:
        """:class:`str`: The ID of the select menu that gets received during an interaction."""
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("custom_id must be None or str")

        self._underlying.custom_id = value

    @property
    def placeholder(self) -> Optional[str]:
        """Optional[:class:`str`]: The placeholder text that is shown if nothing is selected, if any."""
        return self._underlying.placeholder

    @placeholder.setter
    def placeholder(self, value: Optional[str]):
        if value is not None and not isinstance(value, str):
            raise TypeError("placeholder must be None or str")

        self._underlying.placeholder = value

    @property
    def min_values(self) -> int:
        """:class:`int`: The minimum number of items that must be chosen for this select menu."""
        return self._underlying.min_values

    @min_values.setter
    def min_values(self, value: int) -> None:
        self._underlying.min_values = int(value)

    @property
    def max_values(self) -> int:
        """:class:`int`: The maximum number of items that must be chosen for this select menu."""
        return self._underlying.max_values

    @max_values.setter
    def max_values(self, value: int) -> None:
        self._underlying.max_values = int(value)

    @property
    def disabled(self) -> bool:
        """:class:`bool`: Whether the select is disabled or not."""
        return self._underlying.disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        self._underlying.disabled = bool(value)

    @property
    def values(self) -> List[str]:
        """List[:class:`str`]: A list of values that have been selected by the user."""
        return self._selected_values

    @property
    def width(self) -> int:
        return 5

    def to_component_dict(self) -> SelectMenuPayload:
        return self._underlying.to_dict()

    def refresh_component(self, component: SelectMenu) -> None:
        self._underlying = component

    def refresh_state(
        self, data: ComponentInteractionData, state: ConnectionState, guild: Optional[Guild]
    ) -> None:
        self._selected_values = data.get("values", [])

    @classmethod
    def from_component(cls, component: SelectMenu) -> Self:
        return cls(
            custom_id=component.custom_id,
            placeholder=component.placeholder,
            min_values=component.min_values,
            max_values=component.max_values,
            disabled=component.disabled,
            row=None,
        )

    @property
    def type(self) -> ComponentType:
        return self._underlying.type

    def is_dispatchable(self) -> bool:
        return True
