from __future__ import annotations
import asyncio

from .interactions import Interaction
from .client import Client
from .enums import ApplicationCommandOptionType as CommandOptionType
from .enums import ApplicationCommandType as CommandType
from .application_command import ApplicationCommandResponse
from inspect import signature, Parameter
import logging

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
    'SlashOption',
    'ApplicationCommand',
    'ApplicationSubcommand',
    'CommandArgument',
    'CommandClient',
    'CommandCog',
    'slash_command',
    'user_command',
    'message_command'
)


class InvalidCommandType(Exception):
    pass


class SlashOption:
    def __init__(self, name: str = None, description: str = None, required: bool = None, choices: dict = None,
                 default: Any = None, channel_types: List[ChannelType, ...] = None):
        if not choices:
            choices = []
        self.name: Optional[str] = name
        self.description: Optional[str] = description
        self.required: Optional[bool] = required
        self.choices: Optional[dict] = choices
        self.default: Optional[Any] = default
        self.channel_types: Optional[List[ChannelType, ...]] = channel_types


class CommandArgument(SlashOption):
    """This must set all variables from CmdArg, hence the subclass."""
    def __init__(self, parameter: Parameter):
        super().__init__()
        self.parameter = parameter
        cmd_arg_given = False
        cmd_arg = SlashOption()
        if isinstance(parameter.default, SlashOption):
            cmd_arg = parameter.default
            cmd_arg_given = True
        print(f"CMD arg name: {cmd_arg.name}, Parameter name: {parameter.name}")
        self.functional_name = parameter.name

        # TODO: Cleanup logic for this.
        self.name = cmd_arg.name if cmd_arg.name is not None else parameter.name
        self.description = cmd_arg.description if cmd_arg.description is not None else " "
        self.required = cmd_arg.required if cmd_arg.required is not None else None
        self.choices = cmd_arg.choices if cmd_arg.choices is not None else {}
        if not cmd_arg_given and parameter.default is not parameter.empty:
            self.default = parameter.default
        else:
            self.default = cmd_arg.default
        if self.default is None and cmd_arg.required in (None, True):
            self.required = True
        self.channel_types = cmd_arg.channel_types if cmd_arg.channel_types is not None else []
        self.type: CommandOptionType = self.get_type(parameter.annotation)
        self.verify()

    def get_type(self, typing: Type) -> CommandOptionType:
        if typing is self.parameter.empty:
            return CommandOptionType.string
        elif typing is str:
            return CommandOptionType.string
        elif typing is int:
            return CommandOptionType.integer
        elif typing is bool:
            return CommandOptionType.boolean
        elif typing is User or typing is Member:
            return CommandOptionType.user
        elif typing is GuildChannel:  # TODO: Make this more inclusive.
            return CommandOptionType.channel
        elif typing is Role:
            return CommandOptionType.role
        # elif isinstance(typing, Mentionable):  # TODO: Is this in the library at all?? Includes Users AND Roles?
        #     return CommandOptionType.MENTIONABLE
        elif typing is float:
            return CommandOptionType.number
        elif typing is Message:  # TODO: Brutally test please.
            return CommandOptionType.integer
        else:
            raise NotImplementedError(f"Type \"{typing}\" isn't supported.")

    def verify(self):
        """This should run through CmdArg variables and raise errors when conflicting data is given."""
        if self.channel_types and self.type is not CommandOptionType.channel:
            raise ValueError("channel_types can only be given when the var is typed as nextcord.abc.GuildChannel")

    def handle_argument(self, state: ConnectionState, argument: Any, interaction: Interaction) -> Any:
        if self.type is CommandOptionType.channel:
            return state.get_channel(int(argument))
        elif self.type is CommandOptionType.user:  # TODO: Brutally test please.
            if interaction.guild:
                return interaction.guild.get_member(int(argument))
            else:
                return state.get_user(int(argument))
        elif self.type is CommandOptionType.role:
            return interaction.guild.get_role(int(argument))
        elif self.type is CommandOptionType.integer:
            return int(argument)
        elif self.type is CommandOptionType.number:
            return float(argument)
        elif self.type is Message:  # TODO: Brutally test please.
            return state._get_message(int(argument))
        return argument

    @property
    def payload(self) -> dict:
        # self.verify()
        # TODO: Figure out why pycharm is being a dingus about self.type.value being an unsolved attribute.
        # noinspection PyUnresolvedReferences
        ret = {"type": self.type.value, "name": self.name, "description": self.description}
        # ret["type"] = self.type.value
        # ret["name"] = self.name
        # ret["description"] = self.description
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
            guild_ids = []
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
        self.arguments: Dict[str, CommandArgument] = {}
        self.children: Dict[str, ApplicationSubcommand] = {}
        self._analyze_content()
        self._analyze_callback()

    def _analyze_content(self):
        if isinstance(self._parent, ApplicationSubcommand) and self.children:
            raise NotImplementedError("A subcommand can't have both subcommand parents and children! Discord does not"
                                      "support this.")
        if isinstance(self._parent, ApplicationCommand):
            if self.children:
                self.type = CommandOptionType.sub_command_group
            else:
                self.type = CommandOptionType.sub_command
        if self.type is CommandType.user or self.type is CommandType.message:
            self.description = ""
            print(f"ANALYZE CONTENT: Description: \"{self.description}\"")
        else:
            print(f"ANALYZE CONTENT: {self.type} {type(self.type)} {CommandType.user}")
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
                if value.annotation is not value.empty and value.annotation is not Interaction:
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
        """
        Calls the callback, gathering and inserting kwargs into the callback as needed.
        This must be able to call itself as subcommands may be subcommand groups, and thus have subcommands of their
        own.

        Parameters
        ----------
        state: :class:`ConnectionState`
            State object used to fetch Guild, Channel, etc from cache.
        interaction: :class:`Interaction`
            Interaction object to pass to callback.
        option_data: :class:`list`
            List of option data dictionaries from interaction data payload.

        Returns
        -------

        """

        if self.children:
            # Discord currently does not allow commands that have subcommands to be ran. Therefore, if a command has
            # children, a subcommand must be being called.
            print(f"Found children, running that in {self.name} with options {option_data[0].get('options', {})}")
            await self.children[option_data[0]["name"]].call(state, interaction, option_data[0].get("options", {}))
        elif self.type in (CommandType.chat_input, CommandOptionType.sub_command):
            # Slash commands are able to have subcommands, therefore that is handled here.
            await self.call_invoke_slash(state, interaction, option_data)
        else:
            # Anything that can't be handled in here should be raised for ApplicationCommand to handle.
            # TODO: Figure out how to hide this in exception trace log.
            raise InvalidCommandType(f"{self.type} is not a handled Application Command type.")

    async def call_invoke_slash(self, state: ConnectionState, interaction: Interaction,
                                option_data: List[Dict[str, Any]]):
        """
        This invokes the slash command implementation with the given raw option data to turn into proper kwargs for the
        callback.

        Parameters
        ----------
        state: :class:`ConnectionState`
            State object used to fetch Guild, Channel, etc from cache.
        interaction: :class:`Interaction`
            Interaction object to pass to the callback.
        option_data: :class:`list`
            List of option data dictionaries from interaction data payload.

        Returns
        -------

        """
        print(f"Running call + invoke in command {self.name}")
        kwargs = {}
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

    async def invoke_slash(self, interaction: Interaction, **kwargs):
        # Invokes the callback with the kwargs given.
        if self.cog_parent:
            await self.callback(self.cog_parent, interaction, **kwargs)
        else:
            await self.callback(interaction, **kwargs)

    def error(self, coro):
        # TODO: Parity with legacy commands.
        raise NotImplementedError

    @property
    def payload(self) -> dict:
        # noinspection PyUnresolvedReferences
        ret = {"type": self.type.value, "name": self.name, "description": self.description}
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
            result = ApplicationSubcommand(func, self, CommandOptionType.sub_command, **kwargs)
            self.children[result.name] = result
            return result
        return decorator


