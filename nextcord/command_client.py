from __future__ import annotations
import asyncio
from .interactions import Interaction
from typing import Dict, List, Optional, Union, Type, Any, Callable
from .client import Client
from .application_command import ApplicationCommand as ApplicationCommandResponse
from .application_command import ApplicationCommandOptionType as CommandOptionType
from .application_command import ApplicationCommandType as CommandType
from inspect import signature, Parameter
import logging
from warnings import warn

from .user import User
from .member import Member
from .abc import GuildChannel
from .role import Role


_log = logging.getLogger(__name__)


__all__ = (
    'CmdArg',
    'ApplicationCommand',
    'ApplicationSubcommand',
    'CommandArgument',
    'CommandClient',
    'slash_command'
)


class CmdArg:
    def __init__(self, name: str = None, description: str = None, required: bool = None, choices: dict = None,
                 default: Any = None):
        if not choices:
            choices = list()
        self.name: Optional[str] = name
        self.description: Optional[str] = description
        self.required: Optional[bool] = required
        self.choices: Optional[dict] = choices
        self.default: Optional[Any] = default


class CommandArgument(CmdArg):
    def __init__(self, parameter: Parameter):
        super().__init__()
        self.parameter = parameter
        cmd_arg_given = False
        cmd_arg = CmdArg()
        if isinstance(parameter.default, CmdArg):
            cmd_arg = parameter.default
            cmd_arg_given = True
        print(f"CMD arg name: {cmd_arg.name}, Parameter name: {parameter.name}")
        # TODO: Cleanup logic for this.
        self.name = cmd_arg.name if cmd_arg.name is not None else parameter.name
        self.functional_name = parameter.name
        self.description = cmd_arg.description if cmd_arg.description is not None else " "
        self.required = cmd_arg.required if cmd_arg.required is not None else None
        self.choices = cmd_arg.choices if cmd_arg.choices is not None else dict()
        if not cmd_arg_given and parameter.default is not parameter.empty:
            self.default = parameter.default
        else:
            self.default = cmd_arg.default
        if self.default is None and cmd_arg.required in (None, True):
            self.required = True
        self.type: CommandOptionType = self.get_type(parameter.annotation)

    def get_type(self, typing: Type) -> CommandOptionType:
        if typing is self.parameter.empty:
            return CommandOptionType.STRING
        elif typing is str:
            return CommandOptionType.STRING
        elif typing is int:
            return CommandOptionType.INTEGER
        elif typing is bool:
            return CommandOptionType.BOOLEAN
        elif typing is User or typing is Member:
            return CommandOptionType.USER
        elif typing is GuildChannel:  # TODO: Make this more inclusive.
            return CommandOptionType.CHANNEL
        elif typing is Role:
            return CommandOptionType.ROLE
        # elif isinstance(typing, Mentionable):  # TODO: Is this in the library at all?? Includes Users AND Roles?
        #     return CommandOptionType.MENTIONABLE
        elif typing is float:
            return CommandOptionType.NUMBER
        else:
            raise NotImplementedError(f"Type \"{typing}\" isn't supported.")

    @property
    def payload(self) -> dict:
        ret = dict()
        ret["type"] = self.type.value
        ret["name"] = self.name
        ret["description"] = self.description
        if self.required is not None:
            ret["required"] = self.required
        if self.choices:
            ret["choices"] = [{"name": key, "value": value} for key, value in self.choices.items()]
        # We don't ask for the payload if we have options, so no point in checking for options.
        return ret


