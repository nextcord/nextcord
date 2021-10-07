from __future__ import annotations
import asyncio

from .interactions import Interaction
from .client import Client
from .application_command import ApplicationCommand as ApplicationCommandResponse
from .application_command import ApplicationCommandOptionType as CommandOptionType
from .application_command import ApplicationCommandType as CommandType
from inspect import signature, Parameter
import logging
from warnings import warn

from typing import Dict, List, Optional, Union, Type, Any, Callable
from .user import User
from .member import Member
from .abc import GuildChannel
from .role import Role
from .state import ConnectionState
from .enums import ChannelType
from .message import Message


_log = logging.getLogger(__name__)


__all__ = (
    'CmdArg',
    'ApplicationCommand',
    'ApplicationSubcommand',
    'CommandArgument',
    'CommandClient',
    'slash_command',
    'user_command',
    'message_command'
)


class InvalidCommandType(Exception):
    pass


class FakeContext:
    def __init__(self, interaction: Interaction):
        self.interaction = interaction
        self.message: Optional[Message] = interaction.message
        self.guild = interaction.guild
        self.channel = interaction.channel
        self.author = interaction.user
        self.me = self.guild.me

    async def reply(self, content: Optional[str] = None, **kwargs: Any):
        return await self.message.reply(content, **kwargs)

    async def send(self, content=None, **kwargs):
        return await self.interaction.response.send_message(content=content, **kwargs)


class CmdArg:
    def __init__(self, name: str = None, description: str = None, required: bool = None, choices: dict = None,
                 default: Any = None, channel_types: List[ChannelType, ...] = None):
        if not choices:
            choices = list()
        self.name: Optional[str] = name
        self.description: Optional[str] = description
        self.required: Optional[bool] = required
        self.choices: Optional[dict] = choices
        self.default: Optional[Any] = default
        self.channel_types: Optional[List[ChannelType, ...]] = channel_types


class CommandArgument(CmdArg):
    """This must set all variables from CmdArg, hence the subclass."""
    def __init__(self, parameter: Parameter):
        super().__init__()
        self.parameter = parameter
        cmd_arg_given = False
        cmd_arg = CmdArg()
        if isinstance(parameter.default, CmdArg):
            cmd_arg = parameter.default
            cmd_arg_given = True
        print(f"CMD arg name: {cmd_arg.name}, Parameter name: {parameter.name}")
        self.functional_name = parameter.name

        # TODO: Cleanup logic for this.
        self.name = cmd_arg.name if cmd_arg.name is not None else parameter.name
        self.description = cmd_arg.description if cmd_arg.description is not None else " "
        self.required = cmd_arg.required if cmd_arg.required is not None else None
        self.choices = cmd_arg.choices if cmd_arg.choices is not None else dict()
        if not cmd_arg_given and parameter.default is not parameter.empty:
            self.default = parameter.default
        else:
            self.default = cmd_arg.default
        if self.default is None and cmd_arg.required in (None, True):
            self.required = True
        self.channel_types = cmd_arg.channel_types if cmd_arg.channel_types is not None else list()
        self.type: CommandOptionType = self.get_type(parameter.annotation)
        self.verify()

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

    def verify(self):
        """This should run through CmdArg variables and raise errors when conflicting data is given."""
        if self.channel_types and self.type is not CommandOptionType.CHANNEL:
            raise ValueError("channel_types can only be given when the var is typed as nextcord.abc.GuildChannel")

    def handle_argument(self, state: ConnectionState, argument: Any, interaction: Interaction) -> Any:
        if self.type is CommandOptionType.CHANNEL:
            return state.get_channel(int(argument))
        elif self.type is CommandOptionType.USER:
            return interaction.guild.get_member(int(argument))
        elif self.type is CommandOptionType.ROLE:
            return interaction.guild.get_role(int(argument))
        elif self.type is CommandOptionType.INTEGER:
            return int(argument)
        elif self.type is CommandOptionType.NUMBER:
            return float(argument)
        return argument

    @property
    def payload(self) -> dict:
        # self.verify()
        ret = dict()
        ret["type"] = self.type.value
        ret["name"] = self.name
        ret["description"] = self.description
        if self.required is not None:
            ret["required"] = self.required
        if self.choices:
            ret["choices"] = [{"name": key, "value": value} for key, value in self.choices.items()]
        if self.channel_types:
            # TODO: Figure out why pycharm is being a dingus about channel_type.value being an unsolved attribute.
            # noinspection PyUnresolvedReferences
            ret["channel_types"] = [channel_type.value for channel_type in self.channel_types]
        # We don't ask for the payload if we have options, so no point in checking for options.
        return ret


