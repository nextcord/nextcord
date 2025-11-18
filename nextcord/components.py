# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, List, Literal, Optional, Tuple, TypeVar, Union, cast

from .enums import (
    ButtonStyle,
    ComponentType,
    MediaItemLoadingState,
    SeparatorSpacing,
    TextInputStyle,
    try_enum,
)
from .partial_emoji import PartialEmoji, _EmojiTag
from .utils import MISSING, get_slots

if TYPE_CHECKING:
    from typing_extensions import Self

    from .channel import ChannelType
    from .colour import Colour
    from .emoji import Emoji
    from .file import File
    from .state import ConnectionState
    from .types.components import (
        ActionRow as ActionRowPayload,
        ButtonComponent as ButtonComponentPayload,
        ChannelSelectMenu as ChannelSelectMenuPayload,
        Component as ComponentPayload,
        ContainerComponent as ContainerComponentPayload,
        FileComponent as FileComponentPayload,
        FileUploadComponent as FileUploadComponentPayload,
        LabelComponent as LabelComponentPayload,
        MediaGalleryComponent as MediaGalleryComponentPayload,
        MediaGalleryItem as MediaGalleryItemPayload,
        MentionableSelectMenu as MentionableSelectMenuPayload,
        RoleSelectMenu as RoleSelectMenuPayload,
        SectionComponent as SectionComponentPayload,
        SelectMenu as SelectMenuPayload,
        SelectMenuBase as SelectMenuBasePayload,
        SelectOption as SelectOptionPayload,
        SeparatorComponent as SeparatorComponentPayload,
        TextComponent as TextComponentPayload,
        TextInputComponent as TextInputComponentPayload,
        ThumbnailComponent as ThumbnailComponentPayload,
        UnfurledMediaItem as UnfurledMediaItemPayload,
        UserSelectMenu as UserSelectMenuPayload,
    )


__all__ = (
    "Component",
    "ActionRow",
    "Button",
    "SelectMenu",
    "SelectOption",
    "TextInput",
    "UnfurledMediaItem",
    "MediaGalleryItem",
    "TextDisplay",
    "ThumbnailComponent",
    "MediaGalleryComponent",
    "FileComponent",
    "SeparatorComponent",
    "SectionComponent",
    "Container",
    "LabelComponent",
    "FileUploadComponent",
)

C = TypeVar("C", bound="Component")


class Component:
    """Represents a Discord Bot UI Kit Component.

    Currently, the components supported by Discord are:

    - :class:`ActionRow`
    - :class:`Button`
    - :class:`SelectMenu`
    - :class:`TextInput`
    - :class:`UserSelectMenu`
    - :class:`ChannelSelectMenu`
    - :class:`RoleSelectMenu`
    - :class:`MentionableSelectMenu`
    - :class:`SectionComponent`
    - :class:`TextDisplay`
    - :class:`ThumbnailComponent`
    - :class:`MediaGalleryComponent`
    - :class:`FileComponent`
    - :class:`SeparatorComponent`
    - :class:`Container`
    - :class:`LabelComponent`
    - :class:`FileUploadComponent`

    This class is abstract and cannot be instantiated.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    """

    __slots__: Tuple[str, ...] = ()

    __repr_info__: ClassVar[Tuple[str, ...]]
    type: ComponentType

    def __repr__(self) -> str:
        attrs = " ".join(f"{key}={getattr(self, key)!r}" for key in self.__repr_info__)
        return f"<{self.__class__.__name__} {attrs}>"

    @classmethod
    def _raw_construct(cls, **kwargs) -> Self:
        self = cls.__new__(cls)
        for slot in get_slots(cls):
            try:
                value = kwargs[slot]
            except KeyError:
                pass
            else:
                setattr(self, slot, value)
        return self

    def to_dict(self) -> ComponentPayload:
        raise NotImplementedError


