"""
The MIT License (MIT)

Copyright (c) 2021-present tag-epic

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations
import asyncio
from inspect import signature, Parameter
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
)

from . import utils
from .abc import GuildChannel
from .enums import ApplicationCommandType, ApplicationCommandOptionType, ChannelType
from .interactions import Interaction
from .member import Member
from .message import Message
from .mixins import Hashable
from .role import Role
from .user import User
from .utils import MISSING

if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState


__all__ = (
    "ApplicationCommandResponse",
    "ApplicationCommandResponseOptionChoice",
    "ApplicationCommandResponseOption",
    "ClientCog",
    "SlashOption",
    "ApplicationSubcommand",
    "ApplicationCommand",
    "CommandOption",
    "slash_command",
    "message_command",
    "user_command",
)


class InvalidCommandType(Exception):
    """Raised when an unhandled Application Command type is encountered."""
    pass


class ApplicationCommandResponse(Hashable):
    """Represents the response that Discord sends back when queried for Application Commands.

    Attributes
    ----------
    id: :class:`int`
        Discord ID of the Application Command.
     type: :class:`nextcord.ApplicationCommandType`
    asdf: :class:`asdf`
        Enum corresponding to the Application Command type. (slash, message, user)
    guild_id: Optional[:class:`int`]
        The Guild ID associated with the Application Command. If None, it's a global command.
    name: :class:`str`
        Name of the Application Command.
    description: :class:`str`
        Description of the Application Command.
    options: List[:class:`nextcord.ApplicationCommandResponseOption`]
        A list of options or subcommands that the Application Command has.
    default_permission: :class:`bool`
        If the command is enabled for users by default.
    """

    def __init__(self, state: ConnectionState, payload: dict):
        self._state: ConnectionState = state
        self.id: int = int(payload["id"])
        self.type: ApplicationCommandType = ApplicationCommandType(payload["type"])
        self.guild_id: Optional[int] = utils._get_as_snowflake(payload, "guild_id")
        self.name: str = payload["name"]
        self.description: str = payload["description"]
        self.options: List[
            ApplicationCommandResponseOption
        ] = ApplicationCommandResponseOption._create_options(payload.get("options", []))
        self.default_permission: Optional[bool] = payload.get(
            "default_permission", True
        )

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: Returns the :class:`Guild` associated with this Response, if any."""
        return self._state._get_guild(self.guild_id)

    @property
    def signature(self) -> Tuple[str, int, Optional[int]]:
        """Returns a simple high level signature of the command. No commands registered in the bot at the same time
        should have identical signatures.

        Returns
        -------
        name: :class:`str`
            Name of the Application Command.
        type: :class:`int`
            Discord's integer value of the Application Command type
        guild_id: Optional[:class:`int`]
            The Guild ID associated with the Application Command. If None, it's a global command.
        """
        return self.name, self.type.value, self.guild_id


class ApplicationCommandResponseOptionChoice:
    """Represents a single choice in a list of options.

    Attributes
    ----------
    name: :class:`str`
        Name of the choice, this is what users see in Discord.
    value: Union[:class:`str`, :class:`int`, :class:`float`]
        Value of the choice, this is what Discord sends back to us.
    """

    def __init__(self, payload: Optional[dict] = None):
        if not payload:
            payload = {}
        self.name: str = payload["name"]
        self.value: Union[str, int, float] = payload["value"]


class ApplicationCommandResponseOption:
    """Represents an argument/parameter/option or subcommand of an Application Command.

    Attributes
    ----------
    type: :class:`ApplicationCommandOptionType`
        Enum corresponding to the Application Command Option type. (subcommand, string, integer, etc.)
    name: :class:`str`
        Name of the option or subcommand.
    description: :class:`str`
        Description of the option or subcommand.
    required: :class:`bool`
        If this option is required for users or not.
    """

    def __init__(self, payload: dict):
        self.type = ApplicationCommandOptionType(int(payload["type"]))
        self.name: str = payload["name"]
        self.description: str = payload["description"]
        self.required: Optional[bool] = payload.get("required")
        self.choices: List[ApplicationCommandResponseOptionChoice] = self._create_choices(payload.get("choices", []))
        self.options: List[ApplicationCommandResponseOption] = self._create_options(payload.get("options", []))

    @staticmethod
    def _create_choices(data: List[dict]) -> List[ApplicationCommandResponseOptionChoice]:
        return [ApplicationCommandResponseOptionChoice(raw_choice) for raw_choice in data]

    @staticmethod
    def _create_options(data: List[dict]) -> List[ApplicationCommandResponseOption]:
        return [ApplicationCommandResponseOption(raw_option) for raw_option in data]


