from __future__ import annotations
from typing import TYPE_CHECKING, Union, Optional, List, Tuple
from dataclasses import dataclass
# from enum import IntEnum
from .enums import ApplicationCommandType, ApplicationCommandOptionType
from .mixins import Hashable
from . import utils

if TYPE_CHECKING:
    from .state import ConnectionState
    from .guild import Guild
    from .command_client import ApplicationCommand, ApplicationSubcommand


# class ApplicationCommandType(IntEnum):
#     CHAT_INPUT = 1
#     USER = 2
#     MESSAGE = 3


# class ApplicationCommandOptionType(IntEnum):
#     SUB_COMMAND = 1
#     SUB_COMMAND_GROUP = 2
#     STRING = 3
#     INTEGER = 4
#     BOOLEAN = 5
#     USER = 6
#     CHANNEL = 7
#     ROLE = 8
#     MENTIONABLE = 9
#     NUMBER = 10  # A double, AKA floating point, AKA decimal.


__all__ = (
    'ApplicationCommandOptionChoice',
    'ApplicationCommandOption',
    'ApplicationCommandResponse'
)


class ApplicationCommandOptionChoice:
    def __init__(self, payload: Optional[dict] = None):
        if not payload:
            payload = {}
        self.name: str = payload.get('name')
        self.value: Union[str, int, float] = payload.get('value')

    def from_data(self, data: dict):
        self.__init__(data)


class ApplicationCommandOption:
    def __init__(self, payload: Optional[dict] = None):
        if payload:
            self._from_data(payload)

    def _from_data(self, data: dict):
        self.type = ApplicationCommandOptionType(int(data["type"]))
        self.name: str = data['name']
        self.description: str = data['description']
        self.required: Optional[bool] = data.get('required')
        self.choices: List[ApplicationCommandOptionChoice] = self.create_all_choices(data.get('choices', []))
        self.options: List[ApplicationCommandOption] = self.create_all_options(data.get('options', []))

    @staticmethod
    def create_all_choices(data: List[dict]) -> List[ApplicationCommandOptionChoice]:
        return [ApplicationCommandOptionChoice(raw_choice) for raw_choice in data]

    @staticmethod
    def create_all_options(data: List[dict]) -> List[ApplicationCommandOption]:
        return [ApplicationCommandOption(raw_option) for raw_option in data]


class ApplicationCommandResponse(Hashable):

    def __init__(self, state: ConnectionState, payload: dict):
        self._state: ConnectionState = state
        self._from_data(payload)

    def _from_data(self, data: dict):
        self.id: int = int(data['id'])
        self.type: ApplicationCommandType = ApplicationCommandType(int(data['type']))
        self.application_id: int = int(data['application_id'])
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.name: str = data['name']
        self.description: str = data['description']
        self.options = ApplicationCommandOption.create_all_options(data.get('options', []))
        self.default_permission: Optional[bool] = data.get('default_permission', True)

    @property
    def guild(self) -> Optional[Guild]:
        return self._state._get_guild(self.guild_id)

    async def edit(self, *args, **kwargs):
        raise NotImplementedError

    async def delete(self):
        if self.guild_id:
            await self._state.http.delete_guild_command(self.application_id, self.guild_id, self.id)
        else:
            await self._state.http.delete_global_command(self.application_id, self.id)

    async def fetch_permissions(self):
        raise NotImplementedError

    async def edit_permissions(self):
        raise NotImplementedError

    @property
    def signature(self) -> Tuple[str, int, Optional[int]]:
        return self.name, self.type.value, self.guild_id


# @dataclass
# class ApplicationCommandOptionSignature:
#     name: str
#     type: int
#     description: str
#     required: Optional[bool] = None
#     options: Tuple[ApplicationCommandOptionSignature] = None
#
#
# @dataclass
# class ApplicationCommandSignature:
#     name: str
#     type: int
#     guild_id: Optional[int]
#     description: Optional[str] = None
#     default_permission: Optional[bool] = None
#     options: Optional[Tuple[ApplicationCommandOptionSignature]] = None
#
#     @classmethod
#     def from_application_command(cls, application_command: ApplicationCommand):
#         pass
#
#     @classmethod
#     def from_raw_response(cls, raw_response: dict):
#         guild_id = int(guild_id) if (guild_id := raw_response.get("guild_id")) else guild_id
#         options = tuple(_get_raw_recursive_options(option) for option in raw_response.get("options", []))
#         return cls(name=raw_response["name"], type=int(raw_response["type"]), guild_id=guild_id,
#                    description=raw_response["description"], default_permission=raw_response["guild_permission"],
#                    options=options)
#
#     @classmethod
#     def from_response(cls, response: ApplicationCommandResponse):
#         pass
#
#
# # def raw_response_to_signature(raw_response: dict):
# #     return raw_response["name"], int(raw_response["type"]), \
# #            int(guild_id) if (guild_id := raw_response.get("guild_id", None)) else None
# #
# #
# # def raw_response_to_complex_signature(raw_response: dict):
# #     # This MUST maintain parity with nextcord/command_client/ApplicationCommand.get_complex_signature()
# #     signature = raw_response_to_signature(raw_response)
# #     option_signatures = (_get_option_signature(option_sig) for option_sig in raw_response.get("options", tuple()))
# #
# #     pass
#
#
# def _get_command_recursive_options(command: ApplicationSubcommand):
#     # TODO: Look into choices getting added.
#     tuple_options = None
#     if cmd_children := command.children.values():
#         tuple_options = tuple(_get_command_recursive_options(child) for child in cmd_children)
#     elif arg_options := command.arguments.values():
#         tuple_options = tuple()
#
#
# def _get_raw_recursive_options(command_dict: dict) -> ApplicationCommandOptionSignature:
#     # TODO: Look into choices getting added.
#     tuple_options = None
#     if raw_options := command_dict.get("options", None):
#         tuple_options = tuple(_get_raw_recursive_options(option) for option in raw_options)
#     # return int(command_dict["type"]), command_dict["name"], command_dict["description"], \
#     #     command_dict.get("required", None), tuple_options
#     return ApplicationCommandOptionSignature(name=command_dict["name"], type=int(command_dict["type"]),
#                                              description=command_dict["description"],
#                                              required=command_dict.get("required"), options=tuple_options)
#
# #
# # def _get_option_signature(option_dict: dict):
# #
# #     return int(option_dict["type"]), option_dict["name"], option_dict["description"], option_dict.get("required", None)