class ActionRow(Component):
    """Represents a Discord Bot UI Kit Action Row.

    This is a component that holds up to 5 children components in a row.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    children: List[:class:`Component`]
        The children components that this holds, if any.
    """

    __slots__: Tuple[str, ...] = ("type", "children")

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ComponentPayload) -> None:
        self.type: ComponentType = try_enum(ComponentType, data["type"])
        self.children: List[Component] = [
            comp for d in data.get("components", []) if (comp := _component_factory(d)) is not None
        ]

    def to_dict(self) -> ActionRowPayload:
        return {
            "type": cast(Literal[1], int(self.type)),
            "components": [child.to_dict() for child in self.children],
        }


class Button(Component):
    """Represents a button from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a button is :class:`nextcord.ui.Button`
        not this one.

    .. versionadded:: 2.0

    Attributes
    ----------
    style: :class:`.ButtonStyle`
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
    emoji: Optional[:class:`PartialEmoji`]
        The emoji of the button, if available.
    """

    __slots__: Tuple[str, ...] = (
        "type",
        "style",
        "custom_id",
        "url",
        "disabled",
        "label",
        "emoji",
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ButtonComponentPayload) -> None:
        self.type: ComponentType = try_enum(ComponentType, data["type"])
        self.style: ButtonStyle = try_enum(ButtonStyle, data["style"])
        self.custom_id: Optional[str] = data.get("custom_id")
        self.url: Optional[str] = data.get("url")
        self.disabled: bool = data.get("disabled", False)
        self.label: Optional[str] = data.get("label")
        self.emoji: Optional[PartialEmoji] = None
        if "emoji" in data:
            self.emoji = PartialEmoji.from_dict(data["emoji"])

    def to_dict(self) -> ButtonComponentPayload:
        payload = {
            "type": 2,
            "style": int(self.style),
            "label": self.label,
            "disabled": self.disabled,
        }
        if self.custom_id:
            payload["custom_id"] = self.custom_id

        if self.url:
            payload["url"] = self.url

        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()

        return payload  # type: ignore


class SelectMenuBase(Component):
    """Represents a Discord Bot UI Kit Select Menu.

    This is the base class for all select menus.

    .. versionadded:: 2.3

    Attributes
    ----------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
    disabled: :class:`bool`
        Whether the select menu is disabled or not. Defaults to ``False``.
    placeholder: Optional[:class:`str`]
        The placeholder of the select menu, if any.
    min_values: :class:`int`
        The minimum number of values that must be chosen. Defaults to 1.
    max_values: :class:`int`
        The maximum number of values that can be chosen. Defaults to 1.
    """

    __slots__: Tuple[str, ...] = (
        "custom_id",
        "disabled",
        "placeholder",
        "min_values",
        "max_values",
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: SelectMenuBasePayload) -> None:
        self.custom_id: str = data["custom_id"]
        self.disabled: bool = data.get("disabled", False)
        self.placeholder: Optional[str] = data.get("placeholder")
        self.min_values: int = data.get("min_values", 1)
        self.max_values: int = data.get("max_values", 1)

    def to_dict(self) -> SelectMenuBasePayload:
        payload: SelectMenuBasePayload = {
            "custom_id": self.custom_id,
            "disabled": self.disabled,
            "min_values": self.min_values,
            "max_values": self.max_values,
        }

        if self.placeholder:
            payload["placeholder"] = self.placeholder

        return payload


class StringSelectMenu(SelectMenuBase):
    """Represents a string select menu from the Discord Bot UI Kit.

    A select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    There is an alias for this class called ``SelectMenu``.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`nextcord.ui.Select` not this one.

    .. versionadded:: 2.0

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    options: List[:class:`SelectOption`]
        A list of options that can be selected in this menu.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    """

    __slots__: Tuple[str, ...] = ("options",)
    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    type: Literal[ComponentType.select] = ComponentType.select

    def __init__(self, data: SelectMenuPayload) -> None:
        super().__init__(data)
        self.options: List[SelectOption] = [
            SelectOption.from_dict(option) for option in data.get("options", [])
        ]

    def to_dict(self) -> SelectMenuPayload:
        payload: SelectMenuPayload = {
            "type": self.type.value,
            "options": [op.to_dict() for op in self.options],
            **super().to_dict(),
        }

        return payload


