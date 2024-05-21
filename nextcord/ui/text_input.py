# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional, Tuple, TypeVar

from ..components import TextInput as TextInputComponent
from ..enums import ComponentType, TextInputStyle
from ..guild import Guild
from ..state import ConnectionState
from ..utils import MISSING
from .item import Item

__all__ = ("TextInput",)

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..types.components import TextInputComponent as TextInputComponentPayload
    from ..types.interactions import ComponentInteractionData
    from .view import View


V_co = TypeVar("V_co", bound="View", covariant=True)


class TextInput(Item[V_co]):
    """Represent a UI text input.

    .. versionadded:: 2.0

    Parameters
    ----------
    label: :class:`str`
        The label of the text input
    style: :class:`TextInputStyle`
        The style of the text input.
        By default, the style is ``TextInputStyle.short``, a one line
        input, but you can use ``TextInputStyle.paragraph``, a multi line
        input.
    custom_id: Optional[:class:`str`]
        The ID of the text input that get received during an interaction.
    row: Optional[:class:`int`]
        The relative row this text input belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    min_length: Optional[:class:`int`]
        The minimal length of the user's input
    max_length: Optional[:class:`int`]
        The maximal length of the user's input
    required: Optional[:class:`bool`]
        If ``True``, the user cannot send the form without filling this
        field.
    default_value: Optional[:class:`str`]
        The value already in the input when the user open the form.
    placeholder: Optional[:class:`str`]
        The text shown to the user when the text input is empty.
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        "custom_id",
        "label",
        "style",
        "min_length",
        "max_length",
        "required",
        "default_value",
        "value",
        "placeholder",
    )

    def __init__(
        self,
        label: str,
        *,
        style: TextInputStyle = TextInputStyle.short,
        custom_id: str = MISSING,
        row: Optional[int] = None,
        min_length: Optional[int] = 0,
        max_length: Optional[int] = 4000,
        required: Optional[bool] = None,
        default_value: Optional[str] = None,
        placeholder: Optional[str] = None,
    ) -> None:
        self._provided_custom_id = custom_id is not MISSING
        custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        self._underlying = TextInputComponent._raw_construct(
            type=ComponentType.text_input,
            custom_id=custom_id,
            label=label,
            style=style,
            min_length=min_length,
            max_length=max_length,
            required=required,
            value=default_value,
            placeholder=placeholder,
        )
        self.row = row
        self._inputed_value: Optional[str] = None

    @property
    def style(self) -> TextInputStyle:
        """:class:`nextcord.TextInputStyle`: The style of the text input."""
        return self._underlying.style

    @style.setter
    def style(self, value: TextInputStyle) -> None:
        self._underlying.style = value

    @property
    def custom_id(self) -> Optional[str]:
        """Optional[:class:`str`]: The ID of the text input that gets received during an interaction."""
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError("custom_id must be None or str")

        self._underlying.custom_id = value  # type: ignore

    @property
    def label(self) -> str:
        """:class:`str`: The label of the text input."""
        return self._underlying.label

    @label.setter
    def label(self, value: str) -> None:
        if value is None:  # pyright: ignore[reportUnnecessaryComparison]
            raise TypeError("label must cannot be None")
        self._underlying.label = str(value)

    @property
    def min_length(self) -> Optional[int]:
        """:class:`int`: The minimum input length for a text input"""
        return self._underlying.min_length

    @min_length.setter
    def min_length(self, value: int) -> None:
        self._underlying.min_length = value

    @property
    def max_length(self) -> Optional[int]:
        """:class:`int`: The maximum input length for a text input"""
        return self._underlying.max_length

    @max_length.setter
    def max_length(self, value: int) -> None:
        self._underlying.max_length = value

    @property
    def required(self) -> Optional[bool]:
        """:class:`bool`: Whether this component is required to be filled"""
        return self._underlying.required

    @required.setter
    def required(self, value: Optional[bool]) -> None:
        if value is not None and not isinstance(value, bool):
            raise TypeError("required must be None or bool")

        self._underlying.required = value

    @property
    def default_value(self) -> Optional[str]:
        """Optional[:class:`str`]: The value already in the text input when the user open the form."""
        return self._underlying.value

    @default_value.setter
    def default_value(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError("default_value must be None or str")
        self._underlying.value = value

    @property
    def value(self) -> Optional[str]:
        """Optional[:class:`str`]: The value sent by the user.
        This field is updated when an interaction is received.
        ``TextInput.value`` is ``None`` when no interaction where received.
        """
        return self._inputed_value

    @property
    def placeholder(self) -> Optional[str]:
        """Optional[:class:`str`]: The text shown to the user when the text input is empty."""
        return self._underlying.placeholder

    @placeholder.setter
    def placeholder(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError("placeholder must be None or str")

        self._underlying.placeholder = value

    @property
    def width(self) -> int:
        return 5

    @classmethod
    def from_component(cls, text_input: TextInputComponent) -> Self:
        return cls(
            style=text_input.style,
            custom_id=text_input.custom_id,
            label=text_input.label,
            min_length=text_input.min_length,
            max_length=text_input.max_length,
            required=text_input.required,
            placeholder=text_input.placeholder,
            row=None,
        )

    @property
    def type(self) -> ComponentType:
        return self._underlying.type

    def to_component_dict(self) -> TextInputComponentPayload:
        return self._underlying.to_dict()

    def is_dispatchable(self) -> bool:
        return True

    def refresh_component(self, text_input: TextInputComponent) -> None:
        self._underlying = text_input

    def refresh_state(
        self, data: ComponentInteractionData, state: ConnectionState, guild: Optional[Guild]
    ) -> None:
        self._inputed_value = data.get("value", "")
