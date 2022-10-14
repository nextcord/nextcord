"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz
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
from typing import TYPE_CHECKING, Callable, List, Optional, Union

from ...components import SelectMenu, SelectOption
from ...enums import ComponentType
from ...utils import MISSING
from ..item import Item, ItemCallbackType
from .string_select import Select

if TYPE_CHECKING:
    from ...abc import GuildChannel
    from ...enums import ChannelType
    from ...guild import Guild
    from ...threads import Thread

__all__ = ("ChannelSelect", "channel_select")


class ChannelSelect(Select):

    """Represents a UI channel select menu.

    This is usually represented as a drop down menu.

    In order to get the selected items that the user has chosen,
    use :attr:`Select.values`., :meth:`Select.get_channels` or :meth:`Select.fetch_channels`.

    .. versionadded:: 2.0

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
    channel_types: List[:class:`nextcord.ChannelType`]
        The types of channels that can be selected. If not given, all channel types are allowed.
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
        channel_types: List[ChannelType] = MISSING,
    ) -> None:
        Item.__init__(self)
        self._selected_values: List[str] = []
        self._provided_custom_id = custom_id is not MISSING
        custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        kwargs = {}
        if channel_types is not MISSING:
            kwargs["channel_types"] = channel_types
        self._underlying = SelectMenu._raw_construct(
            custom_id=custom_id,
            type=ComponentType.channel_select,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            **kwargs,
        )
        self.row = row

    @property
    def options(self) -> List[SelectOption]:
        """List[:class:`nextcord.SelectOption`]: A list of options that can be selected in this menu.
        This will always be an empty list since channel selects cannot have any options."""
        return []

    @property
    def values(self) -> List[int]:
        """List[:class:`int`]: A list of channel ids that have been selected by the user."""
        return [int(id) for id in self._selected_values]

    def get_channels(self, guild: Guild) -> List[Union[GuildChannel, Thread]]:
        """A shortcut for getting all :class:`nextcord.abc.GuildChannel`'s of :attr:`.values`.
        Channels that are not found in cache will not be returned.
        To get all channels regardless of whether they are in cache or not, use :meth:`.fetch_channels`.

        Parameters
        ----------
        guild: :class:`nextcord.Guild`
            The guild to get the channels from.

        Returns
        -------
        List[Union[:class:`nextcord.abc.GuildChannel`, :class:`nextcord.Thread`]]
            A list of channels that have been selected by the user.
        """
        channels: List[Union[GuildChannel, Thread]] = []
        for id in self.values:
            channel = guild.get_channel_or_thread(id)
            if channel is not None:
                channels.append(channel)
        return channels

    async def fetch_channels(self, guild: Guild) -> List[Union[GuildChannel, Thread]]:
        """A shortcut for fetching all :class:`nextcord.abc.GuildChannel`'s of :attr:`.values`.
        Channels that are not found in cache will be fetched.

        Parameters
        ----------
        guild: :class:`nextcord.Guild`
            The guild to get the channels from.

        Raises
        ------
        :exc:`.HTTPException`
            Fetching the channels failed.
        :exc:`.NotFound`
            A channel was not found.
        :exc:`.Forbidden`
            You do not have the proper permissions to fetch a channel.
        :exc:`.InvalidArgument`
            The channel type is not supported.

        Returns
        -------
        List[Union[:class:`nextcord.abc.GuildChannel`, :class:`nextcord.Thread`]]
            A list of channels that have been selected by the user.
        """
        channels: List[Union[GuildChannel, Thread]] = []
        guild_channels = None
        for id in self.values:
            channel = guild.get_channel_or_thread(id)
            if channel is None:
                if guild_channels is None:
                    guild_channels = await guild.fetch_channels()
                for channel in guild_channels:
                    if channel.id == id:
                        channels.append(channel)
                        break
            else:
                channels.append(channel)
        return channels


def channel_select(
    *,
    placeholder: Optional[str] = None,
    custom_id: str = MISSING,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: Optional[int] = None,
    channel_types: List[ChannelType] = MISSING,
) -> Callable[[ItemCallbackType], ItemCallbackType]:
    """A decorator that attaches a channel select menu to a component.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`nextcord.ui.View`, the :class:`nextcord.ui.ChannelSelect` being pressed and
    the :class:`nextcord.Interaction` you receive.

    In order to get the selected items that the user has chosen within the callback
    use :attr:`Select.values`., :attr:`Select.get_channels` or :attr:`Select.fetch_channels`.

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
    channel_types: List[:class:`nextcord.ChannelType`]
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