class ApplicationCommand(ApplicationSubcommand):
    def __init__(self, callback: Callable, cmd_type: CommandType,
                 name: str = "", description: str = "", guild_ids: List[int] = None, force_global: bool = False,
                 default_permission: Optional[bool] = None):
        # TODO: Have global and guilds be off. Allow a command to be in the system, but not registered to guilds or
        #  global. Global should be True, False, None where None makes it default to True if no guild_ids and false
        #  if there are guild_ids. For super dynamic guild_id setting, it will be done at runtime. Thus, being able to
        #  have a command not be global and not be a guild command must be possible. Index by type + name.
        super().__init__(callback=callback, parent=None, cmd_type=cmd_type, name=name, description=description,
                         guild_ids=None)
        # Basic input checking.
        if guild_ids is None:
            guild_ids = []
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("Callback must be a coroutine.")
        # Hidden variable init.
        self._state: Optional[ConnectionState] = None  # TODO: I thought there was a way around doing this, but *sigh*.
        self._is_global: Optional[bool] = True if (guild_ids and force_global) or (not guild_ids) else False
        self._is_guild: Optional[bool] = True if guild_ids else False

        self.default_permission: Optional[bool] = default_permission
        self.guild_ids: List[int] = guild_ids
        self.type = cmd_type
        self._global_id: Optional[int] = None
        self._guild_ids: Dict[int, int] = {}  # Guild ID is key, command ID is value.

    def parse_response(self, response: ApplicationCommandResponse):
        self._state = response._state
        if response.guild_id:
            self._guild_ids[response.guild_id] = response.id
        else:
            self._global_id = response.id

    async def call_from_interaction(self, interaction: Interaction):
        """Runs call using the held ConnectionState object and given interaction."""
        if not self._state:
            raise NotImplementedError("State hasn't been set yet, this isn't handled yet!")
        await self.call(self._state, interaction, interaction.data.get("options", {}))

    async def call(self, state: ConnectionState, interaction: Interaction, option_data: List[Dict[str, Any]]):
        """
        Calls the callback, gathering and inserting kwargs into the callback as needed.
        This handles CommandTypes that subcommands cannot handle, such as Message or User commands.
        :param state: ConnectionState to fetch objects from cache.
        :param interaction: Current Interaction object.
        :param option_data: List of options, typically 'options' in the interaction data payload.
        """
        try:
            await super().call(state, interaction, option_data)
        except InvalidCommandType:
            if self.type is CommandType.message:
                await self.call_invoke_message(state, interaction)
            elif self.type is CommandType.user:
                await self.call_invoke_user(state, interaction)
            else:
                raise InvalidCommandType(f"{self.type} is not a handled Application Command type.")

    def _handle_resolved_message(self, message_data: dict):
        """
        TODO: This is garbage, find a better way to add a Message to the cache.
        Parameters
        ----------
        message_data: dict
            The resolved message payload to add to the internal cache.

        Returns
        -------

        """
        # The interaction gives us message data, might as well use it and add it to the cache?
        channel, guild = self._state._get_guild_channel(message_data)
        message = Message(channel=channel, data=message_data, state=self._state)
        if not self._state._get_message(message.id) and self._state._messages is not None:
            self._state._messages.append(message)

    async def call_invoke_message(self, state: ConnectionState, interaction: Interaction):
        # TODO: Look into function arguments being autoconverted and given? Arg typed "Channel" gets filled with the
        #  channel?
        for message_data in interaction.data["resolved"]["messages"].values():
            self._handle_resolved_message(message_data)
        message = state._get_message(int(interaction.data["target_id"]))
        print(f"COMMAND_CLIENT.PY: Got message of {message} target id {interaction.data['target_id']}")
        await self.invoke_message(interaction, message)

    async def call_invoke_user(self, state: ConnectionState, interaction: Interaction):
        # TODO: Look into function arguments being autoconverted and given? Arg typed "Channel" gets filled with the
        #  channel?
        if interaction.guild:
            member = interaction.guild.get_member(int(interaction.data["target_id"]))
        else:
            member = state.get_user(int(interaction.data["target_id"]))
        # member = interaction.guild.get_member(int(interaction.data["target_id"]))
        await self.invoke_user(interaction, member)

    async def invoke_message(self, interaction: Interaction, message: Message, **kwargs):
        """The parameters of this function should have the bare minimum needed to do a user command."""
        if self.cog_parent:
            await self.callback(self.cog_parent, interaction, message, **kwargs)
        else:
            await self.callback(interaction, message, **kwargs)

    async def invoke_user(self, interaction: Interaction, member: Member, **kwargs):
        """The parameters of this function should have the bare minimum needed to do a user command."""
        if self.cog_parent:
            await self.callback(self.cog_parent, interaction, member, **kwargs)
        else:
            await self.callback(interaction, member, **kwargs)

    @property
    # def payload(self) -> Union[List[Dict[str, ...]], Dict[str, ...]]:
    def payload(self) -> List[dict]:
        """

        Returns
        -------

        """
        # TODO: This always returns a list, should it be "payloads"? Won't override subcommand payload though.
        partial_payload = super().payload
        if self.type is not CommandType.chat_input and "options" in partial_payload:
            partial_payload.pop("options")
        if self.default_permission is not None:
            partial_payload["default_permission"] = self.default_permission

    #     if self.guild_ids:
        ret = []
        if self.is_guild:
            for guild_id in self.guild_ids:
                temp = partial_payload.copy()  # This shouldn't need to be a deep copy, guild_id is on the top layer.
                temp["guild_id"] = guild_id
                ret.append(temp)
        if self.is_global:
            ret.append(partial_payload)
        return ret

    @property
    def is_guild(self) -> bool:
        return self._is_guild

    @property
    def is_global(self) -> bool:
        return self._is_global


