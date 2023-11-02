from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Coroutine, TypeVar

if TYPE_CHECKING:
    from ..client import Client
    from ..interactions import ClientT, Interaction
    from .item import Item, ModalItem, ViewItem
    from .modal import Modal
    from .view import View


# TODO: Maybe move this to discord/interactions.py?
if TYPE_CHECKING:
    from typing_extensions import TypeVar  # noqa: F811

    ClientT = TypeVar("ClientT", bound="Client", default="Client")
else:
    ClientT = TypeVar("ClientT", bound="Client")


ModalT_co = TypeVar("ModalT_co", bound="Modal", covariant=True)
ViewT_co = TypeVar("ViewT_co", bound="View", covariant=True)
ItemT_co = TypeVar("ItemT_co", bound="Item", covariant=True)
ModalItem_co = TypeVar("ModalItem_co", bound="ModalItem[Modal]", covariant=True)
ViewItem_co = TypeVar("ViewItem_co", bound="ViewItem[View]", covariant=True)

ItemCallbackType = Callable[[Any, ItemT_co, Interaction[ClientT]], Coroutine[Any, Any, Any]]