class ClientCog:
    # TODO: I get it's a terrible name, I just don't want it to duplicate current Cog right now.
    __cog_application_commands__: Dict[int, ApplicationCommand]
    __cog_to_register__: List[ApplicationCommand]

    def __new__(cls, *args: Any, **kwargs: Any):
        new_cls = super(ClientCog, cls).__new__(cls)
        new_cls._read_methods()
        return new_cls

    def _read_methods(self) -> None:
        self.__cog_to_register__ = []
        for base in reversed(self.__class__.__mro__):
            for elem, value in base.__dict__.items():
                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__
                if isinstance(value, ApplicationCommand):
                    if isinstance(value, staticmethod):
                        raise TypeError(f"Command {self.__name__}.{elem} can not be a staticmethod.")
                    value.set_self_argument(self)
                    self.__cog_to_register__.append(value)
                elif isinstance(value, ApplicationSubcommand):
                    value.set_self_argument(self)

    @property
    def to_register(self) -> List[ApplicationCommand]:
        return self.__cog_to_register__


# class SlashOption:
#     def __init__(
#         self,
#         name: str = None,
#         description: str = None,
#         required: bool = None,
#         choices: dict = None,
#         default: Any = None,
#         channel_types: List[ChannelType] = None,
# ):
class SlashOption:
    def __init__(self, name: str = MISSING,
                 description: str = MISSING,
                 required: bool = MISSING,
                 choices: Dict[str, Union[str, int, float]] = MISSING,
                 channel_types: List[ChannelType] = MISSING,
                 min_value: Union[int, float] = MISSING,
                 max_value: Union[int, float] = MISSING,
                 autocomplete: bool = MISSING,
                 default: Optional[Any] = None,
                 verify: bool = True
                 ):
        """Provides Discord with information about an option in a command.

        When this class is set as the default argument of a parameter in an Application Command, additional information
        about the parameter is sent to Discord for the user to see.

        Parameters
        ----------
        name: Optional[:class:`str`]
            The name of the Option on Discords side. If left as None, it defaults to the parameter name.
        description: Optional[:class:'str']
            The description of the Option on Discords side. If left as None, it defaults to "".
        required: Optional[:class:'bool']
            If a user is required to provide this argument before sending the command. Defaults to Discords choice. (False at this time)
        choices: Optional[:class:`bool`]
            Dictionary of choices. The keys are what the user sees, the values correspond to what is sent to us.
        default: Optional[Any]
            When required is not True and the user doesn't provide a value for this Option, this value is given instead.
        channel_types: Optional[List[:class:`enums.ChannelType`]]
            The list of valid channel types for the user to choose from. Used only by channel Options.
        """
        self.name: Optional[str] = name
        self.description: Optional[str] = description
        self.required: Optional[bool] = required
        self.choices: Optional[dict] = choices
        self.channel_types: Optional[List[ChannelType, ...]] = channel_types
        self.min_value: Optional[Union[int, float]] = min_value
        self.max_value: Optional[Union[int, float]] = max_value
        self.autocomplete: Optional[bool] = autocomplete
        self.default: Optional[Any] = default
        if verify:
            self.verify()

    def verify(self) -> bool:
        """Checks if the given values conflict with one another or are invalid."""

        if self.choices and self.autocomplete:  # Incompatible according to Discord Docs.
            raise ValueError("Autocomplete may not be set to true if choices are present.")
        return True


