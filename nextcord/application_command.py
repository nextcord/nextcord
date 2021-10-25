from __future__ import annotations
from typing import TYPE_CHECKING, Union, Optional, List, Tuple
# from enum import IntEnum
from .enums import ApplicationCommandType, ApplicationCommandOptionType
from .mixins import Hashable
from . import utils

if TYPE_CHECKING:
    from .state import ConnectionState
    from .guild import Guild


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