SelectMenu = StringSelectMenu


class UserSelectMenu(SelectMenuBase):
    """Represents a user select menu from the Discord Bot UI Kit.

    A user select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`nextcord.ui.UserSelect` not this one.

    .. versionadded:: 2.3

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
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
    """

    __slots__: Tuple[str, ...] = ()
    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    type: Literal[ComponentType.user_select] = ComponentType.user_select

    def __init__(self, data: UserSelectMenuPayload) -> None:
        super().__init__(data)

    def to_dict(self) -> UserSelectMenuPayload:
        payload: UserSelectMenuPayload = {"type": self.type.value, **super().to_dict()}

        return payload


class RoleSelectMenu(SelectMenuBase):
    """Represents a role select menu from the Discord Bot UI Kit.

    A role select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`nextcord.ui.RoleSelect` not this one.

    .. versionadded:: 2.3

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
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
    """

    __slots__: Tuple[str, ...] = ()
    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    type: Literal[ComponentType.role_select] = ComponentType.role_select

    def __init__(self, data: RoleSelectMenuPayload) -> None:
        super().__init__(data)

    def to_dict(self) -> RoleSelectMenuPayload:
        payload: RoleSelectMenuPayload = {"type": self.type.value, **super().to_dict()}

        return payload


class MentionableSelectMenu(SelectMenuBase):
    """Represents a mentionable select menu from the Discord Bot UI Kit.

    A mentionable select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`nextcord.ui.MentionableSelect` not this one.

    .. versionadded:: 2.3

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
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
    """

    __slots__: Tuple[str, ...] = ()
    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    type: Literal[ComponentType.mentionable_select] = ComponentType.mentionable_select

    def __init__(self, data: MentionableSelectMenuPayload) -> None:
        super().__init__(data)

    def to_dict(self) -> MentionableSelectMenuPayload:
        payload: MentionableSelectMenuPayload = {"type": self.type.value, **super().to_dict()}

        return payload


class ChannelSelectMenu(SelectMenuBase):
    """Represents a mentionable select menu from the Discord Bot UI Kit.

    A mentionable select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`nextcord.ui.ChannelSelect` not this one.

    .. versionadded:: 2.3

    Attributes
    ----------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
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
    channel_types: List[:class:`ChannelType`]
        The types of channels that can be selected. If not given, all channel types are allowed.
    """

    __slots__: Tuple[str, ...] = ("channel_types",)
    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    type: Literal[ComponentType.channel_select] = ComponentType.channel_select

    def __init__(self, data: ChannelSelectMenuPayload) -> None:
        super().__init__(data)
        self.channel_types: List[ChannelType] = [
            ChannelType(t) for t in data.get("channel_types", [])
        ]

    def to_dict(self) -> ChannelSelectMenuPayload:
        payload: ChannelSelectMenuPayload = {"type": self.type.value, **super().to_dict()}
        if self.channel_types:
            payload["channel_types"] = [t.value for t in self.channel_types]

        return payload


