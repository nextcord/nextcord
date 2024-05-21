# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
import os
import sys
import time
import traceback
from functools import partial
from itertools import groupby
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

from ..components import Component
from ..utils import MISSING
from .item import Item
from .view import _component_to_item, _ViewWeights, _walk_all_components

__all__ = (
    "Modal",
    "ModalStore",
)


if TYPE_CHECKING:
    from ..interactions import ClientT, Interaction
    from ..state import ConnectionState
    from ..types.components import ActionRow as ActionRowPayload
    from ..types.interactions import (
        ComponentInteractionData,
        ModalSubmitComponentInteractionData,
        ModalSubmitInteractionData,
    )


def _walk_component_interaction_data(
    components: List[ModalSubmitComponentInteractionData],
) -> Iterator[ComponentInteractionData]:
    for item in components:
        if "components" in item:
            yield from item["components"]  # type: ignore
        else:
            yield item


class Modal:
    """Represents a Discord modal popup.

    This object must be inherited to create a modal within Discord.

    .. versionadded:: 2.0

    Parameters
    ----------
    title: :class:`str`
        The title of the modal.
    timeout: Optional[:class:`float`] = None
        Timeout in seconds from last interaction with the UI before no longer accepting input.
        If ``None`` then there is no timeout.
    custom_id: :class:`str` = MISSING
        The ID of the modal that gets received during an interaction.
        If the ``custom_id`` is MISSING, then a random ``custom_id`` is set.
    auto_defer: :class:`bool` = True
        Whether or not to automatically defer the modal when the callback completes
        without responding to the interaction. Set this to ``False`` if you want to
        handle the modal interaction outside of the callback.

    Attributes
    ----------
    title: :class:`str`
        The title of the modal.
    timeout: Optional[:class:`float`]
        Timeout from last interaction with the UI before no longer accepting input.
        If ``None`` then there is no timeout.
    children: List[:class:`Item`]
        The list of children attached to this modal.
    custom_id: :class:`str`
        The ID of the modal that gets received during an interaction.
    auto_defer: :class:`bool` = True
        Whether or not to automatically defer the modal when the callback completes
        without responding to the interaction. Set this to ``False`` if you want to
        handle the modal interaction outside of the callback.
    """

    def __init__(
        self,
        title: str,
        *,
        timeout: Optional[float] = None,
        custom_id: str = MISSING,
        auto_defer: bool = True,
    ) -> None:
        self.title = title
        self.timeout = timeout
        self._provided_custom_id = custom_id is not MISSING
        self.custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        self.auto_defer = auto_defer

        self.children = []
        self.__weights = _ViewWeights(self.children)
        loop = asyncio.get_running_loop()
        self.id: str = os.urandom(16).hex()
        self.__cancel_callback: Optional[Callable[[Modal], None]] = None
        self.__timeout_expiry: Optional[float] = None
        self.__timeout_task: Optional[asyncio.Task[None]] = None
        self.__background_tasks: Set[asyncio.Task[None]] = set()
        self.__stopped: asyncio.Future[bool] = loop.create_future()

    async def __timeout_task_impl(self) -> None:
        while True:
            # Guard just in case someone changes the value of the timeout at runtime
            if self.timeout is None:
                return None

            if self.__timeout_expiry is None:
                return self._dispatch_timeout()

            # Check if we've elapsed our currently set timeout
            now = time.monotonic()
            if now >= self.__timeout_expiry:
                return self._dispatch_timeout()

            # Wait N seconds to see if timeout data has been refreshed
            await asyncio.sleep(self.__timeout_expiry - now)

    def to_components(self) -> List[ActionRowPayload]:
        def key(item: Item) -> int:
            return item._rendered_row or 0

        children = sorted(self.children, key=key)
        components: List[ActionRowPayload] = []
        for _, group in groupby(children, key=key):
            children = [item.to_component_dict() for item in group]
            if not children:
                continue

            components.append(
                {
                    "type": 1,
                    "components": children,
                }
            )

        return components

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "custom_id": self.custom_id,
            "components": self.to_components(),
        }

    @property
    def _expires_at(self) -> Optional[float]:
        """The monotonic time this modal times out at.

        Returns
        -------
        Optional[float]
            When this modal times out.

            None if no timeout is set.
        """
        return self.__timeout_expiry

    def add_item(self, item: Item) -> Modal:
        r"""Adds an item to the modal.

        Parameters
        ----------
        item: :class:`Item`
            The item to add to the modal.

            .. note::

                The only items that are currently supported are :class:`TextInput`\s.

        Raises
        ------
        TypeError
            An :class:`Item` was not passed.
        ValueError
            The row the item is trying to be added to is full.
        """

        if not isinstance(item, Item):
            raise TypeError(f"Expected Item not {item.__class__!r}")

        self.__weights.add_item(item)

        self.children.append(item)

        return self

    def remove_item(self, item: Item) -> Modal:
        """Removes an item from the modal.

        Parameters
        ----------
        item: :class:`Item`
            The item to remove from the modal.
        """

        try:
            self.children.remove(item)
        except ValueError:
            pass
        else:
            self.__weights.remove_item(item)

        return self

    def clear_items(self) -> None:
        """Removes all items from the modal."""
        self.children.clear()
        self.__weights.clear()

    async def callback(self, interaction: Interaction) -> None:
        """|coro|

        The callback that is called when the user press the submit button.

        The default implementation does nothing and the user sees an error
        message on their screen, so you need to overwrite this function.

        Parameters
        ----------
        interaction: :class:`Interaction`
            The interaction fired by the user.

        """

    async def on_timeout(self) -> None:
        """|coro|

        A callback that is called when a modal's timeout elapses without being explicitly stopped.
        """

    async def on_error(self, error: Exception, interaction: Interaction) -> None:
        """|coro|

        A callback that is called when an item's callback or :meth:`interaction_check`
        fails with an error.

        The default implementation prints the traceback to stderr.

        Parameters
        ----------
        error: :class:`Exception`
            The exception that was raised.
        item: :class:`Item`
            The item that failed the dispatch.
        interaction: :class:`~nextcord.Interaction`
            The interaction that led to the failure.
        """
        print(f"Ignoring exception in modal {self}:", file=sys.stderr)  # noqa: T201
        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    async def _scheduled_task(self, interaction: Interaction):
        data: ModalSubmitInteractionData = interaction.data  # type: ignore
        for child in self.children:
            for component_data in _walk_component_interaction_data(data["components"]):
                if component_data["custom_id"] == child.custom_id:  # type: ignore
                    child.refresh_state(component_data, interaction._state, interaction.guild)
                    break
        try:
            if self.timeout:
                self.__timeout_expiry = time.monotonic() + self.timeout

            await self.callback(interaction)
            if (
                not interaction.response._responded
                and not interaction.is_expired()
                and self.auto_defer
            ):
                await interaction.response.defer()
        except Exception as e:
            return await self.on_error(e, interaction)

    def _start_listening_from_store(self, store: ModalStore) -> None:
        self.__cancel_callback = partial(store.remove_modal)
        if self.timeout:
            loop = asyncio.get_running_loop()
            if self.__timeout_task is not None:
                self.__timeout_task.cancel()

            self.__timeout_expiry = time.monotonic() + self.timeout
            self.__timeout_task = loop.create_task(self.__timeout_task_impl())

    def _dispatch_timeout(self) -> None:
        if self.__stopped.done():
            return

        task = asyncio.create_task(self.on_timeout(), name=f"discord-ui-modal-timeout-{self.id}")
        self.__background_tasks.add(task)
        task.add_done_callback(self.__background_tasks.discard)
        self.__stopped.set_result(True)

    def _dispatch(self, interaction: Interaction) -> None:
        if self.__stopped.done():
            return

        task = asyncio.create_task(
            self._scheduled_task(interaction), name=f"discord-ui-modal-dispatch-{self.id}"
        )
        self.__background_tasks.add(task)
        task.add_done_callback(self.__background_tasks.discard)

    def refresh(self, components: List[Component]) -> None:
        # This is pretty hacky at the moment
        old_state: Dict[Tuple[int, str], Item] = {
            (item.type.value, item.custom_id): item  # type: ignore
            # TODO: refactor this to explicitly type custom_id
            for item in self.children
            if item.is_dispatchable()
        }
        children: List[Item] = []
        for component in _walk_all_components(components):
            try:
                older = old_state[(component.type.value, component.custom_id)]  # type: ignore
            except (KeyError, AttributeError):
                children.append(_component_to_item(component))
            else:
                older.refresh_component(component)
                children.append(older)

        self.children = children

    def stop(self) -> None:
        """Stops listening to interaction events from this modal.

        This operation cannot be undone.
        """
        if not self.__stopped.done():
            self.__stopped.set_result(False)

        self.__timeout_expiry = None
        if self.__timeout_task is not None:
            self.__timeout_task.cancel()
            self.__timeout_task = None

        if self.__cancel_callback:
            self.__cancel_callback(self)
            self.__cancel_callback = None

    def is_finished(self) -> bool:
        """:class:`bool`: Whether the modal has finished interacting."""
        return self.__stopped.done()

    def is_dispatching(self) -> bool:
        """:class:`bool`: Whether the modal has been added for dispatching purposes."""
        return self.__cancel_callback is not None

    def is_persistent(self) -> bool:
        """:class:`bool`: Whether the modal is set up as persistent.

        A persistent modal has a set ``custom_id`` and all their components with a set ``custom_id`` and
        a :attr:`timeout` set to ``None``.
        """
        return (
            self._provided_custom_id
            and self.timeout is None
            and all(item.is_persistent() for item in self.children)
        )

    async def wait(self) -> bool:
        """Waits until the modal has finished interacting.

        A modal is considered finished when :meth:`stop` is called
        or it times out.

        Returns
        -------
        :class:`bool`
            If ``True``, then the modal timed out. If ``False`` then
            the modal finished normally.
        """
        return await self.__stopped