class CommandOption(SlashOption):
    option_types = {
        str: ApplicationCommandOptionType.string,
        int: ApplicationCommandOptionType.integer,
        bool: ApplicationCommandOptionType.boolean,
        User: ApplicationCommandOptionType.user,
        Member: ApplicationCommandOptionType.user,
        GuildChannel: ApplicationCommandOptionType.channel,
        Role: ApplicationCommandOptionType.role,
        # TODO: Is this in the library at all currently? This includes Users and Roles.
        # Mentionable: CommandOptionType.mentionable
        float: ApplicationCommandOptionType.number,
        Message: ApplicationCommandOptionType.integer  # TODO: This is janky, the user provides an ID or something? Ugh.
    }
    """Maps Python typings to Discord Application Command typings."""
    def __init__(self, parameter: Parameter):
        """Represents a Python function parameter that corresponds to a Discord Option.

        This must set and/or handle all variables from SlashOption, hence the subclass.
        This shouldn't be created by the user, only by other Application Command-related classes.

        Parameters
        ----------
        parameter: :class:`inspect.Parameter`
            The Application Command Parameter object to read and make usable by Discord.
        """
        super().__init__()
        self.parameter = parameter
        cmd_arg_given = False
        cmd_arg = SlashOption()
        if isinstance(parameter.default, SlashOption):
            cmd_arg = parameter.default
            cmd_arg_given = True
        self.functional_name = parameter.name

        # All optional variables need to default to MISSING for functions down the line to understand that they were
        # never set. If Discord demands a value, it should be the minimum value required.
        self.name = cmd_arg.name or parameter.name
        self._description = cmd_arg.description or MISSING
        # While long, this is required. If cmd_arg.required is False, the expression:
        # self.required = cmd_arg.required or MISSING
        # will cause self.required to be MISSING, not False.
        self.required = cmd_arg.required if cmd_arg.required is not MISSING else MISSING
        self.choices = cmd_arg.choices or MISSING
        self.channel_types = cmd_arg.channel_types or MISSING
        # min_value of 0 will cause an `or` to give the variable MISSING
        self.min_value = cmd_arg.min_value if cmd_arg.min_value is not MISSING else MISSING
        # max_value of 0 will cause an `or` to give the variable MISSING
        self.max_value = cmd_arg.max_value if cmd_arg.max_value is not MISSING else MISSING
        # autocomplete set to False will cause an `or` to give the variable MISSING
        self.autocomplete = cmd_arg.autocomplete if cmd_arg.autocomplete is not MISSING else MISSING

        if not cmd_arg_given and parameter.default is not parameter.empty:
            self.default = parameter.default
        else:
            self.default = cmd_arg.default

        # if self.required is MISSING and self.default is None:
        #     self.required = True

        self.autocomplete_function: Optional[Callable] = MISSING

        self.type: ApplicationCommandOptionType = self.get_type(parameter.annotation)
        self.verify()

    # Basic getters and setters.

    @property
    def description(self) -> str:
        if not self._description:
            return " "
        else:
            return self._description

    @description.setter
    def description(self, value: str):
        self._description = value

    def get_type(self, typing: type) -> ApplicationCommandOptionType:

        if typing is self.parameter.empty:
            return ApplicationCommandOptionType.string
        elif valid_type := self.option_types.get(typing, None):
            return valid_type
        else:
            raise NotImplementedError(f'Type "{typing}" isn\'t a supported typing for Application Commands.')

    def verify(self) -> None:
        """This should run through CmdArg variables and raise errors when conflicting data is given."""
        super().verify()
        if self.channel_types and self.type is not ApplicationCommandOptionType.channel:
            raise ValueError("channel_types can only be given when the var is typed as nextcord.abc.GuildChannel")
        if self.min_value is not MISSING and type(self.min_value) not in (int, float):
            raise ValueError("min_value must be an int or float.")
        if self.max_value is not MISSING and type(self.max_value) not in (int, float):
            raise ValueError("max_value must be an int or float.")
        if (self.min_value is not MISSING or self.max_value is not MISSING) and self.type not in (
                ApplicationCommandOptionType.integer, ApplicationCommandOptionType.number):
            raise ValueError("min_value or max_value can only be set if the type is integer or number.")

    def handle_slash_argument(self, state: ConnectionState, argument: Any, interaction: Interaction) -> Any:
        """Handles arguments, specifically for Slash Commands."""
        if self.type is ApplicationCommandOptionType.channel:
            return state.get_channel(int(argument))
        elif self.type is ApplicationCommandOptionType.user:
            if interaction.guild:
                return interaction.guild.get_member(int(argument))
            else:
                return state.get_user(int(argument))
        elif self.type is ApplicationCommandOptionType.role:
            return interaction.guild.get_role(int(argument))
        elif self.type is ApplicationCommandOptionType.integer:
            return int(argument)
        elif self.type is ApplicationCommandOptionType.number:
            return float(argument)
        elif self.type is Message:  # TODO: This is mostly a workaround for Message commands, switch to handles below.
            return state._get_message(int(argument))
        return argument

    def handle_message_argument(self, *args: List[Any]):
        """For possible future use, will handle arguments specific to Message Commands (Context Menu type.)"""
        raise NotImplementedError  # TODO: Even worth doing? We pass in what we know already.

    def handle_user_argument(self, *args: List[Any]):
        """For possible future use, will handle arguments specific to User Commands (Context Menu type.)"""
        raise NotImplementedError  # TODO: Even worth doing? We pass in what we know already.

    @property
    def payload(self) -> dict:
        """Returns a payload meant for Discord for this specific Option.

        Options that are not specified AND not required won't be in the returned payload.

        Returns
        -------
        payload: :class:`dict`
            The Discord payload for this specific Option.
        """
        # TODO: Figure out why pycharm is being a dingus about self.type.value being an unsolved attribute.
        # noinspection PyUnresolvedReferences
        ret = {"type": self.type.value, "name": self.name, "description": self.description}
        # False is included in this because that's the default for Discord currently. Not putting in the required param
        # when possible minimizes the payload size and makes checks between registered and found commands easier.
        if self.required:
            ret["required"] = self.required
        if self.required is not MISSING:
            pass  # Discord doesn't currently provide Required if it's False due to it being default.
        else:
            # While this violates Discord's default and our goal (not specified should return minimum or nothing), a
            # parameter being optional by default goes against traditional programming. A parameter not explicitly
            # stated to be optional should be required.
            ret["required"] = True

        if self.choices:
            ret["choices"] = [{"name": key, "value": value} for key, value in self.choices.items()]
        if self.channel_types:
            # noinspection PyUnresolvedReferences
            ret["channel_types"] = [channel_type.value for channel_type in self.channel_types]
        # We don't ask for the payload if we have options, so no point in checking for options.
        if self.min_value is not MISSING:
            ret["min_value"] = self.min_value
        if self.max_value is not MISSING:
            ret["max_value"] = self.max_value
        if self.autocomplete is not MISSING:
            ret["autocomplete"] = self.autocomplete
        return ret