class SelectOption:
    """Represents a select menu's option.

    These can be created by users.

    .. versionadded:: 2.0

    Attributes
    ----------
    label: :class:`str`
        The label of the option. This is displayed to users.
        Can only be up to 100 characters.
    value: :class:`str`
        The value of the option. This is not displayed to users.
        If not provided when constructed then it defaults to the
        label. Can only be up to 100 characters.
    description: Optional[:class:`str`]
        An additional description of the option, if any.
        Can only be up to 100 characters.
    emoji: Optional[Union[:class:`str`, :class:`Emoji`, :class:`PartialEmoji`]]
        The emoji of the option, if available.
    default: :class:`bool`
        Whether this option is selected by default.
    """

    __slots__: Tuple[str, ...] = (
        "label",
        "value",
        "description",
        "emoji",
        "default",
    )

    def __init__(
        self,
        *,
        label: str,
        value: str = MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        default: bool = False,
    ) -> None:
        self.label: str = label
        self.value: str = label if value is MISSING else value
        self.description: Optional[str] = description

        if emoji is not None:
            if isinstance(emoji, str):
                emoji = PartialEmoji.from_str(emoji)
            elif isinstance(emoji, _EmojiTag):
                emoji = emoji._to_partial()
            else:
                raise TypeError(
                    f"Expected emoji to be str, Emoji, or PartialEmoji not {emoji.__class__}"
                )

        self.emoji: Optional[PartialEmoji] = emoji
        self.default: bool = default

    def __repr__(self) -> str:
        return (
            f"<SelectOption label={self.label!r} value={self.value!r} description={self.description!r} "
            f"emoji={self.emoji!r} default={self.default!r}>"
        )

    def __str__(self) -> str:
        base = f"{self.emoji} {self.label}" if self.emoji else self.label

        if self.description:
            return f"{base}\n{self.description}"
        return base

    @classmethod
    def from_dict(cls, data: SelectOptionPayload) -> SelectOption:
        emoji = PartialEmoji.from_dict(data["emoji"]) if "emoji" in data else None

        return cls(
            label=data["label"],
            value=data["value"],
            description=data.get("description"),
            emoji=emoji,
            default=data.get("default", False),
        )

    def to_dict(self) -> SelectOptionPayload:
        payload: SelectOptionPayload = {
            "label": self.label,
            "value": self.value,
            "default": self.default,
        }

        if self.emoji:
            payload["emoji"] = self.emoji.to_dict()  # type: ignore

        if self.description:
            payload["description"] = self.description

        return payload


class TextInput(Component):
    __slots__: Tuple[str, ...] = (
        "type",
        "style",
        "custom_id",
        "label",
        "min_length",
        "max_length",
        "required",
        "value",
        "placeholder",
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: TextInputComponentPayload) -> None:
        self.type: ComponentType = try_enum(ComponentType, data["type"])
        self.style: TextInputStyle = try_enum(
            TextInputStyle,
            data.get("style", 1),
        )
        self.custom_id: str = data.get("custom_id")
        self.label: str = data.get("label")
        self.min_length: Optional[int] = data.get("min_length")
        self.max_length: Optional[int] = data.get("max_length")
        self.required: Optional[bool] = data.get("required")
        self.value: Optional[str] = data.get("value")
        self.placeholder: Optional[str] = data.get("placeholder")

    def to_dict(self) -> TextInputComponentPayload:
        payload = {
            "type": 4,
            "custom_id": self.custom_id,
            "style": int(self.style.value),
            "label": self.label,
        }

        if self.min_length:
            payload["min_length"] = self.min_length

        if self.max_length:
            payload["max_length"] = self.max_length

        if self.required is not None:
            payload["required"] = self.required

        if self.value:
            payload["value"] = self.value

        if self.placeholder:
            payload["placeholder"] = self.placeholder

        return payload  # type: ignore