class ApplicationSubcommand:
    def __init__(self, callback: Callable, parent: Optional[Union[ApplicationCommand, ApplicationSubcommand]],
                 cmd_type: Union[CommandType, CommandOptionType],
                 name: str = "", description: str = "", required: Optional[bool] = None, guild_ids: List[int] = None,
                 choices: Dict[str, Any] = None):
        if guild_ids is None:
            guild_ids = list()
        else:
            # TODO: Per-guild subcommands.
            raise NotImplementedError("Per-guild subcommands are not yet handled properly. Ask Alento about them!")
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("Callback must be a coroutine.")

        self._parent: Union[ApplicationCommand, ApplicationSubcommand] = parent
        self._callback: Callable = callback

        self.type: Union[CommandType, CommandOptionType] = cmd_type
        self.name: str = name
        self.description: str = description
        self.required: Optional[bool] = required
        self.guild_ids: List[int] = guild_ids
        self.choices: Dict[str, Any] = choices

        self.arguments: Dict[str, CommandArgument] = dict()
        self.children: Dict[str, ApplicationSubcommand] = dict()
        self._analyze_content()
        self._analyze_callback()

    def _analyze_content(self):
        if isinstance(self._parent, ApplicationSubcommand) and self.children:
            raise NotImplementedError("A subcommand can't have both subcommand parents and children! Discord does not"
                                      "support this.")
        if isinstance(self._parent, ApplicationCommand) and self.children:
            self.type = CommandOptionType.SUB_COMMAND_GROUP
        else:
            self.type = CommandOptionType.SUB_COMMAND
        if self.type not in (CommandType.USER, CommandType.MESSAGE) and not self.description:
            self.description = " "

    def _analyze_callback(self):
        if not self.name:
            self.name = self._callback.__name__
        first_arg = True
        for value in signature(self.callback).parameters.values():
            if first_arg:
                # TODO: Is this even worth having?
                if value.annotation is not value.empty and value.annotation is not Interaction:
                    raise TypeError("First argument in an Application Command should be an Interaction.")
                first_arg = False
            else:
                arg = CommandArgument(value)
                self.arguments[arg.name] = arg

    @property
    def callback(self) -> Callable:
        return self._callback

    async def call(self, interaction: Interaction, option_data: List[Dict[str, Any]]):
        # Invokes the callback or subcommands with kwargs provided by the callback and interaction.
        if self.children:
            print(f"Found children, running that in {self.name} with options {option_data[0].get('options', dict())}")
            await self.children[option_data[0]["name"]].call(interaction, option_data[0].get("options", dict()))
        else:
            print(f"Running call + invoke in command {self.name}")
            kwargs = dict()
            uncalled_args = self.arguments.copy()
            for arg_data in option_data:
                if arg_data["name"] in uncalled_args:
                    uncalled_args.pop(arg_data["name"])
                    kwargs[self.arguments[arg_data["name"]].functional_name] = arg_data["value"]
                else:
                    # TODO: Handle this better.
                    raise NotImplementedError(f"An argument was provided that wasn't already in the function, did you"
                                              f"recently change it?\nRegistered Args: {self.arguments}, Discord-sent"
                                              f"args: {interaction.data['options']}, broke on {arg_data}")
            for uncalled_arg in uncalled_args.values():
                kwargs[uncalled_arg.functional_name] = uncalled_arg.default
            await self.invoke(interaction, **kwargs)

    async def invoke(self, interaction: Interaction, **kwargs):
        # Invokes the callback with the kwargs given.
        await self._callback(interaction, **kwargs)

    @property
    def payload(self) -> dict:
        ret = dict()
        ret["type"] = self.type.value
        ret["name"] = self.name
        ret["description"] = self.description
        if self.required is not None:
            ret["required"] = self.required
        if self.choices:
            ret["choices"] = [{key: value} for key, value in self.choices.items()]
        if self.children:
            ret["options"] = [child.payload for child in self.children.values()]
        elif self.arguments:
            ret["options"] = [argument.payload for argument in self.arguments.values()]
        return ret

    def subcommand(self, **kwargs):
        def decorator(func: Callable):
            result = ApplicationSubcommand(func, self, CommandOptionType.SUB_COMMAND, **kwargs)
            self.children[result.name] = result
            return result
        return decorator

    def group(self, **kwargs):
        warn("This function will be removed for application commands.", DeprecationWarning, stacklevel=2)
        return self.subcommand(**kwargs)


