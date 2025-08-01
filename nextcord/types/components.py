# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List, Literal, TypedDict, Union

from typing_extensions import NotRequired

from .channel import ChannelType
from .emoji import PartialEmoji
from .snowflake import Snowflake

ComponentType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17]
ButtonStyle = Literal[1, 2, 3, 4, 5, 6]
TextInputStyle = Literal[1, 2]


class BaseComponent(TypedDict):
    type: ComponentType
    id: int


class ActionRow(BaseComponent):
    type: Literal[1]
    components: List[Component]


class ButtonComponent(BaseComponent):
    type: Literal[2]
    style: ButtonStyle
    custom_id: NotRequired[str]
    url: NotRequired[str]
    disabled: NotRequired[bool]
    emoji: NotRequired[PartialEmoji]
    label: NotRequired[str]
    sku_id: NotRequired[Snowflake]


class SelectOption(TypedDict):
    label: str
    value: str
    default: NotRequired[bool]
    description: NotRequired[str]
    emoji: NotRequired[PartialEmoji]


class SelectDefaultValue(TypedDict):
    id: Snowflake
    type: Literal["user", "role", "channel"]


class SelectMenuBase(BaseComponent):
    custom_id: str
    placeholder: NotRequired[str]
    default_values: NotRequired[list[SelectDefaultValue]]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]


class SelectMenu(SelectMenuBase):
    type: Literal[3]
    options: List[SelectOption]


class UserSelectMenu(SelectMenuBase):
    type: Literal[5]


class RoleSelectMenu(SelectMenuBase):
    type: Literal[6]


class MentionableSelectMenu(SelectMenuBase):
    type: Literal[7]


class ChannelSelectMenu(SelectMenuBase):
    type: Literal[8]
    channel_types: NotRequired[List[ChannelType]]


class TextInputComponent(BaseComponent):
    type: Literal[4]
    custom_id: str
    style: TextInputStyle
    label: str
    min_length: NotRequired[int]
    max_length: NotRequired[int]
    required: NotRequired[bool]
    value: NotRequired[str]
    placeholder: NotRequired[str]


class Section(BaseComponent):
    type: Literal[9]
    components: list[TextDisplay]
    accessory: Component


class TextDisplay(BaseComponent):
    type: Literal[10]
    content: str


class UnfurledMedia(TypedDict):
    url: str
    proxy_url: NotRequired[str]
    height: NotRequired[int | None]
    width: NotRequired[int | None]
    content_type: NotRequired[str]
    attachment_id: NotRequired[Snowflake]


class Thumbnail(BaseComponent):
    type: Literal[11]
    media: UnfurledMedia
    description: NotRequired[str]
    spoiler: NotRequired[bool]


class MediaGalleryItem(TypedDict):
    media: UnfurledMedia
    description: NotRequired[str]
    spoiler: NotRequired[bool]


class MediaGallery(BaseComponent):
    type: Literal[12]
    items: list[MediaGalleryItem]


class File(BaseComponent):
    type: Literal[13]
    file: UnfurledMedia
    spoiler: NotRequired[bool]
    name: str  # Sent back as part of the API, ignored when sending.
    size: int  # Sent back as part of the API, ignored when sending.


class Separator(BaseComponent):
    type: Literal[14]
    divider: NotRequired[bool]
    spacing: NotRequired[Literal[1, 2]]


class Container(BaseComponent):
    type: Literal[17]
    components: list[Component]
    accent_color: NotRequired[int | None]
    spoiler: NotRequired[bool]


Component = Union[
    ActionRow,
    ButtonComponent,
    SelectMenu,
    UserSelectMenu,
    RoleSelectMenu,
    MentionableSelectMenu,
    ChannelSelectMenu,
    TextInputComponent,
    Section,
    TextDisplay,
    Thumbnail,
    MediaGallery,
    File,
    Separator,
    Container,
]