class UnfurledMediaItem:
    """Represents an unfurled media item.

    .. versionadded:: 3.12

    Parameters
    ----------
    url: :class:`str`
        The URL of this media item. This can be an arbitrary url or a reference to a local
        file uploaded as an attachment within the message, which can be accessed with the
        ``attachment://<filename>`` format.

    Attributes
    ----------
    url: :class:`str`
        The URL of this media item.
    proxy_url: Optional[:class:`str`]
        The proxy URL. This is a cached version of the :attr:`.url` in the
        case of images.
    height: Optional[:class:`int`]
        The media item's height, in pixels. Only applicable to images and videos.
    width: Optional[:class:`int`]
        The media item's width, in pixels. Only applicable to images and videos.
    content_type: Optional[:class:`str`]
        The media item's media type.
    placeholder: Optional[:class:`str`]
        The media item's placeholder.
    loading_state: Optional[:class:`MediaItemLoadingState`]
        The loading state of this media item.
    attachment_id: Optional[:class:`int`]
        The attachment id this media item points to.
    """

    __slots__: Tuple[str, ...] = (
        "url",
        "proxy_url",
        "height",
        "width",
        "content_type",
        "placeholder",
        "loading_state",
        "attachment_id",
    )

    def __init__(self, url: str) -> None:
        self.url: str = url
        self.proxy_url: Optional[str] = None
        self.height: Optional[int] = None
        self.width: Optional[int] = None
        self.content_type: Optional[str] = None
        self.placeholder: Optional[str] = None
        self.loading_state: Optional[MediaItemLoadingState] = None
        self.attachment_id: Optional[int] = None

    def __repr__(self) -> str:
        return f"<UnfurledMediaItem url={self.url}>"

    @classmethod
    def _from_data(cls, data: UnfurledMediaItemPayload) -> Self:
        self = cls(data["url"])
        self.proxy_url = data.get("proxy_url")
        self.height = data.get("height")
        self.width = data.get("width")
        self.content_type = data.get("content_type")
        self.placeholder = data.get("placeholder")

        loading_state = data.get("loading_state")
        if loading_state is not None:
            self.loading_state = try_enum(MediaItemLoadingState, loading_state)

        attachment_id = data.get("attachment_id")
        if attachment_id is not None:
            self.attachment_id = int(attachment_id)

        return self

    def to_dict(self) -> UnfurledMediaItemPayload:
        return {"url": self.url}


class MediaGalleryItem:
    """Represents a MediaGalleryComponent media item.

    .. versionadded:: 3.12

    Parameters
    ----------
    media: Union[:class:`str`, :class:`File`, :class:`UnfurledMediaItem`]
        The media item data. This can be a string representing a local
        file uploaded as an attachment in the message, which can be accessed
        using the ``attachment://<filename>`` format, or an arbitrary url.
    description: Optional[:class:`str`]
        The description to show within this item. Up to 256 characters.
    spoiler: :class:`bool`
        Whether this item should be flagged as a spoiler.

    Attributes
    ----------
    media: :class:`UnfurledMediaItem`
        This item's media data.
    description: Optional[:class:`str`]
        The description to show within this item.
    spoiler: :class:`bool`
        Whether this item should be flagged as a spoiler.
    """

    __slots__: Tuple[str, ...] = ("_media", "description", "spoiler")

    def __init__(
        self,
        media: Union[str, File, UnfurledMediaItem],
        *,
        description: Optional[str] = None,
        spoiler: bool = False,
    ) -> None:
        self.media = media
        self.description: Optional[str] = description
        self.spoiler: bool = bool(spoiler)

    def __repr__(self) -> str:
        return f"<MediaGalleryItem media={self.media!r}>"

    @property
    def media(self) -> UnfurledMediaItem:
        """:class:`UnfurledMediaItem`: This item's media data."""
        return self._media

    @media.setter
    def media(self, value: Union[str, File, UnfurledMediaItem]) -> None:  # type: ignore
        if isinstance(value, str):
            self._media = UnfurledMediaItem(value)
        elif isinstance(value, UnfurledMediaItem):
            self._media = value
        else:
            from .file import File as FileClass

            if isinstance(value, FileClass):
                self._media = UnfurledMediaItem(f"attachment://{value.filename}")
            else:
                raise TypeError(
                    f"Expected a str, File, or UnfurledMediaItem, not {value.__class__.__name__}"
                )

    @classmethod
    def _from_data(cls, data: MediaGalleryItemPayload) -> Self:
        media = data["media"]
        return cls(
            media=UnfurledMediaItem._from_data(media),
            description=data.get("description"),
            spoiler=data.get("spoiler", False),
        )

    def to_dict(self) -> MediaGalleryItemPayload:
        payload: MediaGalleryItemPayload = {
            "media": self.media.to_dict(),
            "spoiler": self.spoiler,
        }
        if self.description:
            payload["description"] = self.description
        return payload