class ApplicationCommand(ApplicationSubcommand):
    def __init__(self, callback: Callable, cmd_type: CommandType,
                 name: str = "", description: str = "", guild_ids: List[int] = None,
                 default_permission: Optional[bool] = None):
        super().__init__(callback=callback, parent=None, cmd_type=cmd_type, name=name, description=description,
                         guild_ids=None)
        if guild_ids is None:
            guild_ids = list()
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("Callback must be a coroutine.")

        self.default_permission: Optional[bool] = default_permission
        self.guild_ids: List[int] = guild_ids
        self.type = cmd_type
        self.id: Optional[int] = None

    def parse_response(self, response: ApplicationCommandResponse):
        print(self.id)
        self.id = response.id

    @property
    def payload(self) -> Union[List[Dict[str, ...]], Dict[str, ...]]:
        ret = super().payload
        if self.default_permission is not None:
            ret["default_permission"] = self.default_permission

        if self.guild_ids:
            guild_ret = list()
            for guild_id in self.guild_ids:
                temp = ret.copy()
                temp["guild_id"] = guild_id
                guild_ret.append(temp)
            return guild_ret
        else:
            return ret


class CommandClient(Client):
    def __init__(self, register_commands_on_startup: bool = True,
                 delete_unknown_commands: bool = True,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._register_commands_on_startup: bool = register_commands_on_startup
        self._delete_unknown_commands: bool = delete_unknown_commands
        self._registered_application_commands: Dict[int, ApplicationCommand] = dict()
        self._to_be_registered_commands: List[ApplicationCommand] = list()

    async def on_connect(self):
        if self._register_commands_on_startup:
            await self.register_application_commands()
        await super().on_connect()
        if self._delete_unknown_commands:
            await self.delete_unknown_commands()
        print(f"ON CONNECT: {self._connection.application_commands}")

    async def register_application_commands(self):
        print(f"TO BE REGISTERED: {self._to_be_registered_commands}")
        for not_registered_cmd in self._to_be_registered_commands:
            if not_registered_cmd.guild_ids:
                guild_payloads = not_registered_cmd.payload
                for payload in guild_payloads:
                    response_json = await self.http.upsert_guild_command(self.application_id, payload["guild_id"],
                                                                         payload)
                    not_registered_cmd.parse_response(ApplicationCommandResponse(self._connection, response_json))
                    self._registered_application_commands[not_registered_cmd.id] = not_registered_cmd
                    print(f"REGISTERED COMMAND {not_registered_cmd.name} FOR GUILD {payload['guild_id']}")
            else:
                response_json = await self.http.upsert_global_command(self.application_id, not_registered_cmd.payload)
                not_registered_cmd.parse_response(ApplicationCommandResponse(self._connection, response_json))
                self._registered_application_commands[not_registered_cmd.id] = not_registered_cmd
        self._to_be_registered_commands.clear()

    async def delete_unknown_commands(self):
        to_remove = list()
        for app_response in self._connection.application_commands:
            if app_response.id not in self._registered_application_commands:

                if app_response.guild_id:
                    print(f"Removing command NAME {app_response.name} ID {app_response.id} from "
                          f"GUILD {app_response.guild.name} ID {app_response.guild_id}")
                    await self.http.delete_guild_command(self.application_id, app_response.guild_id, app_response.id)
                else:
                    print(f"Removing command NAME {app_response.name} ID {app_response.id}")
                    await self.http.delete_global_command(self.application_id, app_response.id)
                to_remove.append(app_response.id)
        for app_id in to_remove:
            self._connection._remove_application_command(app_id)

    def add_application_command_request(self, application_command: ApplicationCommand):
        self._to_be_registered_commands.append(application_command)

    def slash_command(self, *args, **kwargs):
        def decorator(func: Callable):
            result = slash_command(*args, **kwargs)(func)
            self.add_application_command_request(result)
            return result
        return decorator

    async def on_application_command(self, interaction: Interaction):
        print(f"ON APPLICATION COMMAND: {interaction.data}")
        print(f"ON APPLICATION COMMAND: \n{interaction.data}\n{self._registered_application_commands}")
        if interaction.data['type'] in (1, 2, 3) and \
                (app_cmd := self._registered_application_commands.get(int(interaction.data["id"]))):
            print("Found viable command, calling it!")
            await app_cmd.call(interaction, interaction.data.get("options", dict()))


def slash_command(*args, **kwargs):
    def decorator(func: Callable):
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        return ApplicationCommand(func, cmd_type=CommandType.CHAT_INPUT, *args, **kwargs)
    return decorator


def options_to_args(options: List[Dict[str, Any]]) -> Dict[str, Any]:
    ret = dict()
    for option in options:
        ret[option["name"]] = option["value"]
    return ret
