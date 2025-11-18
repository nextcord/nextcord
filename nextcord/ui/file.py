# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, Literal, Optional, TypeVar, Union

from .item import Item
from ..components import FileComponent, UnfurledMediaItem
from ..enums import ComponentType
from ..utils import MISSING
from ..file import File as SendableFile

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView

V = TypeVar("V", bound="LayoutView", covariant=True)

__all__ = ("File",)


class File(Item[V]):
    """Represents a UI file component.

    This is a top-level layout component that can only be used on :class:`LayoutView`.

        .. versionadded:: 3.12

    Parameters
    ----------
    media: Union[:class:`str`, :class:`.UnfurledMediaItem`, :class:`File`]
        This file's media. If this is a string it must point to a local
        file uploaded within the parent view of this item, and must
        meet the ``attachment://<filename>`` format.
    spoiler: :class:`bool`
        Whether to flag this file as a spoiler. Defaults to ``False``.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.

    Attributes
    ----------
    media: :class:`.UnfurledMediaItem`
        This file's media.
    spoiler: :class:`bool`
        Whether this file is flagged as a spoiler.
    url: :class:`str`
        This file's URL.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __item_repr_attributes__ = (
        "media",
        "spoiler",
        "id",
    )

    def __init__(
        self,
        media: Union[str, UnfurledMediaItem, SendableFile],
        *,
        spoiler: bool = MISSING,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        if isinstance(media, SendableFile):
            media_url = f"attachment://{media.filename}"
            spoiler_value = media.spoiler if spoiler is MISSING else spoiler
            self._underlying = FileComponent._raw_construct(
                media=UnfurledMediaItem(media_url),
                spoiler=spoiler_value,
                id=id,
            )
        else:
            spoiler_value = False if spoiler is MISSING else bool(spoiler)
            self._underlying = FileComponent._raw_construct(
                media=UnfurledMediaItem(media) if isinstance(media, str) else media,
                spoiler=spoiler_value,
                id=id,
            )

    @property
    def id(self) -> Optional[int]:
        """Optional[:class:`int`]: The ID of this file component."""
        return self._underlying.id

    @id.setter
    def id(self, value: Optional[int]) -> None:
        self._underlying.id = value

    def _is_v2(self) -> bool:
        return True

    @property
    def width(self) -> int:
        return 5

    @property
    def type(self) -> Literal[ComponentType.file]:
        return self._underlying.type

    @property
    def media(self) -> UnfurledMediaItem:
        """:class:`.UnfurledMediaItem`: Returns this file media."""
        return self._underlying.media

    @media.setter
    def media(self, value: Union[str, SendableFile, UnfurledMediaItem]) -> None:  # type: ignore
        if isinstance(value, str):
            self._underlying.media = UnfurledMediaItem(value)
        elif isinstance(value, UnfurledMediaItem):
            self._underlying.media = value
        elif isinstance(value, SendableFile):
            self._underlying.media = UnfurledMediaItem(f"attachment://{value.filename}")
        else:
            raise TypeError(
                f"expected a str, UnfurledMediaItem, or File, not {value.__class__.__name__!r}"
            )

    @property
    def url(self) -> str:
        """:class:`str`: Returns this file's url."""
        return self._underlying.media.url

    @url.setter
    def url(self, value: str) -> None:
        self._underlying.media = UnfurledMediaItem(value)

    @property
    def spoiler(self) -> bool:
        """:class:`bool`: Returns whether this file should be flagged as a spoiler."""
        return self._underlying.spoiler

    @spoiler.setter
    def spoiler(self, value: bool) -> None:
        self._underlying.spoiler = value

    def to_component_dict(self) -> Dict[str, Any]:
        return self._underlying.to_dict()  # type: ignore

    @classmethod
    def from_component(cls, component: FileComponent) -> Self:
        return cls(
            media=component.media,
            spoiler=component.spoiler,
            id=component.id,
        )

