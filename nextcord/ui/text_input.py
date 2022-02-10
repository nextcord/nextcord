"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz
Copyright (c) 2022 ascpial

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING, Type, TypeVar
import inspect
import os


from .item import Item, ItemCallbackType
from ..enums import TextInputStyle, ComponentType
from ..components import TextInput as TextInputComponent
from ..utils import MISSING
from ..interactions import Interaction

__all__ = (
    'TextInput',
    'text_input',
)

if TYPE_CHECKING:
    from .view import View
    from ..emoji import Emoji

T = TypeVar('T', bound='TextInput')
V = TypeVar('V', bound='View', covariant=True)


class TextInput(Item[V]):
    
    __item_repr_attributes__ = (
        'custom_id',
        'label',
        'style',
        'min_lenght',
        'max_lenght',
        'required',
        'value',
        'placeholder',
    )

    def __init__(
        self,
        label: str,
        *,
        style: TextInputStyle = TextInputStyle.short,
        custom_id: str = MISSING,
        row: Optional[int] = None,
        min_lenght: int = 0,
        max_lenght: int = 4000,
        required: bool = None,
        value: Optional[str] = None,
        placeholder: Optional[str] = None,
    ):
        self._provided_custom_id = custom_id is not MISSING
        custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        self._underlying = TextInputComponent._raw_construct(
            type=ComponentType.textinput,
            custom_id=custom_id,
            label=label,
            style=style,
            min_lenght=min_lenght,
            max_lenght=max_lenght,
            required=required,
            value=value,
            placeholder=placeholder,
        )
        self.row = row

    @property
    def style(self) -> TextInputStyle:
        """:class:`nextcord.ButtonStyle`: The style of the button."""
        return self._underlying.style

    @style.setter
    def style(self, value: TextInputStyle):
        self._underlying.style = value

    @property
    def custom_id(self) -> Optional[str]:
        """Optional[:class:`str`]: The ID of the button that gets received during an interaction.

        If this button is for a URL, it does not have a custom ID.
        """
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: Optional[str]):
        if value is not None and not isinstance(value, str):
            raise TypeError('custom_id must be None or str')

        self._underlying.custom_id = value

    @property
    def label(self) -> str:
        """Optional[:class:`str`]: The label of the button, if available."""
        return self._underlying.label

    @label.setter
    def label(self, value: str):
        if value is None:
            raise TypeError('label must cannot be None')
        self._underlying.label = str(value)
    
    @property
    def min_lenght(self) -> int:
        """:class:`int`: The minimum input length for a text input"""
        return self._underlying.min_lenght
    
    @min_lenght.setter
    def min_lenght(self, value: int):
        self._underlying.min_lenght = value
    
    @property
    def max_lenght(self) -> int:
        """:class:`int`: The maximum input length for a text input"""
        return self._underlying.max_lenght
    
    @max_lenght.setter
    def max_lenght(self, value: int):
        self._underlying.max_lenght = value
    
    @property
    def required(self) -> bool:
        """:class:`bool`: Whether this component is required to be filled"""
        if self._underlying.required is not None:
            return self._underlying.required
        else:
            return False
    
    @required.setter
    def required(self, value: Optional[bool]):
        if value is not None and not isinstance(value, bool):
            raise TypeError('required must be None or bool')
        self._underlying.required = value
    
    @property
    def value(self) -> Optional[str]:
        return self._underlying.value
    
    @value.setter
    def value(self, value: Optional[str]):
        if value is not None and not isinstance(value, str):
            raise TypeError('value must be None or str')
        self._underlying.value = value
    
    @property
    def placeholder(self) -> Optional[str]:
        return self._underlying.placeholder
    
    @placeholder.setter
    def placeholder(self, value: Optional[str]):
        if value is not None and not isinstance(value, str):
            raise TypeError('placeholder must be None or str')
        self._underlying.placeholder = value
    
    @property
    def width(self) -> int:
        return 5

    @classmethod
    def from_component(cls: Type[T], text_input: TextInputComponent) -> T:
        return cls(
            style=text_input.style,
            custom_id=text_input.custom_id,
            label=text_input.label,
            min_lenght=text_input.min_lenght,
            max_lenght=text_input.max_lenght,
            required=text_input.required,
            value=text_input.value,
            placeholder=text_input.placeholder,
            row=None,
        )

    @property
    def type(self) -> ComponentType:
        return self._underlying.type

    def to_component_dict(self):
        return self._underlying.to_dict()

    def is_dispatchable(self) -> bool:
        return True

    def refresh_component(self, text_input: TextInputComponent) -> None:
        self._underlying = text_input
