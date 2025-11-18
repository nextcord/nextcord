# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, TypeVar, Union

from .item import Item
from ..enums import ComponentType
from ..components import UnfurledMediaItem
from ..file import File
from ..utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView
    from ..components import ThumbnailComponent

V = TypeVar("V", bound="LayoutView", covariant=True)

__all__ = ("Thumbnail",)


class Thumbnail(Item[V]):
    """Represents a UI Thumbnail. This currently can only be used as a :class:`Section`'s accessory.

        .. versionadded:: 3.12

    Parameters
    ----------
    media: Union[:class:`str`, :class:`File`, :class:`UnfurledMediaItem`]
        The media of the thumbnail. This can be a URL or a reference
        to an attachment that matches the ``attachment://filename.extension``
        structure.
    description: Optional[:class:`str`]
        The description of this thumbnail. Up to 256 characters. Defaults to ``None``.
    spoiler: :class:`bool`
        Whether to flag this thumbnail as a spoiler. Defaults to ``False``.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.

    Attributes
    ----------
    media: :class:`UnfurledMediaItem`
        This thumbnail unfurled media data.
    description: Optional[:class:`str`]
        The description of this thumbnail.
    spoiler: :class:`bool`
        Whether this thumbnail is flagged as a spoiler.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__ = (
        "_media",
        "description",
        "spoiler",
    )

    __item_repr_attributes__ = (
        "media",
        "description",
        "spoiler",
        "row",
        "id",
    )

    def __init__(
        self,
        media: Union[str, File, UnfurledMediaItem],
        *,
        description: Optional[str] = MISSING,
        spoiler: bool = MISSING,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()

        if isinstance(media, File):
            description = description if description is not MISSING else media.description
            spoiler = spoiler if spoiler is not MISSING else media.spoiler
            media_url = f"attachment://{media.filename}"
        elif isinstance(media, str):
            media_url = media
        else:
            media_url = media.url if isinstance(media, UnfurledMediaItem) else str(media)

        self._media: UnfurledMediaItem = (
            UnfurledMediaItem(media_url)
            if isinstance(media, (str, File))
            else media
        )
        self.description: Optional[str] = None if description is MISSING else description
        self.spoiler: bool = False if spoiler is MISSING else bool(spoiler)

        self.id = id

    @property
    def width(self) -> int:
        return 5

    @property
    def media(self) -> UnfurledMediaItem:
        """:class:`UnfurledMediaItem`: This thumbnail unfurled media data."""
        return self._media

    @media.setter
    def media(self, value: Union[str, File, UnfurledMediaItem]) -> None:  # type: ignore
        if isinstance(value, str):
            self._media = UnfurledMediaItem(value)
        elif isinstance(value, UnfurledMediaItem):
            self._media = value
        elif isinstance(value, File):
            self._media = UnfurledMediaItem(f"attachment://{value.filename}")
        else:
            raise TypeError(
                f"expected a str, File, or UnfurledMediaItem, not {value.__class__.__name__!r}"
            )

    @property
    def type(self) -> Literal[ComponentType.thumbnail]:
        return ComponentType.thumbnail

    def _is_v2(self) -> bool:
        return True

    def to_component_dict(self) -> Dict[str, Any]:
        base = {
            "type": self.type.value,
            "spoiler": self.spoiler,
            "media": self.media.to_dict(),
            "description": self.description,
        }
        if self.id is not None:
            base["id"] = self.id
        return base

    @classmethod
    def from_component(cls, component: ThumbnailComponent) -> Self:
        return cls(
            media=component.media.url,
            description=component.description,
            spoiler=component.spoiler,
            id=component.id,
        )

