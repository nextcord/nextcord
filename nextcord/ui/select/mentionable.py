"""
The MIT License (MIT)

Copyright (c) 2022-present tag-epic

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

import asyncio
import os
from collections import UserList
from typing import TYPE_CHECKING, Callable, List, Optional, Union, Type, TypeVar

from .base import SelectBase
from ...components import MentionableSelectMenu, SelectOption
from ...enums import ComponentType
from ...utils import MISSING, get
from ..item import Item, ItemCallbackType

if TYPE_CHECKING:
    from ...guild import Guild
    from ...member import Member
    from ...role import Role
    from ...types.components import MentionableSelectMenu as MentionableSelectMenuPayload

__all__ = ("MentionableSelect", "mentionable_select")

S = TypeVar("S", bound="MentionableSelect")


class MentionableSelectValues(UserList):
    """Represents the values of a :class:`MentionableSelect`."""

    def get(self, guild: Guild) -> List[Union[Member, Role]]:
        """A shortcut for getting all :class:`nextcord.Member`'s and :class:`nextcord.Role`'s of :attr:`.values`.

        Mentionables that are not found in cache will not be returned.
        To get all mentionables regardless of whether they are in cache or not, use :meth:`.fetch_mentionables`.

        Parameters
        ----------
        guild: :class:`nextcord.Guild`
            The guild to get the mentionables from.

        Returns
        -------
        List[Union[:class:`nextcord.Member`, :class:`nextcord.Role`]]
            A list of mentionables that have been selected by the user.
        """
        mentionables: List[Union[Member, Role]] = []
        for id in self.data:
            mentionable = guild.get_member(id) or guild.get_role(id)
            if mentionable:
                mentionables.append(mentionable)
        return mentionables

    async def fetch(self, guild: Guild) -> List[Union[Member, Role]]:
        """A shortcut for fetching all :class:`nextcord.Member`'s and :class:`nextcord.Role`'s of :attr:`.values`.

        Mentionables that are not found in cache will be fetched.

        Parameters
        ----------
        guild: :class:`nextcord.Guild`
            The guild to get the mentionables from.

        Raises
        ------
        :exc:`.HTTPException`
            Fetching the mentionables failed.
        :exc:`.Forbidden`
            You do not have the proper permissions to fetch the mentionables.

        Returns
        -------
        List[Union[:class:`nextcord.Member`, :class:`nextcord.Role`]]
            A list of mentionables that have been selected by the user.
        """
        mentionables = self.get(guild)
        if len(mentionables) == len(self.data):
            return mentionables

        mentionables: List[Union[Member, Role]] = []
        guild_roles = None
        for id in self.data:
            mentionable = guild.get_member(id) or guild.get_role(id)
            if not mentionable:
                if not guild_roles:
                    guild_roles = await guild.fetch_roles()
                mentionable = get(guild_roles, id=id) or await guild.fetch_member(id)
            mentionables.append(mentionable)
        return mentionables


class MentionableSelect(SelectBase):

    """Represents a UI mentionable select menu.

    This is usually represented as a drop down menu.

    In order to get the selected items that the user has chosen,
    use :attr:`MentionableSelect.values`., :meth:`MentionableSelect.get_mentionables`
    or :meth:`MentionableSelect.fetch_mentionables`.

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
        Item.__init__(self)
        self._selected_values: List[str] = []
        self._provided_custom_id = custom_id is not MISSING
        custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        self._underlying = MentionableSelectMenu._raw_construct(
            custom_id=custom_id,
            type=ComponentType.mentionable_select,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
        )
        self.row = row

    @property
    def values(self) -> MentionableSelectValues:
        """List[:class:`int`]: A list of mentionable ids that have been selected by the user."""
        return MentionableSelectValues([int(id) for id in self._selected_values])

    def to_component_dict(self) -> MentionableSelectMenuPayload:
        return self._underlying.to_dict()
    
    @classmethod
    def from_component(cls: Type[S], component: MentionableSelectMenu) -> S:
        return cls(
            custom_id=component.custom_id,
            placeholder=component.placeholder,
            min_values=component.min_values,
            max_values=component.max_values,
            disabled=component.disabled,
            row=None,
        )


def mentionable_select(
    *,
    placeholder: Optional[str] = None,
    custom_id: str = MISSING,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: Optional[int] = None,
) -> Callable[[ItemCallbackType], ItemCallbackType]:
    """A decorator that attaches a mentionable select menu to a component.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`nextcord.ui.View`, the :class:`nextcord.ui.MentionableSelect` being pressed and
    the :class:`nextcord.Interaction` you receive.

    In order to get the selected items that the user has chosen within the callback
    use :attr:`MentionableSelect.values`., :attr:`MentionableSelect.get_mentionables`
    or :attr:`MentionableSelect.fetch_mentionables`.

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
