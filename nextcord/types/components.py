# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List, Literal, TypedDict, Union

from typing_extensions import NotRequired

from .channel import ChannelType
from .emoji import PartialEmoji

ComponentType = Literal[1, 2, 3, 4]
ButtonStyle = Literal[1, 2, 3, 4, 5]
TextInputStyle = Literal[1, 2]


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


Component = Union[ActionRow, ButtonComponent, SelectMenu, TextInputComponent]
