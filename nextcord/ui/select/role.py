"""
The MIT License (MIT)

Copyright (c) 2021-present tag-epic

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
from typing import TYPE_CHECKING, Callable, List, Optional

from ...components import RoleSelectMenu, SelectOption
from ...enums import ComponentType
from ...utils import MISSING
from ..item import Item, ItemCallbackType
from .string import Select

if TYPE_CHECKING:
    from ...guild import Guild
    from ...role import Role
    from ...types.components import RoleSelectMenu as RoleSelectMenuPayload

__all__ = ("RoleSelect", "role_select")


class RoleSelect(Select):

    """Represents a UI role select menu.

    This is usually represented as a drop down menu.

    In order to get the selected items that the user has chosen,
    use :attr:`RoleSelect.values`., :meth:`RoleSelect.get_roles` or :meth:`RoleSelect.fetch_roles`.

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
        Whether the select is disabled or not.
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
        self._underlying = RoleSelectMenu._raw_construct(
            custom_id=custom_id,
            type=ComponentType.role_select,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
        )
        self.row = row

    @property
    def options(self) -> List[SelectOption]:
        """List[:class:`nextcord.SelectOption`]: A list of options that can be selected in this menu.
        This will always be an empty list since role selects cannot have any options.
        """
        return []

    @property
    def values(self) -> List[int]:
        """List[:class:`int`]: A list of role ids that have been selected by the user."""
        return [int(id) for id in self._selected_values]

    def get_roles(self, guild: Guild) -> List[Role]:
        """A shortcut for getting all :class:`nextcord.Role`'s of :attr:`.values`.
        Roles that are not found in cache will not be returned.
        To get all roles regardless of whether they are in cache or not, use :meth:`.fetch_roles`.

        Parameters
        ----------
        guild: :class:`nextcord.Guild`
            The guild to get the roles from.

        Returns
        -------
        List[:class:`nextcord.Role`]
            A list of roles that were found."""
        roles: List[Role] = []
        for id in self.values:
            member = guild.get_role(id)
            if member is not None:
                roles.append(member)
        return roles

    async def fetch_roles(self, guild: Guild) -> List[Role]:
        """A shortcut for fetching all :class:`nextcord.Role`'s of :attr:`.values`.
        Roles that are not found in cache will be fetched.

        Parameters
        ----------
        guild: :class:`nextcord.Guild`
            The guild to fetch the roles from.

        Raises
        ------
        :exc:`.HTTPException`
            Retrieving the roles failed.

        Returns
        -------
        List[:class:`nextcord.Role`]
            A list of all roles that have been selected."""
        roles: List[Role] = self.get_roles(guild)
        if len(roles) == len(self.values):
            return roles
        guild_roles: List[Role] = await guild.fetch_roles()
        for id in self.values:
            for role in guild_roles:
                if role.id == id:
                    roles.append(role)
                    break
        return roles
    
    def to_component_dict(self) -> RoleSelectMenuPayload:
        return self._underlying.to_dict()


def role_select(
    *,
    placeholder: Optional[str] = None,
    custom_id: str = MISSING,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: Optional[int] = None,
) -> Callable[[ItemCallbackType], ItemCallbackType]:
    """A decorator that attaches a role select menu to a component.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`nextcord.ui.View`, the :class:`nextcord.ui.RoleSelect` being pressed and
    the :class:`nextcord.Interaction` you receive.

    In order to get the selected items that the user has chosen within the callback
    use :attr:`RoleSelect.values`., :attr:`RoleSelect.get_roles` or :attr:`RoleSelect.fetch_roles`.

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