class TextDisplay(Component):
    """Represents a text display from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a text display is
        :class:`nextcord.ui.TextDisplay` not this one.

    .. versionadded:: 3.12

    Attributes
    ----------
    content: :class:`str`
        The content that this display shows.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__: Tuple[str, ...] = ("content", "id")

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: TextComponentPayload) -> None:
        self.content: str = data["content"]
        self.id: Optional[int] = data.get("id")

    @property
    def type(self) -> Literal[ComponentType.text_display]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.text_display

    def to_dict(self) -> TextComponentPayload:
        payload: TextComponentPayload = {
            "type": self.type.value,
            "content": self.content,
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload


class ThumbnailComponent(Component):
    """Represents a Thumbnail from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a thumbnail is
        :class:`nextcord.ui.Thumbnail` not this one.

    .. versionadded:: 3.12

    Attributes
    ----------
    media: :class:`UnfurledMediaItem`
        The media for this thumbnail.
    description: Optional[:class:`str`]
        The description shown within this thumbnail.
    spoiler: :class:`bool`
        Whether this thumbnail is flagged as a spoiler.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__: Tuple[str, ...] = ("media", "spoiler", "description", "id")

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ThumbnailComponentPayload, state: Optional[ConnectionState]) -> None:
        self.media: UnfurledMediaItem = UnfurledMediaItem._from_data(data["media"])
        self.description: Optional[str] = data.get("description")
        self.spoiler: bool = data.get("spoiler", False)
        self.id: Optional[int] = data.get("id")

    @property
    def type(self) -> Literal[ComponentType.thumbnail]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.thumbnail

    def to_dict(self) -> ThumbnailComponentPayload:
        payload: ThumbnailComponentPayload = {
            "media": self.media.to_dict(),
            "spoiler": self.spoiler,
            "type": self.type.value,
        }
        if self.description is not None:
            payload["description"] = self.description
        if self.id is not None:
            payload["id"] = self.id
        return payload