class ApplicationSubcommand:
    def __init__(
        self,
        callback: Callable = MISSING,
        parent_command: Optional[Union[ApplicationCommand, ApplicationSubcommand]] = MISSING,
        cmd_type: Optional[Union[ApplicationCommandType, ApplicationCommandOptionType]] = MISSING,
        self_argument: Union[ClientCog, Any] = MISSING,
        name: str = MISSING,
        description: str = MISSING,
    ):
        self._callback: Optional[Callable] = None  # TODO: Add verification against vars if callback is added later.
        self.parent_command: Optional[Union[ApplicationCommand, ApplicationSubcommand]] = parent_command
        self.type: Optional[ApplicationCommandOptionType] = cmd_type
        self._self_argument: Optional[ClientCog] = self_argument
        self.name: Optional[str] = name
        self._description: str = description

        self.options: Dict[str, CommandOption] = {}
        self.children: Dict[str, ApplicationSubcommand] = {}

        # self._on_autocomplete: Dict[str, Callable] = {}  # TODO: Maybe move the callbacks into the CommandOptions?

        if callback:
            self._from_callback(callback)

    # Simple getter and setter methods..

    @property
    def error_name(self) -> str:
        return f"{self.__class__.__name__} {self.name} {self.callback}"

    @property
    def description(self) -> str:
        if self._description is MISSING:  # Return Discords bare minimum for a command.
            return " "
        else:
            return self._description

    # def get_option_functional_names(self) -> List[str]:
    #     """Returns a list with the functional, kwarg names of options."""
    #     if self.options:  # If performance from list comprehension is an issue, look into keeping a set/list around.
    #         return [option.functional_name for option in self.options.values()]
    #     else:
    #         return []

    # def _analyze_content(self) -> None:
    #     """This reads the content of itself and performs validation and changes to variables as needed."""
    #     if self.parent_command and self.parent_command.type is ApplicationCommandOptionType.sub_command_group and \
    #             self.children:
    #         raise NotImplementedError("A subcommand can't have both subcommand parents and children! Discord does not"
    #                                   "support this.")
    #     if isinstance(self.parent_command, ApplicationCommand):
    #         if self.children:
    #             self.type = ApplicationCommandOptionType.sub_command_group
    #         else:
    #             self.type = ApplicationCommandOptionType.sub_command
    #     if self.type is ApplicationCommandType.user or self.type is ApplicationCommandType.message:
    #         self.description = ""
    #     else:
    #         if not self.description:
    #             self.description = " "

    def verify_content(self):
        """This verifies the content of the subcommand and raises errors for violations."""
        if not self.callback:
            raise ValueError(f"{self.error_name} No callback assigned!")
        if not self.type:
            raise ValueError(f"{self.error_name} Subcommand type needs to be set.")
        if self.type not in (ApplicationCommandOptionType.sub_command, ApplicationCommandOptionType.sub_command_group):
            raise ValueError(f"{self.error_name} Command type is not set to a valid type, it needs to be a sub_command "
                             f"or sub_command_group")
        if self.type is not ApplicationCommandOptionType.sub_command_group and self.children:
            raise ValueError(f"{self.error_name} ")
        if self.parent_command and self.type is ApplicationCommandOptionType.sub_command_group and \
                self.parent_command.type is ApplicationCommandOptionType.sub_command_group:
            raise NotImplementedError(f"{self.error_name}Discord has not implemented subcommands more than 2 levels deep.")
        for option in self.options.values():
            if option.autocomplete:
                if not option.autocomplete_function:
                    raise ValueError(f"{self.error_name} Kwarg {option.functional_name} has autocomplete enabled, but no on_autocomplete assigned.")
                # While we could check if it has autocomplete disabled but an on_autocomplete function, why should we
                # bother people who are likely reworking their code? It also doesn't break anything.

    @classmethod
    def from_callback(cls, callback: Callable) -> ApplicationSubcommand:
        return cls()._from_callback(callback)

    def _from_callback(self, callback: Callable) -> ApplicationSubcommand:
        # TODO: Add kwarg support.
        # ret = ApplicationSubcommand()
        self.set_callback(callback)
        if not self.name:
            self.name = self.callback.__name__
        first_arg = True

        for value in signature(self.callback).parameters.values():
            self_skip = value.name == "self"  # TODO: What kind of hardcoding is this, figure out a better way for self!
            if first_arg:
                if not self_skip:
                    first_arg = False
            else:
                arg = CommandOption(value)
                self.options[arg.name] = arg
        return self

    @property
    def callback(self) -> Callable:
        return self._callback

    def set_callback(self, callback: Callable) -> ApplicationSubcommand:
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("Callback must be a coroutine.")
        self._callback = callback
        return self

    def set_self_argument(self, self_arg: ClientCog) -> ApplicationSubcommand:
        self._self_argument = self_arg
        return self

    def add_option_autocomplete(self, option: CommandOption, func: Callable):
        if not asyncio.iscoroutinefunction(func):
            raise ValueError(f"{self.error_name} Autocomplete callbacks need to be a coroutine.")
        option.autocomplete_function = func

    async def call_autocomplete(self, state, interaction: Interaction, option_data: List[Dict[str, Any]]) -> None:
        if self.children:  # If this has subcommands, it needs to be forwarded to them to handle.
            await self.children[option_data[0]["name"]].call_autocomplete(state, interaction, option_data[0].get("options", {}))
        elif self.type in (ApplicationCommandType.chat_input, ApplicationCommandOptionType.sub_command):
            focused_option_name = None
            for arg in option_data:
                if arg["focused"] is True:
                    if focused_option_name:
                        raise ValueError("Multiple options are focused, is that supposed to be possible?")
                    focused_option_name = arg["name"]
                    # break

            if focused_option_name:
                focused_option = self.options[focused_option_name]
                autocomplete_kwargs = signature(focused_option.autocomplete_function).parameters.keys()
                kwargs = {}
                uncalled_options = self.options.copy()
                for arg_data in option_data:
                    if option := uncalled_options.get(arg_data["name"], None):
                        uncalled_options.pop(option.name)
                        if option.functional_name in autocomplete_kwargs:
                            kwargs[option.functional_name] = option.handle_slash_argument(state, arg_data["value"], interaction)
                    else:
                        # TODO: Handle this better.
                        raise NotImplementedError(
                            f"An argument was provided that wasn't already in the function, did you"
                            f"recently change it?\nRegistered Options: {self.options}, Discord-sent"
                            f"args: {interaction.data['options']}, broke on {arg_data}"
                        )
                for option in uncalled_options.values():
                    if option.functional_name in autocomplete_kwargs:
                        kwargs[option.functional_name] = option.default
                await self.invoke_autocomplete(interaction, focused_option, **kwargs)
            else:
                raise ValueError("There's supposed to be a focused option, but it's not found?")
        else:
            raise NotImplementedError(f"{self.error_name} Autocomplete isn't handled by this type of command, how did "
                                      f"you get here?")

    async def invoke_autocomplete(self, interaction: Interaction, focused_option: CommandOption, **kwargs) -> None:
        if self._self_argument:
            await focused_option.autocomplete_function(self._self_argument, interaction, **kwargs)
        else:
            await focused_option.autocomplete_function(interaction, **kwargs)

    async def call(self, state: ConnectionState, interaction: Interaction, option_data: List[Dict[str, Any]]) -> None:
        if self.children:
            # Discord currently does not allow commands that have subcommands to be ran. Therefore, if a command has
            # children, a subcommand must be being called.
            await self.children[option_data[0]["name"]].call(state, interaction, option_data[0].get("options", {}))
        elif self.type in (ApplicationCommandType.chat_input, ApplicationCommandOptionType.sub_command):
            # Slash commands are able to have subcommands, therefore that is handled here.
            await self.call_invoke_slash(state, interaction, option_data)
        else:
            # Anything that can't be handled in here should be raised for ApplicationCommand to handle.
            # TODO: Figure out how to hide this in exception trace log, devs don't need to see it.
            raise InvalidCommandType(f"{self.type} is not a handled Application Command type.")

    async def call_invoke_slash(self, state: ConnectionState, interaction: Interaction,
                                option_data: List[Dict[str, Any]]) -> None:
        kwargs = {}
        uncalled_args = self.options.copy()
        for arg_data in option_data:
            if arg_data["name"] in uncalled_args:
                uncalled_args.pop(arg_data["name"])
                kwargs[self.options[arg_data["name"]].functional_name] = \
                    self.options[arg_data["name"]].handle_slash_argument(state, arg_data["value"], interaction)
            else:
                # TODO: Handle this better.
                raise NotImplementedError(
                    f"An argument was provided that wasn't already in the function, did you"
                    f"recently change it?\nRegistered Options: {self.options}, Discord-sent"
                    f"args: {interaction.data['options']}, broke on {arg_data}"
                )
        for uncalled_arg in uncalled_args.values():
            kwargs[uncalled_arg.functional_name] = uncalled_arg.default
        await self.invoke_slash(interaction, **kwargs)

    async def invoke_slash(self, interaction: Interaction, **kwargs: Dict[Any, Any]) -> None:
        if self._self_argument:
            await self.callback(self._self_argument, interaction, **kwargs)
        else:
            await self.callback(interaction, **kwargs)

    def error(self, coro):
        # TODO: Parity with legacy commands.
        raise NotImplementedError

    @property
    def payload(self) -> dict:
        # self._analyze_content()
        self.verify_content()
        ret = {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
        }
        # if self.choices:
        #     ret["choices"] = [{key: value} for key, value in self.choices.items()]
        if self.children:
            ret["options"] = [child.payload for child in self.children.values()]
        elif self.options:
            ret["options"] = [argument.payload for argument in self.options.values()]
        return ret

    def on_autocomplete(self, on_kwarg: str):
        if self.type not in (ApplicationCommandType.chat_input, ApplicationCommandOptionType.sub_command):  # At this time, non-slash commands cannot have autocomplete.
            raise TypeError(f"{self.error_name} {self.type} cannot have autocomplete.")
        found = False
        for name, option in self.options.items():
            if option.functional_name == on_kwarg:
                found = True
                if option.autocomplete is MISSING:
                    option.autocomplete = True
                if option.autocomplete:
                    def decorator(func: Callable):
                        self.add_option_autocomplete(option, func)
                        return func
                    return decorator
                else:
                    print(type(option.autocomplete))
                    raise ValueError(f"{self.error_name} autocomplete for kwarg {on_kwarg} not enabled, cannot add "
                                     f"autocomplete function.")
        if found is False:
            raise TypeError(f"{self.error_name} kwarg {on_kwarg} not found, cannot add autocomplete function.")

    def subcommand(self, **kwargs):
        def decorator(func: Callable):
            # result = ApplicationSubcommand(func, self, ApplicationCommandOptionType.sub_command, **kwargs)
            # result = ApplicationSubcommand.from_callback(func)

            # result.type = ApplicationCommandOptionType.sub_command
            result = ApplicationSubcommand(callback=func, parent_command=self,
                                           cmd_type=ApplicationCommandOptionType.sub_command, **kwargs)
            self.type = ApplicationCommandOptionType.sub_command_group
            self.children[result.name] = result
            return result
        return decorator