# class CommandCogMeta(type):
#     def __new__(mcs, name, bases, namespace, **kwargs):
#         new_cls = super(CommandCogMeta, mcs).__new__(mcs, name, bases, namespace, **kwargs)


class CommandCog:
    # TODO: I get it's a terrible name, I just don't want it to duplicate current Cog right now.
    __cog_application_commands__: Dict[int, ApplicationCommand]
    __cog_to_register__: List[ApplicationCommand]


    def __new__(cls, *args, **kwargs):
        new_cls = super(CommandCog, cls).__new__(cls)
        new_cls._read_methods()
        return new_cls

    def _read_methods(self):
        self.__cog_to_register__ = []
        for base in reversed(self.__class__.__mro__):
            print(f"COG: {base}")
            for elem, value in base.__dict__.items():
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

    @property
    def to_register(self) -> List[ApplicationCommand]:
        print(f"TO REGISTER: {self.__cog_to_register__}")
        return self.__cog_to_register__


class CommandClient(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cogs: List[CommandCog] = []  # TODO: Turn this into dict with names.
        self._commands_to_reg_not_great = []

    async def on_connect(self):
        self.register_cog_commands()
        for command in self._commands_to_reg_not_great:
            await self.register_command(command)

        await super().on_connect()
        print(f"ON CONNECT: Registered command count: {len(self._application_commands)}")

    # async def register_application_commands(self):
    #     print(f"TO BE REGISTERED: {self._commands_to_register_bad}")
    #     for cmd in self._commands_to_register_bad:
    #         await self.register_command(cmd)
    #     self._commands_to_register_bad.clear()

    def register_cog_commands(self):
        print("REG COG CMD: Called.")
        for cog in self._cogs:
            print("REG COG CMD:   Cog.")
            if to_register := cog.to_register:
                for cmd in to_register:
                    print(f"REG COG CMD:     {cmd.name}")
                    # await self.register_command(cmd)
                    self.add_application_command_request(cmd)

    async def register_command(self, command: ApplicationCommand):
        # TODO: Make into bulk registration. Also look into having commands be both guild and global.
        # await self.register_application_command(command)
        self.add_application_command_to_bulk(command)
        # if command.guild_ids:
        #     for payload in command.payload:
        #         response = await self.register_application_command(command.call_from_interaction, payload, payload["guild_id"])
        #         command.parse_response(response)
        # else:
        #     response = await self.register_application_command(command.call_from_interaction, command.payload)
        #     command.parse_response(response)

    # async def delete_unknown_commands(self):
    #     to_remove = []
    #     for app_response in self._connection.application_commands:
    #         if app_response.id not in self._registered_commands:
    #             if app_response.guild_id:
    #                 print(f"Removing command NAME {app_response.name} ID {app_response.id} from "
    #                       f"GUILD {app_response.guild.name} ID {app_response.guild_id}")
    #                 await self.http.delete_guild_command(self.application_id, app_response.guild_id, app_response.id)
    #             else:
    #                 print(f"Removing command NAME {app_response.name} ID {app_response.id}")
    #                 await self.http.delete_global_command(self.application_id, app_response.id)
    #             to_remove.append(app_response.id)
    #     for app_id in to_remove:
    #         self._connection._remove_application_command(app_id)

    def add_application_command_request(self, application_command: ApplicationCommand):
        # self._commands_to_register_bad.append(application_command)
        # self.add_application_command_to_bulk(application_command)  # TODO: Unneeded, refactor.
        self._commands_to_reg_not_great.append(application_command)

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

    # async def on_application_command(self, interaction: Interaction):
    #     print(f"ON APPLICATION COMMAND: {interaction.data}")
    #     print(f"ON APPLICATION COMMAND: \n{interaction.data}\n{self._registered_commands}")
    #     # TODO: Well ain't this a bit hardcoded, huh?
    #     if interaction.data['type'] in (1, 2, 3) and \
    #             (app_cmd := self._registered_commands.get(int(interaction.data["id"]))):
    #         print("Found viable command, calling it!")
    #         await app_cmd.call(self._connection, interaction, interaction.data.get("options", {}))


def slash_command(*args, **kwargs):
    def decorator(func: Callable):
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        return ApplicationCommand(func, cmd_type=CommandType.chat_input, *args, **kwargs)
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
        return ApplicationCommand(func, cmd_type=CommandType.message, *args, **kwargs)
    return decorator


def user_command(*args, **kwargs):
    def decorator(func: Callable):
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        return ApplicationCommand(func, cmd_type=CommandType.user, *args, **kwargs)
    return decorator


def options_to_args(options: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {option["name"]: option["value"] for option in options}
    # ret = {}
    # for option in options:
    #     ret[option["name"]] = option["value"]
    # return ret
