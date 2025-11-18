# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired

from .channel import ChannelType
from .emoji import PartialEmoji
from .snowflake import Snowflake

ComponentType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17, 18, 19]
ButtonStyle = Literal[1, 2, 3, 4, 5]
TextInputStyle = Literal[1, 2]
SeparatorSpacing = Literal[1, 2]
MediaItemLoadingState = Literal[0, 1, 2, 3]


class ActionRow(TypedDict):
    type: Literal[1]
    components: List[Component]


class ButtonComponent(TypedDict):
    type: Literal[2]
    style: ButtonStyle
    custom_id: NotRequired[str]
    url: NotRequired[str]
    disabled: NotRequired[bool]
    emoji: NotRequired[PartialEmoji]
    label: NotRequired[str]


class SelectOption(TypedDict):
    label: str
    value: str
    default: bool
    description: NotRequired[str]
    emoji: NotRequired[PartialEmoji]


class SelectMenuBase(TypedDict):
    custom_id: str
    placeholder: NotRequired[str]
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


class TextInputComponent(TypedDict):
    type: Literal[4]
    custom_id: str
    style: TextInputStyle
    label: str
    min_length: NotRequired[int]
    max_length: NotRequired[int]
    required: NotRequired[bool]
    value: NotRequired[str]
    placeholder: NotRequired[str]


class UnfurledMediaItem(TypedDict):
    url: str
    proxy_url: NotRequired[str]
    height: NotRequired[int]
    width: NotRequired[int]
    content_type: NotRequired[str]
    placeholder: NotRequired[str]
    loading_state: NotRequired[MediaItemLoadingState]
    attachment_id: NotRequired[Snowflake]


class MediaGalleryItem(TypedDict):
    media: UnfurledMediaItem
    description: NotRequired[str]
    spoiler: NotRequired[bool]


class TextComponent(TypedDict):
    type: Literal[10]
    content: str
    id: NotRequired[int]


class ThumbnailComponent(TypedDict):
    type: Literal[11]
    media: UnfurledMediaItem
    description: NotRequired[str]
    spoiler: NotRequired[bool]
    id: NotRequired[int]


class MediaGalleryComponent(TypedDict):
    type: Literal[12]
    items: List[MediaGalleryItem]
    id: NotRequired[int]


class FileComponent(TypedDict):
    type: Literal[13]
    file: UnfurledMediaItem
    spoiler: NotRequired[bool]
    id: NotRequired[int]
    name: NotRequired[str]
    size: NotRequired[int]


class SeparatorComponent(TypedDict):
    type: Literal[14]
    divider: NotRequired[bool]
    spacing: NotRequired[SeparatorSpacing]
    id: NotRequired[int]


class SectionComponent(TypedDict):
    type: Literal[9]
    components: List[TextComponent]
    accessory: Component
    id: NotRequired[int]


class ContainerComponent(TypedDict):
    type: Literal[17]
    components: List[Component]
    accent_color: NotRequired[Optional[int]]
    spoiler: NotRequired[bool]
    id: NotRequired[int]


class LabelComponent(TypedDict):
    type: Literal[18]
    label: str
    component: Component
    description: NotRequired[str]
    id: NotRequired[int]


class FileUploadComponent(TypedDict):
    type: Literal[19]
    custom_id: str
    max_values: NotRequired[int]
    min_values: NotRequired[int]
    required: NotRequired[bool]
    id: NotRequired[int]


Component = Union[
    ActionRow,
    ButtonComponent,
    SelectMenu,
    UserSelectMenu,
    RoleSelectMenu,
    MentionableSelectMenu,
    ChannelSelectMenu,
    TextInputComponent,
    TextComponent,
    ThumbnailComponent,
    MediaGalleryComponent,
    FileComponent,
    SeparatorComponent,
    SectionComponent,
    ContainerComponent,
    LabelComponent,
    FileUploadComponent,
]
ComponentBase = Component