class ApplicationCommand(ApplicationSubcommand):
    def __init__(
        self,
        callback: Callable = MISSING,
        cmd_type: ApplicationCommandType = MISSING,
        name: str = MISSING,
        description: str = MISSING,
        guild_ids: List[int] = MISSING,
        default_permission: Optional[bool] = MISSING,
        force_global: bool = False,
    ):
        # super().__init__(callback=callback, parent=None, cmd_type=cmd_type, name=name, description=description)
        super().__init__(callback=callback, cmd_type=cmd_type, name=name, description=description)
        # self.name = name
        # self.description = self.description or description
        # self._from_callback(callback)
        # Basic input checking.
        self._state: Optional[ConnectionState] = None
        self.force_global: bool = force_global
        # self._is_global: Optional[bool] = True if (guild_ids and force_global) or (not guild_ids) else False
        # self._is_guild: Optional[bool] =

        # self.default_permission: Optional[bool] = default_permission
        self.default_permission: bool = default_permission or True
        self.guild_ids: List[int] = guild_ids or []
        # self.type = cmd_type
        self._global_command_id: Optional[int] = None
        self._guild_command_ids: Dict[int, int] = {}  # Guild ID is key, command ID is value.

    # Property Methods and basic variable getter + setters.

    @property
    def description(self) -> str:
        if self._description is MISSING:  # Return Discord's bare minimum for a command.
            if self.type is ApplicationCommandType.chat_input:
                return " "
            elif self.type in (ApplicationCommandType.user, ApplicationCommandType.message):
                return ""
        else:
            return self._description

    @property
    def global_payload(self) -> Optional[dict]:
        if not self.is_global:
            return None
        return self._get_basic_application_payload()

    @property
    def is_guild(self) -> bool:
        return True if self.guild_ids else False

    @property
    def is_global(self) -> bool:
        """This should return True if either force_global is True or no guild_ids are given."""
        return True if (self.force_global or not self.is_guild) else False

    def set_state(self, state: ConnectionState) -> ApplicationCommand:
        self._state = state
        return self

    # Shortcuts for ApplicationCommand creation.

    @classmethod
    def from_callback(cls, callback: Callable) -> ApplicationCommand:
        return cls()._from_callback(callback)

    # def parse_response(self, response: ApplicationCommandResponse) -> None:
    #     self.raw_parse_result(response._state, response.id, response.guild_id)

    # Command helper methods.

    def verify_content(self):
        """This verifies the content of the command and raises errors for violations."""
        if not self.callback and not self.children:
            raise ValueError(f"{self.error_name} No callback assigned!")
        # Note that while having a callback and children is iffy, it's not worth raising an error.
        if not self.type:
            raise ValueError(f"{self.error_name} Command type needs to be set.")
        if not isinstance(self.type, ApplicationCommandType):
            raise ValueError(f"{self.error_name} Command type is not set to a valid type.")
        if self.type in (ApplicationCommandType.user, ApplicationCommandType.message) and self.children:
            raise ValueError(f"{self.error_name} This type of command cannot have children.")
        if self.description and self.type in (ApplicationCommandType.user, ApplicationCommandType.message):
            raise ValueError(f"{self.error_name} This type of command cannot have a description.")

    def parse_discord_response(self, state: ConnectionState, command_id: int, guild_id: Optional[int], ) -> None:
        self.set_state(state)
        if guild_id:
            self._guild_command_ids[guild_id] = command_id
        else:
            self._global_command_id = command_id

    async def call_autocomplete_from_interaction(self, interaction: Interaction):
        if not self._state:
            raise NotImplementedError("State hasn't been set yet, this isn't handled yet!")
        await self.call_autocomplete(self._state, interaction, interaction.data.get("options", {}))

    async def call_from_interaction(self, interaction: Interaction) -> None:
        if not self._state:
            raise NotImplementedError("State hasn't been set yet, this isn't handled yet!")
        await self.call(self._state, interaction, interaction.data.get("options", {}))

    async def call(self, state: ConnectionState, interaction: Interaction, option_data: List[Dict[str, Any]]) -> None:
        try:
            await super().call(state, interaction, option_data)
        except InvalidCommandType:
            if self.type is ApplicationCommandType.message:
                await self.call_invoke_message(interaction)
            elif self.type is ApplicationCommandType.user:
                await self.call_invoke_user(interaction)
            else:
                raise InvalidCommandType(f"{self.type} is not a handled Application Command type.")

    def _handle_resolved_message(self, message_data: dict) -> Message:
        # TODO: This is garbage, find a better way to add a Message to the cache.
        #  It's not that I'm unhappy adding things to the cache, it's having to manually do it like this.
        # The interaction gives us message data, might as well use it and add it to the cache.
        channel, guild = self._state._get_guild_channel(message_data)
        message = Message(channel=channel, data=message_data, state=self._state)
        if not self._state._get_message(message.id) and self._state._messages is not None:
            self._state._messages.append(message)
        return message

    def _handle_resolved_user(self, user_data: dict) -> User:
        return self._state.store_user(user_data)

    async def call_invoke_message(self, interaction: Interaction) -> None:
        # TODO: Look into function arguments being autoconverted and given? Arg typed "Channel" gets filled with the
        #  channel?
        # Is this kinda dumb? Yeah, but at this time it can only return one message.
        message = self._handle_resolved_message(list(interaction.data["resolved"]["messages"].values())[0])
        await self.invoke_message(interaction, message)

    async def call_invoke_user(self, interaction: Interaction) -> None:
        # TODO: Look into function arguments being autoconverted and given? Arg typed "Channel" gets filled with the
        #  channel?
        # Is this kinda dumb? Yeah, but at this time it can only return one user.
        user = self._handle_resolved_user(list(interaction.data["resolved"]["users"].values())[0])
        if interaction.guild and (member := interaction.guild.get_member(user.id)):
            await self.invoke_user(interaction, member)
        else:
            await self.invoke_user(interaction, user)

    async def invoke_message(self, interaction: Interaction, message: Message, **kwargs: Dict[Any, Any]) -> None:
        if self._self_argument:
            await self.callback(self._self_argument, interaction, message, **kwargs)
        else:
            await self.callback(interaction, message, **kwargs)

    async def invoke_user(self, interaction: Interaction, member: Union[Member, User], **kwargs: Dict[Any, Any]) -> None:
        """|coro|

        Invokes the callback with the given interaction, member/user, and kwargs as a User Command."""
        if self._self_argument:
            await self.callback(self._self_argument, interaction, member, **kwargs)
        else:
            await self.callback(interaction, member, **kwargs)

    def _get_basic_application_payload(self) -> dict:
        """Bare minimum payload that both Global and Guild commands can use."""
        payload = super().payload
        if self.type is not ApplicationCommandType.chat_input and "options" in payload:
            payload.pop("options")
        if self.default_permission is not None:
            payload["default_permission"] = self.default_permission
        return payload

    @property
    def payload(self) -> List[dict]:
        """Returns a list of Discord "Application Command Structure" payloads.

        Returns
        -------
        payloads: List[:class:`dict`]
            Returns a list containing the global command payload, if enabled, and payloads corresponding to every guild
            ID specified.
        """
        # TODO: This always returns a list, should it be "payloads"? Won't override subcommand payload though.
        partial_payload = self._get_basic_application_payload()

        ret = []
        if self.is_guild:
            for guild_id in self.guild_ids:
                temp = (partial_payload.copy())  # We don't need to make a deep copy as guild_id is on the top layer.
                temp["guild_id"] = guild_id
                ret.append(temp)
        if self.is_global:
            ret.append(partial_payload)
        return ret

    def get_guild_payload(self, guild_id: int) -> Optional[dict]:
        if not self.is_guild or guild_id not in self.guild_ids:
            return None
        partial_payload = self._get_basic_application_payload()
        partial_payload["guild_id"] = guild_id
        return partial_payload

    def get_signature(self, guild_id: Optional[int]) -> Optional[Tuple[str, int, Optional[int]]]:
        """Returns a basic signature for a given Guild ID. If None is given, then it is assumed Global."""
        if (guild_id is None and self.is_global) or (guild_id in self.guild_ids):
            return self.name, self.type.value, guild_id
        else:
            return None

    def get_signatures(self) -> Set[Tuple[str, int, Optional[int]]]:
        """Returns all basic signatures for this ApplicationCommand."""
        ret = set()
        if self.is_global:
            ret.add((self.name, self.type.value, None))
        if self.is_guild:
            for guild_id in self.guild_ids:
                ret.add((self.name, self.type.value, guild_id))
        return ret

    def check_against_raw_payload(self, raw_payload: dict, guild_id: Optional[int]) -> bool:
        """Checks if self.payload values match with what the given raw payload has.

        This doesn't make sure they are equal. Instead, this checks if all key:value pairs inside of any of our payloads
        also exist inside of the raw_payload. If there are extra keys inside of the raw_payload that aren't in our
        payloads, they will be ignored.

        Parameters
        ----------
        raw_payload: :class:`dict`
            Dictionary payload our payloads are compared against.
        guild_id: Optional[:class:`int`]
            Guild ID to compare against. If None, it's assumed to be a Global command.

        Returns
        -------
        :class:`bool`
            True if any of our payloads has every key:value pair corresponding with key:value's in the raw_payload,
            False otherwise.
        """
        # our_payloads = self.payload
        # for our_payload in our_payloads:
        #     if our_payload.get("guild_id", None) == guild_id:
        #         if self._recursive_item_check(our_payload, raw_payload):
        #             return True
        if guild_id:
            if self._recursive_item_check(self.get_guild_payload(guild_id), raw_payload):
                return True
        else:
            if self._recursive_item_check(self.global_payload, raw_payload):
                return True
        return False

    def reverse_check_against_raw_payload(self, raw_payload: dict, guild_id: Optional[int]) -> bool:
        """Checks if the given raw payload values match with what self.payload has.

        This doesn't make sure they are equal, and works opposite of check_against_raw_payload. This checks if all
        key:value's inside of the raw_payload also exist inside one of our payloads.

        Parameters
        ----------
        raw_payload: :class:`dict`
            Dictionary payload to compare against our payloads.
        guild_id: :class:`int`
            Guild ID to compare against. If None, it's assumed to be a Global command.

        Returns
        -------
        :class:`bool`
            True if the raw_payload has every key:value pair corresponding to any of our payloads, False otherwise.
        """
        modded_payload = raw_payload.copy()
        modded_payload.pop("id")
        for our_payload in self.payload:
            if our_payload.get("guild_id", None) == guild_id:
                if self._recursive_item_check(modded_payload, our_payload):
                    return True
        return False

    def _recursive_item_check(self, item1, item2) -> bool:
        """Checks if item1 and item2 are equal.

        If both are lists, switches to list check. If dict, recurses. Else, checks equality.
        """
        if isinstance(item1, dict) and isinstance(item2, dict):
            for key, item in item1.items():
                if key == "value":
                    pass
                elif key not in item2:
                    return False
                elif not self._recursive_item_check(item, item2[key]):
                    return False
        elif isinstance(item1, list) and isinstance(item2, list):
            for our_item in item1:
                if not self._recursive_check_item_against_list(our_item, item2):
                    return False
        else:
            if isinstance(item1, str) and item1.isdigit():
                item1 = int(item1)
            if isinstance(item2, str) and item2.isdigit():
                item2 = int(item2)
            if item1 != item2:
                return False
        return True

    def _recursive_check_item_against_list(self, item1, list2: list) -> bool:
        if isinstance(item1, list):
            raise NotImplementedError
        elif isinstance(item1, dict):
            for item2 in list2:
                if isinstance(item2, list):
                    raise NotImplementedError
                elif isinstance(item2, dict):
                    if self._recursive_item_check(item1, item2):
                        return True
                else:
                    raise NotImplementedError
        else:
            raise NotImplementedError
        return False

    def subcommand(self, **kwargs):
        """Makes a function into a subcommand."""
        if self.type != ApplicationCommandType.chat_input:  # At this time, non-slash commands cannot have Subcommands.
            raise TypeError(f"{self.error_name} {self.type} cannot have subcommands.")
        else:
            def decorator(func: Callable):
                # result = ApplicationSubcommand(func, self, ApplicationCommandOptionType.sub_command, **kwargs)
                # result = ApplicationSubcommand.from_callback(func)
                result = ApplicationSubcommand(callback=func, parent_command=self, **kwargs)
                result.type = ApplicationCommandOptionType.sub_command
                self.children[result.name] = result
                return result

            return decorator


