# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Callable, Optional, Tuple, TypeVar, Union

from ..components import Button as ButtonComponent
from ..enums import ButtonStyle, ComponentType
from ..partial_emoji import PartialEmoji, _EmojiTag
from .item import Item, ItemCallbackType

__all__ = (
    "Button",
    "button",
)

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..emoji import Emoji
    from ..interactions import ClientT
    from ..types.components import ButtonComponent as ButtonComponentPayload
    from .view import View

V_co = TypeVar("V_co", bound="View", covariant=True)


class Button(Item[V_co]):
    """Represents a UI button.

    .. versionadded:: 2.0

    Parameters
    ----------
    style: :class:`nextcord.ButtonStyle`
        The style of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        If this button is for a URL, it does not have a custom ID.
    url: Optional[:class:`str`]
        The URL this button sends you to.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    label: Optional[:class:`str`]
        The label of the button, if any.
    emoji: Optional[Union[:class:`.PartialEmoji`, :class:`.Emoji`, :class:`str`]]
        The emoji of the button, if available.
    row: Optional[:class:`int`]
        The relative row this button belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        "style",
        "url",
        "disabled",
        "label",
        "emoji",
        "row",
    )

    def __init__(
        self,
        *,
        style: ButtonStyle = ButtonStyle.secondary,
        label: Optional[str] = None,
        disabled: bool = False,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        row: Optional[int] = None,
    ) -> None:
        super().__init__()
        if custom_id is not None and url is not None:
            raise TypeError("Cannot mix both url and custom_id with Button")

        self._provided_custom_id = custom_id is not None
        if url is None and custom_id is None:
            custom_id = os.urandom(16).hex()

        if url is not None:
            style = ButtonStyle.link

        if emoji is not None:
            if isinstance(emoji, str):
                emoji = PartialEmoji.from_str(emoji)
            elif isinstance(emoji, _EmojiTag):
                emoji = emoji._to_partial()
            else:
                raise TypeError(
                    f"Expected emoji to be str, Emoji, or PartialEmoji not {emoji.__class__}"
                )

        self._underlying = ButtonComponent._raw_construct(
            type=ComponentType.button,
            custom_id=custom_id,
            url=url,
            disabled=disabled,
            label=label,
            style=style,
            emoji=emoji,
        )
        self.row = row

    @property
    def style(self) -> ButtonStyle:
        """:class:`nextcord.ButtonStyle`: The style of the button."""
        return self._underlying.style

    @style.setter
    def style(self, value: ButtonStyle) -> None:
        self._underlying.style = value

    @property
    def custom_id(self) -> Optional[str]:
        """Optional[:class:`str`]: The ID of the button that gets received during an interaction.

        If this button is for a URL, it does not have a custom ID.
        """
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError("custom_id must be None or str")

        self._underlying.custom_id = value

    @property
    def url(self) -> Optional[str]:
        """Optional[:class:`str`]: The URL this button sends you to."""
        return self._underlying.url

    @url.setter
    def url(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError("url must be None or str")
        self._underlying.url = value

    @property
    def disabled(self) -> bool:
        """:class:`bool`: Whether the button is disabled or not."""
        return self._underlying.disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        self._underlying.disabled = bool(value)

    @property
    def label(self) -> Optional[str]:
        """Optional[:class:`str`]: The label of the button, if available."""
        return self._underlying.label

    @label.setter
    def label(self, value: Optional[str]) -> None:
        self._underlying.label = str(value) if value is not None else value

    @property
    def emoji(self) -> Optional[PartialEmoji]:
        """Optional[:class:`.PartialEmoji`]: The emoji of the button, if available."""
        return self._underlying.emoji

    @emoji.setter
    def emoji(self, value: Optional[Union[str, Emoji, PartialEmoji]]) -> None:  # type: ignore
        if value is not None:
            if isinstance(value, str):
                self._underlying.emoji = PartialEmoji.from_str(value)
            elif isinstance(value, _EmojiTag):
                self._underlying.emoji = value._to_partial()
            else:
                raise TypeError(
                    f"Expected str, Emoji, or PartialEmoji, received {value.__class__} instead"
                )
        else:
            self._underlying.emoji = None

    @classmethod
    def from_component(cls, button: ButtonComponent) -> Self:
        return cls(
            style=button.style,
            label=button.label,
            disabled=button.disabled,
            custom_id=button.custom_id,
            url=button.url,
            emoji=button.emoji,
            row=None,
        )

    @property
    def type(self) -> ComponentType:
        return self._underlying.type

    def to_component_dict(self) -> ButtonComponentPayload:
        return self._underlying.to_dict()

    def is_dispatchable(self) -> bool:
        return self.custom_id is not None

    def is_persistent(self) -> bool:
        if self.style is ButtonStyle.link:
            return self.url is not None
        return super().is_persistent()

    def refresh_component(self, button: ButtonComponent) -> None:
        self._underlying = button


def button(
    *,
    label: Optional[str] = None,
    custom_id: Optional[str] = None,
    disabled: bool = False,
    style: ButtonStyle = ButtonStyle.secondary,
    emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
    row: Optional[int] = None,
) -> Callable[[ItemCallbackType[Button[V_co], ClientT]], ItemCallbackType[Button[V_co], ClientT]]:
    """A decorator that attaches a button to a component.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`nextcord.ui.View`, the :class:`nextcord.ui.Button` being pressed and
    the :class:`nextcord.Interaction` you receive.

    .. note::

        Buttons with a URL cannot be created with this function.
        Consider creating a :class:`Button` manually instead.
        This is because buttons with a URL do not have a callback
        associated with them since Discord does not do any processing
        with it.

    Parameters
    ----------
    label: Optional[:class:`str`]
        The label of the button, if any.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        It is recommended not to set this parameter to prevent conflicts.
    style: :class:`.ButtonStyle`
        The style of the button. Defaults to :attr:`.ButtonStyle.grey`.
    disabled: :class:`bool`
        Whether the button is disabled or not. Defaults to ``False``.
    emoji: Optional[Union[:class:`str`, :class:`.Emoji`, :class:`.PartialEmoji`]]
        The emoji of the button. This can be in string form or a :class:`.PartialEmoji`
        or a full :class:`.Emoji`.
    row: Optional[:class:`int`]
        The relative row this button belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    def decorator(
        func: ItemCallbackType[Button[V_co], ClientT]
    ) -> ItemCallbackType[Button[V_co], ClientT]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Button function must be a coroutine function")

        func.__discord_ui_model_type__ = Button
        func.__discord_ui_model_kwargs__ = {
            "style": style,
            "custom_id": custom_id,
            "url": None,
            "disabled": disabled,
            "label": label,
            "emoji": emoji,
            "row": row,
        }
        return func

    return decorator