class MediaGalleryComponent(Component):
    """Represents a Media Gallery component from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a media gallery is
        :class:`nextcord.ui.MediaGallery` not this one.

    .. versionadded:: 3.12

    Attributes
    ----------
    items: List[:class:`MediaGalleryItem`]
        The items this gallery has.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__: Tuple[str, ...] = ("items", "id")

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(
        self, data: MediaGalleryComponentPayload, state: Optional[ConnectionState]
    ) -> None:
        self.items: List[MediaGalleryItem] = [
            MediaGalleryItem._from_data(item) for item in data.get("items", [])
        ]
        self.id: Optional[int] = data.get("id")

    @property
    def type(self) -> Literal[ComponentType.media_gallery]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.media_gallery

    def to_dict(self) -> MediaGalleryComponentPayload:
        payload: MediaGalleryComponentPayload = {
            "type": self.type.value,
            "items": [item.to_dict() for item in self.items],
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload


class FileComponent(Component):
    """Represents a File component from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a file is
        :class:`nextcord.ui.File` not this one.

    .. versionadded:: 3.12

    Attributes
    ----------
    media: :class:`UnfurledMediaItem`
        The unfurled attachment contents of the file.
    spoiler: :class:`bool`
        Whether this file is flagged as a spoiler.
    id: Optional[:class:`int`]
        The ID of this component.
    name: Optional[:class:`str`]
        The displayed file name.
    size: Optional[:class:`int`]
        The file size in MiB.
    """

    __slots__: Tuple[str, ...] = ("media", "spoiler", "id", "name", "size")

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: FileComponentPayload, state: Optional[ConnectionState]) -> None:
        self.media: UnfurledMediaItem = UnfurledMediaItem._from_data(data["file"])
        self.spoiler: bool = data.get("spoiler", False)
        self.id: Optional[int] = data.get("id")
        self.name: Optional[str] = data.get("name")
        self.size: Optional[int] = data.get("size")

    @property
    def type(self) -> Literal[ComponentType.file]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.file

    def to_dict(self) -> FileComponentPayload:
        payload: FileComponentPayload = {
            "type": self.type.value,
            "file": self.media.to_dict(),
            "spoiler": self.spoiler,
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload


class SeparatorComponent(Component):
    """Represents a Separator from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a separator is
        :class:`nextcord.ui.Separator` not this one.

    .. versionadded:: 3.12

    Attributes
    ----------
    spacing: :class:`SeparatorSpacing`
        The spacing size of the separator.
    visible: :class:`bool`
        Whether this separator is visible and shows a divider.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__: Tuple[str, ...] = ("spacing", "visible", "id")

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: SeparatorComponentPayload) -> None:
        self.spacing: SeparatorSpacing = try_enum(SeparatorSpacing, data.get("spacing", 1))
        self.visible: bool = data.get("divider", True)
        self.id: Optional[int] = data.get("id")

    @property
    def type(self) -> Literal[ComponentType.separator]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.separator

    def to_dict(self) -> SeparatorComponentPayload:
        payload: SeparatorComponentPayload = {
            "type": self.type.value,
            "divider": self.visible,
            "spacing": self.spacing.value,
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload


class SectionComponent(Component):
    """Represents a section from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a section is
        :class:`nextcord.ui.Section` not this one.

    .. versionadded:: 3.12

    Attributes
    ----------
    children: List[:class:`TextDisplay`]
        The components on this section.
    accessory: :class:`Component`
        The section accessory.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__: Tuple[str, ...] = ("children", "accessory", "id")

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: SectionComponentPayload, state: Optional[ConnectionState]) -> None:
        self.children: List[TextDisplay] = []
        self.id: Optional[int] = data.get("id")

        for component_data in data.get("components", []):
            component = _component_factory(component_data, state)
            if component is not None and isinstance(component, TextDisplay):
                self.children.append(component)

        accessory_data = data.get("accessory")
        if accessory_data:
            self.accessory: Optional[Component] = _component_factory(accessory_data, state)
        else:
            self.accessory = None

    @property
    def type(self) -> Literal[ComponentType.section]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.section

    def to_dict(self) -> SectionComponentPayload:
        payload: SectionComponentPayload = {
            "type": self.type.value,
            "components": [c.to_dict() for c in self.children],
            "accessory": self.accessory.to_dict() if self.accessory else {},  # type: ignore
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload


class Container(Component):
    """Represents a Container from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type for creating a container is
        :class:`nextcord.ui.Container` not this one.

    .. versionadded:: 3.12

    Attributes
    ----------
    children: List[:class:`Component`]
        This container's children.
    spoiler: :class:`bool`
        Whether this container is flagged as a spoiler.
    id: Optional[:class:`int`]
        The ID of this component.
    accent_colour: Optional[:class:`Colour`]
        The container's accent colour.
    """

    __slots__: Tuple[str, ...] = ("children", "id", "spoiler", "_colour")

    __repr_info__: ClassVar[Tuple[str, ...]] = ("children", "id", "spoiler", "accent_colour")

    def __init__(self, data: ContainerComponentPayload, state: Optional[ConnectionState]) -> None:
        self.children: List[Component] = []
        self.id: Optional[int] = data.get("id")

        for child in data["components"]:
            comp = _component_factory(child, state)

            if comp:
                self.children.append(comp)

        self.spoiler: bool = data.get("spoiler", False)

        colour = data.get("accent_color")
        self._colour: Optional[Colour] = None
        if colour is not None:
            from .colour import Colour

            self._colour = Colour(colour)

    @property
    def accent_colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: The container's accent colour."""
        return self._colour

    accent_color = accent_colour

    @property
    def type(self) -> Literal[ComponentType.container]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.container

    def to_dict(self) -> ContainerComponentPayload:
        payload: ContainerComponentPayload = {
            "type": self.type.value,
            "spoiler": self.spoiler,
            "components": [c.to_dict() for c in self.children],
        }
        if self.id is not None:
            payload["id"] = self.id
        if self._colour:
            payload["accent_color"] = self._colour.value
        return payload


class LabelComponent(Component):
    """Represents a label component from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a label is
        :class:`nextcord.ui.Label` not this one.

    .. versionadded:: 3.12

    Attributes
    ----------
    label: :class:`str`
        The label text to display.
    description: Optional[:class:`str`]
        The description text to display below the label.
    component: :class:`Component`
        The component that this label is associated with.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__: Tuple[str, ...] = ("label", "description", "component", "id")

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: LabelComponentPayload, state: Optional[ConnectionState]) -> None:
        self.label: str = data["label"]
        self.id: Optional[int] = data.get("id")
        self.description: Optional[str] = data.get("description")
        component_data = data.get("component")
        if component_data:
            self.component: Optional[Component] = _component_factory(component_data, state)
        else:
            self.component = None

    @property
    def type(self) -> Literal[ComponentType.label]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.label

    def to_dict(self) -> LabelComponentPayload:
        payload: LabelComponentPayload = {
            "type": self.type.value,
            "label": self.label,
            "component": self.component.to_dict() if self.component else {},  # type: ignore
        }
        if self.description:
            payload["description"] = self.description
        if self.id is not None:
            payload["id"] = self.id
        return payload


class FileUploadComponent(Component):
    """Represents a file upload component from Discord Bot UI Kit (Modals only).

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a file upload is
        :class:`nextcord.ui.FileUpload` not this one.

    .. versionadded:: 3.12

    Attributes
    ----------
    custom_id: :class:`str`
        The custom ID of the file upload component.
    max_values: :class:`int`
        The maximum number of files that can be uploaded. Between 1 and 10.
    min_values: :class:`int`
        The minimum number of files required. Between 0 and 10.
    required: :class:`bool`
        Whether this component is required.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__: Tuple[str, ...] = ("custom_id", "max_values", "min_values", "required", "id")

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: FileUploadComponentPayload) -> None:
        self.custom_id: str = data["custom_id"]
        self.max_values: int = data.get("max_values", 1)
        self.min_values: int = data.get("min_values", 0)
        self.required: bool = data.get("required", True)
        self.id: Optional[int] = data.get("id")

    @property
    def type(self) -> Literal[ComponentType.file_upload]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.file_upload

    def to_dict(self) -> FileUploadComponentPayload:
        payload: FileUploadComponentPayload = {
            "type": self.type.value,
            "custom_id": self.custom_id,
            "max_values": self.max_values,
            "min_values": self.min_values,
            "required": self.required,
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload


def _component_factory(
    data: ComponentPayload, state: Optional[ConnectionState] = None
) -> Optional[Component]:
    component_type = data["type"]
    if component_type == 1:
        return ActionRow(data)
    if component_type == 2:
        return Button(data)  # type: ignore
    if component_type == 3:
        return SelectMenu(data)  # type: ignore
    if component_type == 4:
        return TextInput(data)  # type: ignore
    if component_type in (5, 6, 7, 8):
        return SelectMenu(data)  # type: ignore
    if component_type == 9:
        return SectionComponent(data, state)  # type: ignore
    if component_type == 10:
        return TextDisplay(data)  # type: ignore
    if component_type == 11:
        return ThumbnailComponent(data, state)  # type: ignore
    if component_type == 12:
        return MediaGalleryComponent(data, state)  # type: ignore
    if component_type == 13:
        return FileComponent(data, state)  # type: ignore
    if component_type == 14:
        return SeparatorComponent(data)  # type: ignore
    if component_type == 17:
        return Container(data, state)  # type: ignore
    if component_type == 18:
        return LabelComponent(data, state)  # type: ignore
    if component_type == 19:
        return FileUploadComponent(data)  # type: ignore
    as_enum = try_enum(ComponentType, component_type)
    return Component._raw_construct(type=as_enum)
