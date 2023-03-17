# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Literal, Optional, TypedDict, Union

from typing_extensions import NotRequired

from .channel import ChannelType
from .components import Component, ComponentType
from .embed import Embed
from .member import Member, MemberWithUser
from .role import Role
from .snowflake import Snowflake
from .user import User

if TYPE_CHECKING:
    from .message import AllowedMentions, Attachment, Message


ApplicationCommandType = Literal[1, 2, 3]


class ApplicationCommand(TypedDict):
    id: Snowflake
    application_id: Snowflake
    name: str
    description: str
    default_member_permissions: str
    version: Snowflake
    type: NotRequired[ApplicationCommandType]
    guild_id: NotRequired[Snowflake]
    options: NotRequired[List[ApplicationCommandOption]]
    default_permission: NotRequired[bool]
    dm_permission: NotRequired[bool]
    nsfw: NotRequired[bool]
    name_localizations: NotRequired[Dict[str, str]]
    description_localizations: NotRequired[Dict[str, str]]


class ApplicationCommandOptionChoice(TypedDict):
    name: str
    value: Union[str, int, float]
    name_localizations: Dict[str, str]


ApplicationCommandOptionType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


class ApplicationCommandOption(TypedDict):
    type: ApplicationCommandOptionType
    name: str
    description: str
    required: NotRequired[bool]
    choices: NotRequired[List[ApplicationCommandOptionChoice]]
    options: NotRequired[List[ApplicationCommandOption]]
    channel_types: NotRequired[List[ChannelType]]
    min_value: NotRequired[Union[int, float]]
    max_value: NotRequired[Union[int, float]]
    min_length: NotRequired[int]
    max_length: NotRequired[int]
    autocomplete: NotRequired[bool]
    name_localizations: NotRequired[Dict[str, str]]
    description_localizations: NotRequired[Dict[str, str]]


ApplicationCommandPermissionType = Literal[1, 2]


class ApplicationCommandPermissions(TypedDict):
    id: Snowflake
    type: ApplicationCommandPermissionType
    permission: bool


class BaseGuildApplicationCommandPermissions(TypedDict):
    permissions: List[ApplicationCommandPermissions]


class PartialGuildApplicationCommandPermissions(BaseGuildApplicationCommandPermissions):
    id: Snowflake


class GuildApplicationCommandPermissions(PartialGuildApplicationCommandPermissions):
    application_id: Snowflake
    guild_id: Snowflake


InteractionType = Literal[1, 2, 3]


class _ApplicationCommandInteractionDataOptionSubcommand(TypedDict):
    type: Literal[1, 2]
    name: str
    options: List[ApplicationCommandInteractionDataOption]


class _ApplicationCommandInteractionDataOptionString(TypedDict):
    type: Literal[3]
    name: str
    value: str


class _ApplicationCommandInteractionDataOptionInteger(TypedDict):
    type: Literal[4]
    name: str
    value: int


class _ApplicationCommandInteractionDataOptionBoolean(TypedDict):
    type: Literal[5]
    name: str
    value: bool


class _ApplicationCommandInteractionDataOptionSnowflake(TypedDict):
    type: Literal[6, 7, 8, 9]
    name: str
    value: Snowflake


class _ApplicationCommandInteractionDataOptionNumber(TypedDict):
    type: Literal[10]
    name: str
    value: float


ApplicationCommandInteractionDataOption = Union[
    _ApplicationCommandInteractionDataOptionString,
    _ApplicationCommandInteractionDataOptionInteger,
    _ApplicationCommandInteractionDataOptionSubcommand,
    _ApplicationCommandInteractionDataOptionBoolean,
    _ApplicationCommandInteractionDataOptionSnowflake,
    _ApplicationCommandInteractionDataOptionNumber,
]


class ApplicationCommandResolvedPartialChannel(TypedDict):
    id: Snowflake
    type: ChannelType
    permissions: str
    name: str


class ApplicationCommandInteractionDataResolved(TypedDict, total=False):
    users: Dict[Snowflake, User]
    members: Dict[Snowflake, Member]
    roles: Dict[Snowflake, Role]
    channels: Dict[Snowflake, ApplicationCommandResolvedPartialChannel]
    attachments: Dict[Snowflake, Attachment]
    messages: dict[Snowflake, Message]


class ApplicationCommandInteractionData(TypedDict):
    id: Snowflake
    name: str
    type: ApplicationCommandType
    options: NotRequired[List[ApplicationCommandInteractionDataOption]]
    resolved: NotRequired[ApplicationCommandInteractionDataResolved]
    target_id: NotRequired[Snowflake]


class ComponentInteractionResolved(TypedDict, total=False):
    users: Dict[Snowflake, User]
    members: Dict[Snowflake, MemberWithUser]
    roles: Dict[Snowflake, Role]
    channels: Dict[Snowflake, ApplicationCommandResolvedPartialChannel]


class ComponentInteractionData(TypedDict):
    custom_id: str
    component_type: ComponentType
    values: NotRequired[List[str]]
    value: NotRequired[str]
    resolved: NotRequired[ComponentInteractionResolved]


class ModalSubmitActionRowInteractionData(TypedDict):
    type: Literal[1]
    components: List[ComponentInteractionData]


ModalSubmitComponentInteractionData = Union[
    ModalSubmitActionRowInteractionData,
    ComponentInteractionData,
]


class ModalSubmitInteractionData(TypedDict):
    custom_id: str
    components: List[ModalSubmitComponentInteractionData]


InteractionData = Union[
    ApplicationCommandInteractionData, ComponentInteractionData, ModalSubmitInteractionData
]


class Interaction(TypedDict):
    id: Snowflake
    application_id: Snowflake
    type: InteractionType
    token: str
    version: int
    data: NotRequired[InteractionData]
    guild_id: NotRequired[Snowflake]
    channel_id: NotRequired[Snowflake]
    member: NotRequired[Member]
    user: NotRequired[User]
    message: NotRequired[Message]
    locale: NotRequired[str]
    guild_locale: NotRequired[str]
    app_permissions: NotRequired[str]


class InteractionApplicationCommandCallbackData(TypedDict, total=False):
    tts: bool
    content: str
    embeds: List[Embed]
    allowed_mentions: AllowedMentions
    flags: int
    components: List[Component]


InteractionResponseType = Literal[1, 4, 5, 6, 7]


class InteractionResponse(TypedDict):
    type: InteractionResponseType
    data: NotRequired[InteractionApplicationCommandCallbackData]


class MessageInteraction(TypedDict):
    id: Snowflake
    type: InteractionType
    name: str
    user: User
    member: NotRequired[Member]


class EditApplicationCommand(TypedDict):
    name: str
    default_permission: bool
    description: NotRequired[str]
    options: NotRequired[Optional[List[ApplicationCommandOption]]]
    type: NotRequired[ApplicationCommandType]