def slash_command(**kwargs):
    """Creates a Slash Application Command, used inside of a ClientCog."""
    def decorator(func: Callable):
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        # return ApplicationCommand(func, cmd_type=ApplicationCommandType.chat_input, **kwargs)
        # app_cmd = ApplicationCommand.from_callback(func)
        # app_cmd.type = ApplicationCommandType.chat_input
        # if guild_ids := kwargs.get("guild_ids"):
        #     # print("GOT GUILD IDS!")
        #     app_cmd.guild_ids = guild_ids
        app_cmd = ApplicationCommand(callback=func, cmd_type=ApplicationCommandType.chat_input, **kwargs)
        return app_cmd

    return decorator


def message_command(**kwargs):
    """Creates a Message Application Command, used inside of a ClientCog."""
    def decorator(func: Callable):
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        # return ApplicationCommand(func, cmd_type=ApplicationCommandType.message, **kwargs)
        # app_cmd = ApplicationCommand.from_callback(func)
        # app_cmd.type = ApplicationCommandType.message
        app_cmd = ApplicationCommand(callback=func, cmd_type=ApplicationCommandType.message, **kwargs)
        return app_cmd
    return decorator


def user_command(**kwargs):
    """Creates a User Application Command, used inside of a ClientCog."""
    def decorator(func: Callable):
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        # return ApplicationCommand(func, cmd_type=ApplicationCommandType.user, **kwargs)
        # app_cmd = ApplicationCommand.from_callback(func)
        # app_cmd.type = ApplicationCommandType.user
        app_cmd = ApplicationCommand(callback=func, cmd_type=ApplicationCommandType.user, **kwargs)
        return app_cmd
    return decorator
