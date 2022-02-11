from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List, Callable, Dict, Any, Tuple, Sequence
from functools import partial
from itertools import groupby

import traceback
import asyncio
import os
import time
import sys
from ..utils import MISSING
from .view import (
    _ViewWeights,
    _walk_all_components,
    _component_to_item,
)
from .item import Item
from ..components import Component, _component_factory

if TYPE_CHECKING:
    from ..interactions import Interaction
    from ..state import ConnectionState
    from ..types.components import Component as ComponentPayload

__all__ = (
    'Modal',
    'ModalStore',
)

class Modal:
    def __init__(
        self,
        title: str,
        *,
        timeout: Optional[float] = 180.0,
        custom_id: str = MISSING,
        **components,
    ):
        self.title = title
        self.timeout = timeout
        self._provided_custom_id = custom_id is not MISSING
        self.custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        
        self.children: List[Item] = []
        for key, component in components.items():
            setattr(self, key, component)
            self.children.append(component)
        
        self.__weights = _ViewWeights(self.children)
        loop = asyncio.get_running_loop()
        self.id: str = os.urandom(16).hex()
        self.__cancel_callback: Optional[Callable[[Modal], None]] = None
        self.__timeout_expiry: Optional[float] = None
        self.__timeout_task: Optional[asyncio.Task[None]] = None
        self.__stopped: asyncio.Future[bool] = loop.create_future()
    
    async def __timeout_task_impl(self) -> None:
        while True:
            # Guard just in case someone changes the value of the timeout at runtime
            if self.timeout is None:
                return

            if self.__timeout_expiry is None:
                return self._dispatch_timeout()

            # Check if we've elapsed our currently set timeout
            now = time.monotonic()
            if now >= self.__timeout_expiry:
                return self._dispatch_timeout()

            # Wait N seconds to see if timeout data has been refreshed
            await asyncio.sleep(self.__timeout_expiry - now)

    def to_components(self) -> List[Dict[str, Any]]:
        def key(item: Item) -> int:
            return item._rendered_row or 0

        children = sorted(self.children, key=key)
        components: List[Dict[str, Any]] = []
        for _, group in groupby(children, key=key):
            children = [item.to_component_dict() for item in group]
            if not children:
                continue

            components.append(
                {
                    'type': 1,
                    'components': children,
                }
            )

        return components

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            'title': self.title,
            'custom_id': self.custom_id,
            'components': self.to_components(),
        }
        return payload
    
    @property
    def _expires_at(self) -> Optional[float]:
        if self.timeout:
            return time.monotonic() + self.timeout
        return None
    
    def add_item(self, item: Item) -> None:
        """Adds an item to the modal.

        Parameters
        -----------
        item: :class:`Item`
            The item to add to the modal.

        Raises
        --------
        TypeError
            An :class:`Item` was not passed.
        ValueError
            Maximum number of children has been exceeded (25)
            or the row the item is trying to be added to is full.
        """

        if len(self.children) > 25:
            raise ValueError('maximum number of children exceeded')

        if not isinstance(item, Item):
            raise TypeError(f'expected Item not {item.__class__!r}')

        self.__weights.add_item(item)

        self.children.append(item)

    def remove_item(self, item: Item) -> None:
        """Removes an item from the modal.

        Parameters
        -----------
        item: :class:`Item`
            The item to remove from the view.
        """

        try:
            self.children.remove(item)
        except ValueError:
            pass
        else:
            self.__weights.remove_item(item)

    def clear_items(self) -> None:
        """Removes all items from the view."""
        self.children.clear()
        self.__weights.clear()
    
    async def callback(self, interaction: Interaction):
        pass
    
    async def interaction_check(self, interaction: Interaction) -> bool:
        """|coro|

        A callback that is called when an interaction happens within the view
        that checks whether the view should process item callbacks for the interaction.

        This is useful to override if, for example, you want to ensure that the
        interaction author is a given user.

        The default implementation of this returns ``True``.

        .. note::

            If an exception occurs within the body then the check
            is considered a failure and :meth:`on_error` is called.

        Parameters
        -----------
        interaction: :class:`~nextcord.Interaction`
            The interaction that occurred.

        Returns
        ---------
        :class:`bool`
            Whether the view children's callbacks should be called.
        """
        return True
        
    async def on_timeout(self) -> None:
        """|coro|

        A callback that is called when a modal's timeout elapses without being explicitly stopped.
        """
        pass
    
    async def on_error(self, error: Exception, interaction: Interaction) -> None:
        """|coro|

        A callback that is called when an item's callback or :meth:`interaction_check`
        fails with an error.

        The default implementation prints the traceback to stderr.

        Parameters
        -----------
        error: :class:`Exception`
            The exception that was raised.
        item: :class:`Item`
            The item that failed the dispatch.
        interaction: :class:`~nextcord.Interaction`
            The interaction that led to the failure.
        """
        print(f'Ignoring exception in modal {self}:', file=sys.stderr)
        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)
    
    async def _scheduled_task(self, interaction: Interaction):
        for children in self.children:
            children.refresh_state(interaction)
        try:
            if self.timeout:
                self.__timeout_expiry = time.monotonic() + self.timeout

            allow = await self.interaction_check(interaction)
            if not allow:
                return

            await self.callback(interaction)
            if not interaction.response._responded:
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
    
    def _dispatch_timeout(self):
        if self.__stopped.done():
            return

        self.__stopped.set_result(True)
        asyncio.create_task(self.on_timeout(), name=f'discord-ui-view-timeout-{self.id}')
    
    def _dispatch(self, interaction: Interaction):
        if self.__stopped.done():
            return

        asyncio.create_task(self._scheduled_task(interaction), name=f'discord-ui-view-dispatch-{self.id}')
    
    def refresh(self, components: List[Component]):
        # This is pretty hacky at the moment
        # fmt: off
        old_state: Dict[Tuple[int, str], Item] = {
            (item.type.value, item.custom_id): item  # type: ignore
            for item in self.children
            if item.is_dispatchable()
        }
        # fmt: on
        children: List[Item] = []
        for component in _walk_all_components(components):
            try:
                older = old_state[(component.type.value, component.custom_id)]  # type: ignore
            except (KeyError, AttributeError):
                print("error", component)
                children.append(_component_to_item(component))
            else:
                older.refresh_component(component)
                children.append(older)

        self.children = children
    
    def stop(self) -> None:
        """Stops listening to interaction events from this view.

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
        """:class:`bool`: Whether the view has finished interacting."""
        return self.__stopped.done()

    def is_dispatching(self) -> bool:
        """:class:`bool`: Whether the view has been added for dispatching purposes."""
        return self.__cancel_callback is not None

    def is_persistent(self) -> bool:
        """:class:`bool`: Whether the view is set up as persistent.

        A persistent view has all their components with a set ``custom_id`` and
        a :attr:`timeout` set to ``None``.
        """
        return self._provided_custom_id and self.timeout is None and all(item.is_persistent() for item in self.children)

    async def wait(self) -> bool:
        """Waits until the view has finished interacting.

        A view is considered finished when :meth:`stop` is called
        or it times out.

        Returns
        --------
        :class:`bool`
            If ``True``, then the view timed out. If ``False`` then
            the view finished normally.
        """
        return await self.__stopped

class ModalStore:
    def __init__(self, state: ConnectionState):
        # (user_id, custom_id): Modal
        self._modals: Dict[Tuple[int, str], Modal] = {}
        self._state: ConnectionState = state

    @property
    def persistent_modals(self) -> Sequence[Modal]:
        # fmt: off
        modals = {
            modal.id: modal
            for (_, modal) in self._modals.items()
            if modal.is_persistent()
        }
        # fmt: on
        return list(modals.values())

    def __verify_integrity(self):
        to_remove: List[Tuple[int, Optional[int], str]] = []
        for (k, modal) in self._modals.items():
            if modal.is_finished():
                to_remove.append(k)

        for k in to_remove:
            del self._modals[k]

    def add_modal(self, modal: Modal, user_id: Optional[int] = None):
        self.__verify_integrity()

        modal._start_listening_from_store(self)
        self._modals[(user_id, modal.custom_id)] = modal

    def remove_modal(self, modal: Modal):
        self._modals.popitem(modal)

    def dispatch(self, custom_id: str, interaction: Interaction):
        self.__verify_integrity()
        
        key = (interaction.user.id, custom_id)
        # Fallback to None user_id searches in case a persistent modal
        # was added without an associated message_id
        modal = self._modals.get(key) or self._modals.get((None, custom_id))
        if modal is None:
            return
        
        modal._dispatch(interaction)