class ApplicationSubcommand:
    def __init__(self, callback: Callable, parent: Optional[Union[ApplicationCommand, ApplicationSubcommand]],
                 cmd_type: Union[CommandType, CommandOptionType], cog_parent: Optional[CommandCog] = None,
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

        self.cog_parent: Optional[CommandCog] = cog_parent
        self._use_fake_context: bool = False
        self.arguments: Dict[str, CommandArgument] = dict()
        self.children: Dict[str, ApplicationSubcommand] = dict()
        self._analyze_content()
        self._analyze_callback()

    def _analyze_content(self):
        if isinstance(self._parent, ApplicationSubcommand) and self.children:
            raise NotImplementedError("A subcommand can't have both subcommand parents and children! Discord does not"
                                      "support this.")
        if isinstance(self._parent, ApplicationCommand):
            if self.children:
                self.type = CommandOptionType.SUB_COMMAND_GROUP
            else:
                self.type = CommandOptionType.SUB_COMMAND
        if self.type is CommandType.USER or self.type is CommandType.MESSAGE:
            self.description = ""
            print(f"ANALYZE CONTENT: {self.description}")
        else:
            print(f"ANALYZE CONTENT: {self.type} {type(self.type)} {CommandType.USER}")
            if not self.description:
                self.description = " "

    def _analyze_callback(self):
        if not self.name:
            self.name = self._callback.__name__
        first_arg = True

        # print(f"ANALYZE CALLBACK: Self Skip: {self_skip} {self.callback}")
        for value in signature(self.callback).parameters.values():
            self_skip = value.name == "self"  # TODO: What kind of hardcoding is this, figure out a better way for self!
            if first_arg:
                # TODO: Is this even worth having?
                # print(f"ANALYZE CALLBACK: First arg name is {value.name} {value.kind}")
                if value.annotation is not value.empty and value.annotation.__name__ == "Context":
                    warn("Please migrate Context to Interaction.", DeprecationWarning, stacklevel=3)
                    self._use_fake_context = True
                elif value.annotation is not value.empty and value.annotation is not Interaction:
                    # print(f"ANALYZE CALLBACK: {value.name} - {value.annotation}")
                    raise TypeError("First argument in an Application Command should be an Interaction.")
                if self_skip:
                    self_skip = False
                else:
                    first_arg = False
            else:
                arg = CommandArgument(value)
                self.arguments[arg.name] = arg

    @property
    def callback(self) -> Callable:
        return self._callback

    async def call(self, state: ConnectionState, interaction: Interaction, option_data: List[Dict[str, Any]]):
        # Invokes the callback or subcommands with kwargs provided by the callback and interaction.
        if self.children:
            print(f"Found children, running that in {self.name} with options {option_data[0].get('options', dict())}")
            await self.children[option_data[0]["name"]].call(state, interaction, option_data[0].get("options", dict()))
        elif self.type in (CommandType.CHAT_INPUT, CommandOptionType.SUB_COMMAND):
            await self.call_invoke_slash(state, interaction, option_data)
        else:
            raise InvalidCommandType
            # kwargs = dict()
            # uncalled_args = self.arguments.copy()
            # for arg_data in option_data:
            #     if arg_data["name"] in uncalled_args:
            #         uncalled_args.pop(arg_data["name"])
            #         kwargs[self.arguments[arg_data["name"]].functional_name] = \
            #             self.arguments[arg_data["name"]].handle_argument(state, arg_data["value"], interaction)
            #     else:
            #         # TODO: Handle this better.
            #         raise NotImplementedError(f"An argument was provided that wasn't already in the function, did you"
            #                                   f"recently change it?\nRegistered Args: {self.arguments}, Discord-sent"
            #                                   f"args: {interaction.data['options']}, broke on {arg_data}")
            # for uncalled_arg in uncalled_args.values():
            #     kwargs[uncalled_arg.functional_name] = uncalled_arg.default
            # await self.invoke(interaction, **kwargs)

    async def call_invoke_slash(self, state: ConnectionState, interaction: Interaction, option_data: List[Dict[str, Any]]):
        print(f"Running call + invoke in command {self.name}")
        kwargs = dict()
        uncalled_args = self.arguments.copy()
        for arg_data in option_data:
            if arg_data["name"] in uncalled_args:
                uncalled_args.pop(arg_data["name"])
                kwargs[self.arguments[arg_data["name"]].functional_name] = \
                    self.arguments[arg_data["name"]].handle_argument(state, arg_data["value"], interaction)
            else:
                # TODO: Handle this better.
                raise NotImplementedError(f"An argument was provided that wasn't already in the function, did you"
                                          f"recently change it?\nRegistered Args: {self.arguments}, Discord-sent"
                                          f"args: {interaction.data['options']}, broke on {arg_data}")
        for uncalled_arg in uncalled_args.values():
            kwargs[uncalled_arg.functional_name] = uncalled_arg.default
        await self.invoke_slash(interaction, **kwargs)

    # async def invoke_slash(self, interaction: Interaction, **kwargs):
    #     # Invokes the callback with the kwargs given.
    #     if self._use_fake_context:
    #         await self.callback(FakeContext(interaction), **kwargs)
    #     else:
    #         await self.callback(interaction, **kwargs)

    async def invoke_slash(self, interaction: Interaction, **kwargs):
        # Invokes the callback with the kwargs given.
        if self._use_fake_context:
            interaction = FakeContext(interaction)
        if self.cog_parent:
            await self.callback(self.cog_parent, interaction, **kwargs)
        else:
            await self.callback(interaction, **kwargs)

    def error(self, coro):
        print("APPLICATION SUBCOMMAND ERROR: This isn't actually implemented yet.")
        # TODO: ^
        return coro

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
            result = ApplicationSubcommand(func, self, CommandOptionType.SUB_COMMAND, **migrate_kwargs(kwargs))
            self.children[result.name] = result
            return result
        return decorator

    def group(self, **kwargs):
        warn("This function will be removed for application commands.", DeprecationWarning, stacklevel=2)
        return self.subcommand(**kwargs)

    def command(self, **kwargs):
        warn("This function will be removed for application commands.", DeprecationWarning, stacklevel=2)
        return self.subcommand(**kwargs)


class ApplicationCommand(ApplicationSubcommand):
    def __init__(self, callback: Callable, cmd_type: CommandType,
                 name: str = "", description: str = "", guild_ids: List[int] = None,
                 default_permission: Optional[bool] = None):
        super().__init__(callback=callback, parent=None, cmd_type=cmd_type, name=name, description=description,
                         guild_ids=None)
        self._state: Optional[ConnectionState] = None
        # TODO: I thought there was a way around doing this, but *sigh*.

        if guild_ids is None:
            guild_ids = list()
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("Callback must be a coroutine.")

        self.default_permission: Optional[bool] = default_permission
        self.guild_ids: List[int] = guild_ids
        self.type = cmd_type
        # TODO: If it's a guild command, we can have multiple IDs. Address that.
        self.id: Optional[int] = None

    def parse_response(self, response: ApplicationCommandResponse):
        print(self.id)
        # TODO: Grab state and have access to get_guild stuff for get_member and get_message for user/message commands.
        self.id = response.id
        self._state = response._state

    # async def invoke(self, interaction: Interaction, **kwargs):
    #     if self.cog_parent:  # TODO: *SIGH*.
    #         await self.callback(self.cog_parent, interaction, **kwargs)
    #     else:
    #         await super().invoke(interaction, **kwargs)

    async def call(self, state: ConnectionState, interaction: Interaction, option_data: List[Dict[str, Any]]):
        try:
            await super().call(state, interaction, option_data)
        except InvalidCommandType:
            await self.invoke_slash(interaction)
            # if self.type is CommandType.MESSAGE:
            #     message = state._get_message(int(interaction.data["target_id"]))
            #     await self.invoke_message(interaction, message)
            # elif self.type is CommandType.USER:
            #     member = interaction.guild.get_member(int(interaction.data["target_id"]))
            #     await self.invoke_user(interaction, member)
            # else:
            #     raise InvalidCommandType

    # async def invoke_slash(self, interaction: Interaction, **kwargs):
    #     # Invokes the callback with the kwargs given.
    #     if self._use_fake_context:
    #         interaction = FakeContext(interaction)
    #     if self.cog_parent:
    #         await self.callback(self.cog_parent, interaction, **kwargs)
    #     else:
    #         await super().invoke_slash(interaction, **kwargs)

    async def invoke_message(self, interaction: Interaction, message: Message, **kwargs):
        if self.cog_parent:
            await self.callback(self.cog_parent, interaction, message, **kwargs)
        else:
            await self.callback(interaction, message, **kwargs)

    async def invoke_user(self, interaction: Interaction, member: Member, **kwargs):
        if self.cog_parent:
            await self.callback(self.cog_parent, interaction, member, **kwargs)
        else:
            await self.callback(interaction, member, **kwargs)

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


# class CommandCogMeta(type):
#     def __new__(mcs, name, bases, namespace, **kwargs):
#         new_cls = super(CommandCogMeta, mcs).__new__(mcs, name, bases, namespace, **kwargs)


class CommandCog:
    # TODO: I get it's a terrible name, I just don't want it to duplicate current Cog right now.
    # __cog_name__: str
    # __cog_settings__: Dict[str, Any]
    __cog_application_commands__: Dict[int, ApplicationCommand]
    # __cog_listeners__: List[Tuple[str, str]]
    __cog_to_register__: List[ApplicationCommand]
    # __cog_commands__: Dict[int, ApplicationCommand]

    # def __new__(cls, *args, **kwargs):
    #     # name, bases, attrs = args
    #     listeners = {}
    #     commands = []
    #
    #     # for elem, value in cls.__dict__.items():
    #     #     print(f"COG: {elem}.{value}")
    #     #     if isinstance(value, ApplicationCommand):
    #     #         print(f"COG: ADDING COMMAND!")
    #     #         if isinstance(value, staticmethod):
    #     #             raise TypeError(f"Command {cls.__name__}.{elem} can not be a staticmethod.")
    #     #         commands.append(value)
    #     #     elif inspect.iscoroutinefunction(value):
    #     #         listeners[elem] = value
    #     # new_cls = super(cls, CommandCog).__new__(cls, *args, **kwargs)
    #     new_cls = super(CommandCog, cls).__new__(cls)
    #     for base in reversed(new_cls.__class__.__mro__):
    #         print(f"COG: {base}")
    #         for elem, value in base.__dict__.items():
    #             print(f"COG:   {elem}.{value}")
    #             is_static_method = isinstance(value, staticmethod)
    #             if is_static_method:
    #                 value = value.__func__
    #             if isinstance(value, ApplicationCommand):
    #                 print(f"COG:     ADDING COMMAND {value.name}")
    #                 if isinstance(value, staticmethod):
    #                     raise TypeError(f"Command {cls.__name__}.{elem} can not be a staticmethod.")
    #                 commands.append(value)
    #
    #     # new_cls.__cog_to_register__ = commands
    #     print(f"TO REG: {commands}")
    #     new_cls._to_register = commands
    #     print(f"TO REG: {new_cls._to_register}")
    #     return new_cls

    def __new__(cls, *args, **kwargs):
        # new_cls = super().__new__(cls)
        # new_cls._listeners: List[Tuple[str, str]] = list()  # TODO: Make this function.
        # new_cls._to_register: List[ApplicationCommand] = list()
        # new_cls._commands: Dict[int, ApplicationCommand] = dict()
        # new_cls._read_methods()
        # return new_cls
        new_cls = super(CommandCog, cls).__new__(cls)
        new_cls._read_methods()
        return new_cls




    # def __init__(self, *args):
    #     self._listeners: List[Tuple[str, str]] = list()  # TODO: Make this function.
    #     self._to_register: List[ApplicationCommand] = list()
    #     self._commands: Dict[int, ApplicationCommand] = dict()
    #     self._read_methods()
    #     # print(f"TO REGISTER: {self.to_register}")

    def _read_methods(self):
        # for elem, value in self.__dict__.items():
        #     is_static_method = isinstance(value, staticmethod)
        #     if is_static_method:
        #         value = value.__func__
        #     print(f"READ METHODS: {self.__dict__}")
        #     print(f"READ METHODS: {type(value)}")
        #     if isinstance(value, ApplicationCommand):
        #         if is_static_method:
        #             raise TypeError(f"Command {self.__name__}.{elem} can not be a staticmethod.")
        #         self._to_register.append(value)
            # elif inspect.iscoroutinefunction(value):
            #     self._listeners[elem] = value
        # new_cls = super(CommandCog, cls).__new__(cls)
        self.__cog_to_register__ = list()
        for base in reversed(self.__class__.__mro__):
            print(f"COG: {base}")
            for elem, value in base.__dict__.items():
                # print(f"COG:   {elem}.{value}")
                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__
                if isinstance(value, ApplicationCommand):
                    print(f"COG:     ADDING COMMAND {value.name}")
                    if isinstance(value, staticmethod):
                        raise TypeError(f"Command {self.__name__}.{elem} can not be a staticmethod.")
                    value.cog_parent = self
                    self.__cog_to_register__.append(value)
                elif isinstance(value, ApplicationSubcommand):
                    value.cog_parent = self

    # @property
    # def to_register(self) -> Dict[str, ApplicationCommand]:
    #     return {cmd.name: cmd for cmd in self._to_register}

    @property
    def to_register(self) -> List[ApplicationCommand]:
        print(f"TO REGISTER: {self.__cog_to_register__}")
        return self.__cog_to_register__


class CommandClient(Client):
    def __init__(self, register_commands_on_startup: bool = True,
                 delete_unknown_commands: bool = True,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._register_commands_on_startup: bool = register_commands_on_startup
        self._delete_unknown_commands: bool = delete_unknown_commands

        self._registered_commands: Dict[int, ApplicationCommand] = dict()
        self._commands_to_register: List[ApplicationCommand] = list()
        self._cogs: List[CommandCog] = list()  # TODO: Turn this into dict with names.

    async def on_connect(self):
        if self._register_commands_on_startup:
            await self.register_application_commands()
            await self.register_cog_commands()
        await super().on_connect()
        if self._delete_unknown_commands:
            await self.delete_unknown_commands()
        print(f"ON CONNECT: Registered commmand count: {len(self._connection.application_commands)}")

    async def register_application_commands(self):
        print(f"TO BE REGISTERED: {self._commands_to_register}")
        for cmd in self._commands_to_register:
            await self.register_command(cmd)
        self._commands_to_register.clear()

    async def register_cog_commands(self):
        print("REG COG CMD: Called.")
        for cog in self._cogs:
            print("REG COG CMD:   Cog.")
            if to_register := cog.to_register:
                for cmd in to_register:
                    print(f"REG COG CMD:     {cmd.name}")
                    await self.register_command(cmd)

    async def register_command(self, command: ApplicationCommand):
        # TODO: Worth having a guild override? Seems unnecessary, but some people want to do seemingly
        #  unnecessary things.
        if command.guild_ids:
            for payload in command.payload:
                # TODO: Just realized that the same command object is getting linked to each app_cmd ID. Look into
                #  downsides of doing so.
                response_json = await self.http.upsert_guild_command(self.application_id, payload["guild_id"], payload)
                command.parse_response(ApplicationCommandResponse(self._connection, response_json))
                self._registered_commands[command.id] = command
        else:
            response_json = await self.http.upsert_global_command(self.application_id, command.payload)
            command.parse_response(ApplicationCommandResponse(self._connection, response_json))
            self._registered_commands[command.id] = command

    async def delete_unknown_commands(self):
        to_remove = list()
        for app_response in self._connection.application_commands:
            if app_response.id not in self._registered_commands:
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
        self._commands_to_register.append(application_command)

    def add_cog(self, cog: CommandCog):
        self._cogs.append(cog)

    def user_command(self, *args, **kwargs):
        def decorator(func: Callable):
            result = user_command(*args, **kwargs)(func)
            self.add_application_command_request(result)
            return result
        return decorator

    def message_command(self, *args, **kwargs):
        def decorator(func: Callable):
            result = message_command(*args, **kwargs)(func)
            self.add_application_command_request(result)
            return result
        return decorator

    def slash_command(self, *args, **kwargs):
        def decorator(func: Callable):
            result = slash_command(*args, **kwargs)(func)
            self.add_application_command_request(result)
            return result
        return decorator

    async def on_application_command(self, interaction: Interaction):
        print(f"ON APPLICATION COMMAND: {interaction.data}")
        print(f"ON APPLICATION COMMAND: \n{interaction.data}\n{self._registered_commands}")
        # TODO: Well ain't this a bit hardcoded, huh?
        if interaction.data['type'] in (1, 2, 3) and \
                (app_cmd := self._registered_commands.get(int(interaction.data["id"]))):
            print("Found viable command, calling it!")
            await app_cmd.call(self._connection, interaction, interaction.data.get("options", dict()))


def migrate_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    if "brief" in kwargs:
        kwargs["description"] = kwargs["brief"]
        kwargs.pop("brief")
    if "invoke_without_command" in kwargs:
        kwargs.pop("invoke_without_command")
    if "aliases" in kwargs:
        kwargs.pop("aliases")  # TODO: Make this reality?
    return kwargs


def slash_command(*args, **kwargs):
    def decorator(func: Callable):
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        return ApplicationCommand(func, cmd_type=CommandType.CHAT_INPUT, *args, **migrate_kwargs(kwargs))
    return decorator


# def slash_command(*args, **kwargs):
#     def decorator(func: Callable):
#         @wraps(func)
#         async def wrapper(self, *other_args, **other_kwargs):
#             return func(self, *other_args, **other_kwargs)
#         return ApplicationCommand(wrapper, cmd_type=CommandType.CHAT_INPUT, *args, **kwargs)
#
#     return decorator


def message_command(*args, **kwargs):
    def decorator(func: Callable):
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        return ApplicationCommand(func, cmd_type=CommandType.MESSAGE, *args, **migrate_kwargs(kwargs))
    return decorator


def user_command(*args, **kwargs):
    def decorator(func: Callable):
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        return ApplicationCommand(func, cmd_type=CommandType.USER, *args, **migrate_kwargs(kwargs))
    return decorator


def options_to_args(options: List[Dict[str, Any]]) -> Dict[str, Any]:
    ret = dict()
    for option in options:
        ret[option["name"]] = option["value"]
    return ret
