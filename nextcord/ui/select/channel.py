# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Generic, List, Optional, Tuple, TypeVar

from ...abc import GuildChannel
from ...components import ChannelSelectMenu
from ...enums import ComponentType
from ...interactions import ClientT
from ...utils import MISSING
from ..item import ItemCallbackType
from ..view import View
from .base import SelectBase, SelectValuesBase

if TYPE_CHECKING:
    from typing_extensions import Self

    from ...enums import ChannelType
    from ...guild import Guild
    from ...state import ConnectionState
    from ...types.components import ChannelSelectMenu as ChannelSelectMenuPayload
    from ...types.interactions import ComponentInteractionData

__all__ = ("ChannelSelect", "channel_select", "ChannelSelectValues")

V = TypeVar("V", bound="View", covariant=True)


class ChannelSelectValues(SelectValuesBase):
    """Represents the values of a :class:`.ui.ChannelSelect`."""

    @property
    def channels(self) -> List[GuildChannel]:
        """List[:class:`.abc.GuildChannel`]: The resolved channels."""
        return [v for v in self.data if isinstance(v, GuildChannel)]


class ChannelSelect(SelectBase, Generic[V]):

    """Represents a UI channel select menu.

    This is usually represented as a drop down menu.

    In order to get the selected items that the user has chosen,
    use :attr:`ChannelSelect.values`.

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
        Whether the select is disabled or not. Defaults to ``False``.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    channel_types: List[:class:`.ChannelType`]
        The types of channels that can be selected. If not given, all channel types are allowed.
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        "placeholder",
        "min_values",
        "max_values",
        "disabled",
        "channel_types",
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
        channel_types: List[ChannelType] = MISSING,
    ) -> None:
        super().__init__(
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )
        self._selected_values: ChannelSelectValues = ChannelSelectValues()
        self.channel_types: List[ChannelType] = channel_types
        self._underlying = ChannelSelectMenu._raw_construct(
            custom_id=self.custom_id,
            type=ComponentType.channel_select,
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            channel_types=channel_types,
        )

    @property
    def values(self) -> ChannelSelectValues:
        """:class:`.ui.ChannelSelectValues`: A list of resolved :class:`.abc.GuildChannel` that have been selected by the user."""
        return self._selected_values

    def to_component_dict(self) -> ChannelSelectMenuPayload:
        return self._underlying.to_dict()

    @classmethod
    def from_component(cls, component: ChannelSelectMenu) -> Self:
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
        self._selected_values = ChannelSelectValues.construct(
            data.get("values", []),
            data.get("resolved", {}),
            state,
            guild,
        )


def channel_select(
    *,
    placeholder: Optional[str] = None,
    custom_id: str = MISSING,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: Optional[int] = None,
    channel_types: List[ChannelType] = MISSING,
) -> Callable[
    [ItemCallbackType[ChannelSelect[V], ClientT]], ItemCallbackType[ChannelSelect[V], ClientT]
]:
    """A decorator that attaches a channel select menu to a component.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`.ui.View`, the :class:`.ui.ChannelSelect` being pressed and
    the :class:`.Interaction` you receive.

    In order to get the selected items that the user has chosen within the callback
    use :attr:`ChannelSelect.values`.

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
    channel_types: List[:class:`.ChannelType`]
        A list of channel types that can be selected in this menu.
    """

    def decorator(func: ItemCallbackType) -> ItemCallbackType:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Select function must be a coroutine function")

        func.__discord_ui_model_type__ = ChannelSelect
        func.__discord_ui_model_kwargs__ = {
            "placeholder": placeholder,
            "custom_id": custom_id,
            "row": row,
            "min_values": min_values,
            "max_values": max_values,
            "disabled": disabled,
            "channel_types": channel_types,
        }
        return func

    return decorator
