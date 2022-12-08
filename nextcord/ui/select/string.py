# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable, Generic, List, Optional, Tuple, TypeVar, Union

from ...components import SelectOption, StringSelectMenu
from ...emoji import Emoji
from ...enums import ComponentType
from ...interactions import ClientT
from ...partial_emoji import PartialEmoji
from ...utils import MISSING
from ..item import ItemCallbackType
from ..view import View
from .base import SelectBase

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = (
    "Select",
    "select",
    "StringSelect",
    "string_select",
)

V = TypeVar("V", bound="View", covariant=True)


class StringSelect(SelectBase, Generic[V]):
    """Represents a UI string select menu.

    This is usually represented as a drop down menu.

    In order to get the selected items that the user has chosen, use :attr:`StringSelect.values`.

    There is an alias for this class called ``Select``.

    .. versionadded:: 2.0

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
    options: List[:class:`.SelectOption`]
        A list of options that can be selected in this menu.
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
        options: List[SelectOption] = MISSING,
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
        self._selected_values: List[str] = []
        options = [] if options is MISSING else options
        self._underlying = StringSelectMenu._raw_construct(
            custom_id=self.custom_id,
            type=ComponentType.select,
            placeholder=self.placeholder,
            min_values=self.min_values,
            max_values=self.max_values,
            disabled=self.disabled,
            options=options,
        )

    @property
    def options(self) -> List[SelectOption]:
        """List[:class:`.SelectOption`]: A list of options that can be selected in this menu."""
        return self._underlying.options

    @options.setter
    def options(self, value: List[SelectOption]) -> None:
        if not isinstance(value, list):
            raise TypeError("options must be a list of SelectOption")
        if not all(isinstance(obj, SelectOption) for obj in value):
            raise TypeError("All list items must subclass SelectOption")

        self._underlying.options = value

    def add_option(
        self,
        *,
        label: str,
        value: str = MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        default: bool = False,
    ) -> None:
        """Adds an option to the select menu.

        To append a pre-existing :class:`.SelectOption` use the
        :meth:`append_option` method instead.

        Parameters
        ----------
        label: :class:`str`
            The label of the option. This is displayed to users.
            Can only be up to 100 characters.
        value: :class:`str`
            The value of the option. This is not displayed to users.
            If not given, defaults to the label. Can only be up to 100 characters.
        description: Optional[:class:`str`]
            An additional description of the option, if any.
            Can only be up to 100 characters.
        emoji: Optional[Union[:class:`str`, :class:`.Emoji`, :class:`.PartialEmoji`]]
            The emoji of the option, if available. This can either be a string representing
            the custom or unicode emoji or an instance of :class:`.PartialEmoji` or :class:`.Emoji`.
        default: :class:`bool`
            Whether this option is selected by default.

        Raises
        ------
        ValueError
            The number of options exceeds 25.
        """

        option = SelectOption(
            label=label,
            value=value,
            description=description,
            emoji=emoji,
            default=default,
        )

        self.append_option(option)

    def append_option(self, option: SelectOption) -> None:
        """Appends an option to the select menu.

        Parameters
        ----------
        option: :class:`.SelectOption`
            The option to append to the select menu.

        Raises
        ------
        ValueError
            The number of options exceeds 25.
        """

        if len(self._underlying.options) > 25:
            raise ValueError("maximum number of options already provided")

        self._underlying.options.append(option)

    @classmethod
    def from_component(cls, component: StringSelectMenu) -> Self:
        return cls(
            custom_id=component.custom_id,
            placeholder=component.placeholder,
            min_values=component.min_values,
            max_values=component.max_values,
            options=component.options,
            disabled=component.disabled,
            row=None,
        )


def string_select(
    *,
    placeholder: Optional[str] = None,
    custom_id: str = MISSING,
    min_values: int = 1,
    max_values: int = 1,
    options: List[SelectOption] = MISSING,
    disabled: bool = False,
    row: Optional[int] = None,
) -> Callable[
    [ItemCallbackType[StringSelect[V], ClientT]], ItemCallbackType[StringSelect[V], ClientT]
]:
    """A decorator that attaches a string select menu to a component.

    There is an alias for this function called ``select``.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`.ui.View`, the :class:`.ui.StringSelect` being pressed and
    the :class:`.Interaction` you receive.

    In order to get the selected items that the user has chosen within the callback
    use :attr:`StringSelect.values`.

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
    options: List[:class:`.SelectOption`]
        A list of options that can be selected in this menu.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    """

    def decorator(func: ItemCallbackType[Select[V]]) -> ItemCallbackType[Select[V]]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Select function must be a coroutine function")

        func.__discord_ui_model_type__ = StringSelect
        func.__discord_ui_model_kwargs__ = {
            "placeholder": placeholder,
            "custom_id": custom_id,
            "row": row,
            "min_values": min_values,
            "max_values": max_values,
            "options": options,
            "disabled": disabled,
        }
        return func

    return decorator


Select = StringSelect
select = string_select
"""alias of :func:`string_select`"""