class ModalStore:
    def __init__(self, state: ConnectionState) -> None:
        # (user_id, custom_id): Modal  # noqa: ERA001
        self._modals: Dict[Tuple[int | None, str], Modal] = {}
        self._state: ConnectionState = state

    @property
    def persistent_modals(self) -> List[Modal]:
        # fmt: off
        modals = {
            modal.id: modal
            for (_, modal) in self._modals.items()
            if modal.is_persistent()
        }
        # fmt: on
        return list(modals.values())

    def __verify_integrity(self) -> None:
        to_remove: List[Tuple[int | None, str]] = []
        for k, modal in self._modals.items():
            if modal.is_finished():
                to_remove.append(k)

        for k in to_remove:
            del self._modals[k]

    def add_modal(self, modal: Modal, user_id: Optional[int] = None) -> None:
        self.__verify_integrity()

        modal._start_listening_from_store(self)
        self._modals[(user_id, modal.custom_id)] = modal

    def remove_modal(self, modal: Modal) -> None:
        _modals = self._modals.copy()
        for key, value in _modals.items():
            if value is modal:
                del self._modals[key]

    def dispatch(self, custom_id: str, interaction: Interaction[ClientT]) -> None:
        self.__verify_integrity()

        key = (interaction.user.id, custom_id)  # type: ignore
        # Fallback to None user_id searches in case a persistent modal
        # was added without an associated message_id
        modal = self._modals.get(key) or self._modals.get((None, custom_id))
        if modal is None:
            return

        modal._dispatch(interaction)
