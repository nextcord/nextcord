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
import typing
from inspect import signature, Parameter
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Tuple,
    Union,
    TypeVar,
)
import typing

from .abc import GuildChannel
from .enums import ApplicationCommandType, ApplicationCommandOptionType, ChannelType
from .errors import (
    InvalidCommandType,
    ApplicationCheckFailure,
    ApplicationError,
    ApplicationInvokeError,
)
from .interactions import Interaction
from .guild import Guild
from .member import Member
from .message import Attachment, Message
from .role import Role
from .user import User
from .utils import MISSING, find, maybe_coroutine, parse_docstring

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.checks import (
        ApplicationErrorCallback,
        ApplicationHook,
        ApplicationCheck,
    )

    _SlashOptionMetaBase = Any
else:
    _SlashOptionMetaBase = object

__all__ = (
    "ApplicationCommand",
    "ApplicationSubcommand",
    "ClientCog",
    "CommandOption",
    "message_command",
    "SlashOption",
    "slash_command",
    "user_command",
)

# Maximum allowed length of a command or option description
_MAX_COMMAND_DESCRIPTION_LENGTH = 100

T = TypeVar("T")
FuncT = TypeVar("FuncT", bound=Callable[..., Any])


def _cog_special_method(func: FuncT) -> FuncT:
    func.__cog_special_method__ = None
    return func


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
                        raise TypeError(
                            f"Command {self.__name__}.{elem} can not be a staticmethod."
                        )
                    value.set_self_argument(self)
                    self.__cog_to_register__.append(value)
                elif isinstance(value, ApplicationSubcommand):
                    value.set_self_argument(self)

    @property
    def to_register(self) -> List[ApplicationCommand]:
        return self.__cog_to_register__

    @classmethod
    def _get_overridden_method(cls, method: FuncT) -> Optional[FuncT]:
        """Return None if the method is not overridden. Otherwise returns the overridden method."""
        return getattr(method.__func__, "__cog_special_method__", method)

    @_cog_special_method
    def cog_application_command_check(self, interaction: Interaction) -> bool:
        """A special method that registers as a :func:`.ext.application_checks.check`
        for every application command and subcommand in this cog.

        This function **can** be a coroutine and must take a sole parameter,
        ``interaction``, to represent the :class:`.Interaction`.
        """
        return True

    @_cog_special_method
    async def cog_application_command_before_invoke(
        self, interaction: Interaction
    ) -> None:
        """A special method that acts as a cog local pre-invoke hook.

        This is similar to :meth:`.ApplicationCommand.before_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        interaction: :class:`.Interaction`
            The invocation interaction.
        """
        pass

    @_cog_special_method
    async def cog_application_command_after_invoke(
        self, interaction: Interaction
    ) -> None:
        """A special method that acts as a cog local post-invoke hook.

        This is similar to :meth:`.Command.after_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        interaction: :class:`.Interaction`
            The invocation interaction.
        """
        pass


# Extends Any so that type checkers won't complain that it's a default for a parameter of a different type
class SlashOption(_SlashOptionMetaBase):
    """Provides Discord with information about an option in a command.

    When this class is set as the default argument of a parameter in an Application Command, additional information
    about the parameter is sent to Discord for the user to see.

    Parameters
    ----------
    name: :class:`str`
        The name of the Option that users will see. If not specified, it defaults to the parameter name.
    description: :class:`str`
        The description of the Option that users will see. If not specified, the docstring will be used. If no docstring is found for the
        parameter, it defaults to "No description provided".
    required: :class:`bool`
        If a user is required to provide this argument before sending the command. Defaults to Discords choice. (False at this time)
    choices: Union[Dict[:class:`str`, Union[:class:`str`, :class:`int`, :class:`float`]], Iterable[Union[:class:`str`, :class:`int`, :class:`float`]]]
        A list of choices that a user must choose.
        If a :class:`dict` is given, the keys are what the users are able to see, the values are what is sent back
        to the bot.
        Otherwise, it is treated as an `Iterable` where what the user sees and is sent back to the bot are the same.
    channel_types: List[:class:`ChannelType`]
        List of `ChannelType` enums, limiting the users choice to only those channel types. The parameter must be
        typed as :class:`GuildChannel` for this to function.
    min_value: Union[:class:`int`, :class:`float`]
        Minimum integer or floating point value the user is allowed to input. The parameter must be typed as an
        :class:`int` or :class:`float` for this to function.
    max_value: Union[:class:`int`, :class:`float`]
        Maximum integer or floating point value the user is allowed to input. The parameter must be typed as an
        :class:`int` or :class:`float` for this to function.
    autocomplete: :class:`bool`
        If this parameter has an autocomplete function decorated for it. If unset, it will automatically be `True`
        if an autocomplete function for it is found.
    default: Any
        When required is not True and the user doesn't provide a value for this Option, this value is given instead.
    verify: :class:`bool`
        If True, the given values will be checked to ensure that the payload to Discord is valid.
    """

    def __init__(
        self,
        name: str = MISSING,
        description: str = MISSING,
        required: bool = MISSING,
        # choices: Dict[str, Union[str, int, float]] = MISSING,
        choices: Union[
            Dict[str, Union[str, int, float]], Iterable[Union[str, int, float]]
        ] = MISSING,
        channel_types: List[ChannelType] = MISSING,
        min_value: Union[int, float] = MISSING,
        max_value: Union[int, float] = MISSING,
        autocomplete: bool = MISSING,
        default: Any = None,
        verify: bool = True,
    ):
        self.name: Optional[str] = name
        self.description: Optional[str] = description
        self.required: Optional[bool] = required
        self.choices: Optional[Union[Iterable, dict]] = choices
        self.channel_types: Optional[List[ChannelType]] = channel_types
        self.min_value: Optional[Union[int, float]] = min_value
        self.max_value: Optional[Union[int, float]] = max_value
        self.autocomplete: Optional[bool] = autocomplete
        self.default: Any = default
        self._verify = verify
        if self._verify:
            self.verify()

    def verify(self) -> bool:
        """Checks if the given values conflict with one another or are invalid."""
        # Incompatible according to Discord Docs.
        if self.choices and self.autocomplete:
            raise ValueError(
                "Autocomplete may not be set to true if choices are present."
            )
        return True


class CommandOption(SlashOption):
    """Represents a Python function parameter that corresponds to a Discord Option.

    This must set and/or handle all variables from SlashOption, hence the subclass.
    This should not be created by the user, only by other Application Command-related classes.

    Parameters
    ----------
    parameter: :class:`inspect.Parameter`
        The Application Command Parameter object to read and make usable by Discord.
    """

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
        Message: ApplicationCommandOptionType.integer,  # TODO: This is janky, the user provides an ID or something? Ugh.
        Attachment: ApplicationCommandOptionType.attachment,
    }
    """Maps Python annotations/typehints to Discord Application Command type values."""

    def __init__(self, parameter: Parameter, command: ApplicationSubcommand):
        super().__init__()
        self.parameter = parameter
        self.command = command
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
        # Set required to False if an Optional[...] or Union[..., None] type annotation is given.
        self.required = (
            False if type(None) in typing.get_args(parameter.annotation) else MISSING
        )
        # Override self.required if it was set in the command argument.
        if cmd_arg.required is not MISSING:
            self.required = cmd_arg.required
        self.choices = cmd_arg.choices or MISSING
        self.channel_types = cmd_arg.channel_types or MISSING
        # min_value of 0 will cause an `or` to give the variable MISSING
        self.min_value = (
            cmd_arg.min_value if cmd_arg.min_value is not MISSING else MISSING
        )
        # max_value of 0 will cause an `or` to give the variable MISSING
        self.max_value = (
            cmd_arg.max_value if cmd_arg.max_value is not MISSING else MISSING
        )
        # autocomplete set to False will cause an `or` to give the variable MISSING
        self.autocomplete = (
            cmd_arg.autocomplete if cmd_arg.autocomplete is not MISSING else MISSING
        )

        if not cmd_arg_given and parameter.default is not parameter.empty:
            # If the parameter default is not a SlashOption, it should be set as the default.
            self.default = parameter.default
        else:
            self.default = cmd_arg.default

        self.autocomplete_function: Optional[Callable] = MISSING
        self.type: ApplicationCommandOptionType = self.get_type(parameter.annotation)

        if cmd_arg._verify:
            self.verify()

    # Basic getters and setters.

    @property
    def description(self) -> str:
        """
        Returns the description of the command. If the description is MISSING, the docstring will be used.
        If no docstring is found for the command callback, it defaults to "No description provided".
        """
        if self._description is not MISSING:
            return self._description
        elif docstring := self.command._parsed_docstring["args"].get(self.name):
            return docstring
        else:
            return "No description provided"
            

    @description.setter
    def description(self, value: str):
        self._description = value

    def get_type(self, param_typing: type) -> ApplicationCommandOptionType:
        """Translates a Python or Nextcord :class:`type` into a Discord typing.
        Parameters
        ----------
        param_typing: :class:`type`
            Python or Nextcord type to translate.
        Returns
        -------
        :class:`ApplicationCommandOptionType`
            Enum with a value corresponding to the given type.
        Raises
        ------
        :class:`NotImplementedError`
            Raised if the given typing cannot be translated to a Discord typing.
        """

        if param_typing is self.parameter.empty:
            return ApplicationCommandOptionType.string
        elif valid_type := self.option_types.get(param_typing, None):
            return valid_type
        # If the typing is Optional[...] or Union[..., None], get the type of the first non-None type.
        elif (
            type(None) in typing.get_args(param_typing)
            and (
                inner_type := find(
                    lambda t: t is not type(None), typing.get_args(param_typing)
                )
            )
            and (valid_type := self.option_types.get(inner_type, None))
        ):
            return valid_type
        else:
            raise NotImplementedError(
                f'Type "{param_typing}" isn\'t a supported typing for Application Commands.'
            )

    def verify(self) -> None:
        """This should run through :class:`SlashOption` variables and raise errors when conflicting data is given."""
        super().verify()
        if self.channel_types and self.type is not ApplicationCommandOptionType.channel:
            raise ValueError(
                "channel_types can only be given when the var is typed as nextcord.abc.GuildChannel"
            )
        if self.min_value is not MISSING and type(self.min_value) not in (int, float):
            raise ValueError("min_value must be an int or float.")
        if self.max_value is not MISSING and type(self.max_value) not in (int, float):
            raise ValueError("max_value must be an int or float.")
        if (
            self.min_value is not MISSING or self.max_value is not MISSING
        ) and self.type not in (
            ApplicationCommandOptionType.integer,
            ApplicationCommandOptionType.number,
        ):
            raise ValueError(
                "min_value or max_value can only be set if the type is integer or number."
            )

    async def handle_slash_argument(
        self, state: ConnectionState, argument: Any, interaction: Interaction
    ) -> Any:
        """Handles arguments, specifically for Slash Commands."""
        if self.type is ApplicationCommandOptionType.channel:
            return state.get_channel(int(argument))
        elif self.type is ApplicationCommandOptionType.user:
            user_id = int(argument)
            ret = (
                interaction.guild.get_member(user_id)
                if interaction.guild
                else state.get_user(user_id)
            )
            if ret:
                return ret
            else:
                # Return a Member object if the required data is available, otherwise fallback to User.
                if "members" in interaction.data["resolved"] and (
                    interaction.guild,
                    interaction.guild_id,
                ):
                    resolved_members_payload = interaction.data["resolved"]["members"]
                    resolved_members: Dict[int, Member] = {}
                    guild = interaction.guild or state._get_guild(interaction.guild_id)
                    # Because we modify the payload further down,
                    # a copy is made to avoid affecting methods that read the interaction data ahead of this function.
                    for (
                        member_id,
                        member_payload,
                    ) in resolved_members_payload.copy().items():
                        member = guild.get_member(int(member_id))
                        # Can't find the member in cache, let's construct one.
                        if not member:
                            user_payload = interaction.data["resolved"]["users"][
                                member_id
                            ]
                            # This is required to construct the Member.
                            member_payload["user"] = user_payload
                            member = Member(
                                data=member_payload, guild=guild, state=state
                            )
                            guild._add_member(member)

                        resolved_members[member.id] = member

                    return resolved_members[user_id]
                else:
                    # The interaction data gives a dictionary of resolved users, best to use it if cache isn't available.
                    resolved_users_payload = interaction.data["resolved"]["users"]
                    resolved_users = {
                        int(raw_id): state.store_user(user_payload)
                        for raw_id, user_payload in resolved_users_payload.items()
                    }
                    return resolved_users[user_id]

        elif self.type is ApplicationCommandOptionType.role:
            return interaction.guild.get_role(int(argument))
        elif self.type is ApplicationCommandOptionType.integer:
            return int(argument)
        elif self.type is ApplicationCommandOptionType.number:
            return float(argument)
        elif self.type is Message:  # TODO: This is mostly a workaround for Message commands, switch to handles below.
            return state._get_message(int(argument))
        elif self.type is ApplicationCommandOptionType.attachment:
            resolved_attachment_data: dict = interaction.data["resolved"][
                "attachments"
            ][argument]
            return Attachment(data=resolved_attachment_data, state=state)
        return argument

    async def handle_message_argument(
        self, state: ConnectionState, argument: Any, interaction: Interaction
    ):
        """For possible future use, will handle arguments specific to Message Commands (Context Menu type.)"""
        raise NotImplementedError  # TODO: Even worth doing? We pass in what we know already.

    async def handle_user_argument(
        self, state: ConnectionState, argument: Any, interaction: Interaction
    ):
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
        ret = {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
        }
        # False is included in this because that's the default for Discord currently. Not putting in the required param
        # when possible minimizes the payload size and makes checks between registered and found commands easier.
        if self.required:
            ret["required"] = self.required
        elif self.required is False:
            pass  # Discord doesn't currently provide Required if it's False due to it being default.
        elif self.required is MISSING and self.default:
            pass  # If required isn't explicitly set and a default exists, don't say that this param is required.
        else:
            # While this violates Discord's default and our goal (not specified should return minimum or nothing), a
            # parameter being optional by default goes against traditional programming. A parameter not explicitly
            # stated to be optional should be required.
            ret["required"] = True

        if self.choices:
            # Discord returns the names as strings, might as well do it here so payload comparison is easy.
            if isinstance(self.choices, dict):
                ret["choices"] = [
                    {"name": str(key), "value": value}
                    for key, value in self.choices.items()
                ]
            else:
                ret["choices"] = [
                    {"name": str(value), "value": value} for value in self.choices
                ]
        if self.channel_types:
            # noinspection PyUnresolvedReferences
            ret["channel_types"] = [
                channel_type.value for channel_type in self.channel_types
            ]
        # We don't ask for the payload if we have options, so no point in checking for options.
        if self.min_value is not MISSING:
            ret["min_value"] = self.min_value
        if self.max_value is not MISSING:
            ret["max_value"] = self.max_value
        if self.autocomplete is not MISSING:
            ret["autocomplete"] = self.autocomplete
        return ret


class ApplicationSubcommand:
    """Represents an application subcommand attached to a callback.

    Parameters
    ----------
    callback: Callable
        Function/method to call when the subcommand is triggered.
    parent_command: Optional[Union[:class:`ApplicationCommand`, :class:`ApplicationSubcommand`]]
        Application (sub)command that has this subcommand as its child.
    cmd_type: Optional[Union[:class:`ApplicationCommandType`, :class:`ApplicationCommandOptionType`]]
        Specific type of subcommand this should be.
    self_argument: Union[:class:`ClientCog`, Any]
        Object to pass as `self` to the callback. If not set, the callback will not be given a `self` argument.
    name: :class:`str`
        The name of the subcommand that users will see. If not set, the name of the callback will be used.
    description: :class:`str`
        The description of the subcommand that users will see. If not specified, the docstring will be used.
        If no docstring is found for the subcommand callback, it defaults to "No description provided".
    """

    def __init__(
        self,
        callback: Callable = MISSING,
        parent_command: Optional[
            Union[ApplicationCommand, ApplicationSubcommand]
        ] = MISSING,
        cmd_type: Optional[
            Union[ApplicationCommandType, ApplicationCommandOptionType]
        ] = MISSING,
        self_argument: Union[ClientCog, Any] = MISSING,
        name: str = MISSING,
        description: str = MISSING,
        inherit_hooks: bool = False,
    ):
        # TODO: Add verification against vars if callback is added later.
        self._callback: Optional[Callable] = None
        self.parent_command: Optional[
            Union[ApplicationCommand, ApplicationSubcommand]
        ] = parent_command
        self.type: Optional[ApplicationCommandOptionType] = cmd_type
        self._self_argument: Optional[ClientCog] = self_argument
        self.name: Optional[str] = name
        self._description: str = description
        self._parsed_docstring: Optional[Dict[str, Any]] = None

        self.options: Dict[str, CommandOption] = {}
        self.children: Dict[str, ApplicationSubcommand] = {}

        self.on_error: Optional[ApplicationErrorCallback] = None
        if parent_command is not MISSING and getattr(parent_command, "on_error", False):
            self.on_error = parent_command.on_error

        # self._on_autocomplete: Dict[str, Callable] = {}  # TODO: Maybe move the callbacks into the CommandOptions?

        if callback:
            self._from_callback(callback)

        self.checks: List[ApplicationCheck] = []
        self._application_command_before_invoke: ApplicationHook = None
        self._application_command_after_invoke: ApplicationHook = None

        try:
            checks = callback.__slash_command_checks__
            checks.reverse()
        except AttributeError:
            pass
        else:
            self.checks.extend(checks)

        if inherit_hooks and parent_command is not MISSING:
            self.checks.extend(parent_command.checks)

            self._application_command_before_invoke: Optional[
                ApplicationHook
            ] = parent_command._application_command_before_invoke
            self._application_command_after_invoke: Optional[
                ApplicationHook
            ] = parent_command._application_command_after_invoke
        else:
            try:
                before_invoke = callback.__application_command_before_invoke__
            except AttributeError:
                pass
            else:
                self._application_command_before_invoke = before_invoke

            try:
                after_invoke = callback.__application_command_after_invoke__
            except AttributeError:
                pass
            else:
                self._application_command_after_invoke = after_invoke

    # Simple-ish getter + setters methods.

    @property
    def error_name(self) -> str:
        return f"{self.__class__.__name__} {self.name} {self.callback}"

    @property
    def description(self) -> str:
        """
        Returns the description of the command. If the description is MISSING, the docstring will be used.
        If no docstring is found for the command callback, it defaults to "No description provided".
        """
        if self._description is not MISSING:
            return self._description
        elif docstring := self._parsed_docstring["description"]:
            return docstring
        else:
            return "No description provided"

    @description.setter
    def description(self, new_desc: str):
        self._description = new_desc

    @property
    def callback(self) -> Optional[Callable]:
        """Returns the callback associated with this ApplicationCommand."""
        return self._callback

    @property
    def full_parent_name(self) -> str:
        """:class:`str`: Retrieves the fully qualified parent command name.

        This the base command name required to execute it. For example,
        in ``/one two three`` the parent name would be ``one two``.
        """
        entries = []
        command = self
        # command.parent is type-hinted as GroupMixin some attributes are resolved via MRO
        while command.parent_command is not MISSING:  # type: ignore
            command = command.parent_command  # type: ignore
            entries.append(command.name)  # type: ignore

        return " ".join(reversed(entries))

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Retrieves the fully qualified command name.

        This is the full parent name with the command name as well.
        For example, in ``/one two three`` the qualified name would be
        ``one two three``.
        """

        parent = self.full_parent_name
        if parent:
            return parent + " " + self.name
        else:
            return self.name

    def __str__(self) -> str:
        return self.qualified_name

    def set_callback(self, callback: Callable) -> ApplicationSubcommand:
        """Sets the callback associated with this ApplicationCommand."""
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("Callback must be a coroutine.")
        self._callback = callback
        return self

    @property
    def self_argument(self) -> Optional[ClientCog]:
        """Returns the argument used for ``self``. Optional is used because :class:`ClientCog` isn't strictly correct."""
        return self._self_argument

    def set_self_argument(self, self_arg: ClientCog) -> ApplicationSubcommand:
        """Sets the `self` argument, used when the callback is inside a class."""
        self._self_argument = self_arg
        return self

    def add_check(self, func: ApplicationCheck) -> ApplicationSubcommand:
        """Adds a check to the ApplicationCommand.

        This function is idempotent and will not raise an exception if the function is not in the command’s checks.

        Parameters
        ----------
        func
            The function that will be used as a check.
        """
        self.checks.append(func)
        return self

    def remove_check(self, func: ApplicationCheck) -> ApplicationSubcommand:
        """Removes a check from the ApplicationCommand.

        This function is idempotent and will not raise an exception
        if the function is not in the command's checks.

        Parameters
        ----------
        func
            The function to remove from the checks.
        """

        try:
            self.checks.remove(func)
        except ValueError:
            pass

        return self

    def verify_content(self):
        """This verifies the content of the subcommand and raises errors for violations."""
        if not self.callback:
            raise ValueError(f"{self.error_name} No callback assigned!")
        if not self.type:
            raise ValueError(f"{self.error_name} Subcommand type needs to be set.")
        if self.type not in (
            ApplicationCommandOptionType.sub_command,
            ApplicationCommandOptionType.sub_command_group,
        ):
            raise ValueError(
                f"{self.error_name} Command type is not set to a valid type, it needs to be a sub_command "
                f"or sub_command_group."
            )
        if (
            self.type is not ApplicationCommandOptionType.sub_command_group
            and self.children
        ):
            raise ValueError(
                f"{self.error_name} Command type needs to be sub_command_group to have subcommands."
            )
        if (
            self.parent_command
            and self.type is ApplicationCommandOptionType.sub_command_group
            and self.parent_command.type
            is ApplicationCommandOptionType.sub_command_group
        ):
            raise NotImplementedError(
                f"{self.error_name} Discord has not implemented subcommands more than 2 levels "
                f"deep."
            )
        for option in self.options.values():
            if option.autocomplete:
                if not option.autocomplete_function:
                    raise ValueError(
                        f"{self.error_name} Kwarg {option.functional_name} has autocomplete enabled, but "
                        f"no on_autocomplete assigned."
                    )
                # While we could check if it has autocomplete disabled but an on_autocomplete function, why should we
                # bother people who are likely reworking their code? It also doesn't break anything.

    # Shortcuts for ApplicationSubcommand creation.

    @classmethod
    def from_callback(cls, callback: Callable) -> ApplicationSubcommand:
        """Returns an ApplicationSubcommand object created from the given callback."""
        return cls()._from_callback(callback)

    def _from_callback(self, callback: Callable) -> ApplicationSubcommand:
        """Internal method for returning an ApplicationSubcommand object created from the given callback."""
        # TODO: Add kwarg support.
        # ret = ApplicationSubcommand()
        self.set_callback(callback)
        self._parsed_docstring = parse_docstring(callback, _MAX_COMMAND_DESCRIPTION_LENGTH)
        if not self.name:
            self.name = self.callback.__name__
        first_arg = True

        typehints = typing.get_type_hints(callback)
        for name, param in signature(self.callback).parameters.items():
            # TODO: What kind of hardcoding is this, figure out a better way for self!
            self_skip = name == "self"
            if first_arg:
                if not self_skip:
                    first_arg = False
            else:
                if isinstance(param.annotation, str):
                    # Thank you Disnake for the guidance to use this.
                    param = param.replace(annotation=typehints.get(name, param.empty))
                arg = CommandOption(param, self)
                self.options[arg.name] = arg
        return self

    # Data wrangling.

    @property
    def payload(self) -> dict:
        """Verifies the content of the ApplicationSubommand then constructs and returns the payload for this subcommand.
        This does not return a complete application command payload for Discord, only the subcommand portion of it.
        Returns
        -------
        :class:`dict`
            Dictionary payload of the subcommand.
        """
        self.verify_content()
        ret = {
            "type": self.type.value,
            # Might as well stringify the name, will come in handy if people try using numbers
            "name": str(self.name),
            "description": self.description,
        }
        if self.children:
            ret["options"] = [child.payload for child in self.children.values()]
        elif self.options:
            ret["options"] = [argument.payload for argument in self.options.values()]
        return ret

    @property
    def cog_application_command_before_invoke(self) -> Optional[ApplicationHook]:
        """Returns the cog_application_command_before_invoke method for the cog that this command is in. Returns ``None`` if not the method is not found."""
        if not self._self_argument:
            return None

        return ClientCog._get_overridden_method(
            self._self_argument.cog_application_command_before_invoke
        )

    @property
    def cog_application_command_after_invoke(self) -> Optional[ApplicationHook]:
        """Returns the cog_application_command_after_invoke method for the cog that this command is in. Returns ``None`` if not the method is not found."""
        if not self._self_argument:
            return None

        return ClientCog._get_overridden_method(
            self._self_argument.cog_application_command_after_invoke
        )

    # Methods that can end up running the callback.

    async def call_autocomplete(
        self, state, interaction: Interaction, option_data: List[Dict[str, Any]]
    ) -> None:
        """|coro|

        This will route autocomplete data as needed, either handing it off to subcommands or calling one of the
        autocomplete callbacks registered.

        Parameters
        ----------
        state: :class:`ConnectionState`
            State to grab cached objects from.
        interaction: :class:`Interaction`
            Interaction associated with the autocomplete event.
        option_data: List[Dict[:class:`str`, Any]]
            List of raw option data from Discord.
        """
        # If this has subcommands, it needs to be forwarded to them to handle.
        if self.children:
            await self.children[option_data[0]["name"]].call_autocomplete(
                state, interaction, option_data[0].get("options", {})
            )
        elif self.type in (
            ApplicationCommandType.chat_input,
            ApplicationCommandOptionType.sub_command,
        ):
            focused_option_name = None
            for arg in option_data:
                if arg.get("focused", None) is True:
                    if focused_option_name:
                        raise ValueError(
                            "Multiple options are focused, is that supposed to be possible?"
                        )
                    focused_option_name = arg["name"]

            if not focused_option_name:
                raise ValueError(
                    "There's supposed to be a focused option, but it's not found?"
                )
            focused_option = self.options[focused_option_name]
            if focused_option.autocomplete_function is MISSING:
                raise ValueError(
                    f"{self.error_name} Autocomplete called for option {focused_option.functional_name} "
                    f"but it doesn't have an autocomplete function?"
                )
            autocomplete_kwargs = signature(
                focused_option.autocomplete_function
            ).parameters.keys()
            kwargs = {}
            uncalled_options = self.options.copy()
            uncalled_options.pop(focused_option.name)
            focused_option_value = None
            for arg_data in option_data:
                if option := uncalled_options.get(arg_data["name"], None):
                    uncalled_options.pop(option.name)
                    if option.functional_name in autocomplete_kwargs:
                        kwargs[
                            option.functional_name
                        ] = await option.handle_slash_argument(
                            state, arg_data["value"], interaction
                        )
                elif arg_data["name"] == focused_option.name:
                    focused_option_value = await focused_option.handle_slash_argument(
                        state, arg_data["value"], interaction
                    )
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
            value = await self.invoke_autocomplete(
                interaction, focused_option, focused_option_value, **kwargs
            )
            # Handles when the autocomplete callback returns something and didn't run the autocomplete function.
            if value and not interaction.response.is_done():
                await interaction.response.send_autocomplete(value)
        else:
            raise TypeError(
                f"{self.error_name} Autocomplete is not handled by this type of command."
            )

    def has_error_handler(self) -> bool:
        """:class:`bool`: Checks whether the command has an error handler registered."""
        return self.on_error is not None

    async def invoke_autocomplete(
        self,
        interaction: Interaction,
        focused_option: CommandOption,
        focused_option_value: Any,
        **kwargs,
    ) -> Any:
        """|coro|
        Invokes the autocomplete callback of the given option.

        The given interaction, focused option value, and any other kwargs are forwarded to the autocomplete function.
        If this command was given a self argument, it will be forwarded in first.

        Parameters
        ----------
        interaction: :class:`Interaction`
            Interaction associated with the autocomplete event.
        focused_option: :class:`CommandOption`
            The command option to call the autocomplete callback from.
        focused_option_value: Any
            Focused option value to forward to the autocomplete callback.
        kwargs:
            Keyword arguments to forward to the autocomplete callback.
        """
        if self._self_argument:
            return await focused_option.autocomplete_function(
                self._self_argument, interaction, focused_option_value, **kwargs
            )
        else:
            return await focused_option.autocomplete_function(
                interaction, focused_option_value, **kwargs
            )

    async def call(
        self,
        state: ConnectionState,
        interaction: Interaction,
        option_data: List[Dict[str, Any]],
    ) -> None:
        """|coro|
        Calls the callback and its hooks associated with this command with the given interaction and option data.

        Parameters
        ----------
        state: :class:`ConnectionState`
            State to grab cached objects from.
        interaction: :class:`Interaction`
            Interaction associated with the application command event.
        option_data: List[Dict[:class:`str`, Any]]
            List of raw option data from Discord.
        """
        app_cmd, new_option_data = self._find_subcommand(option_data)

        await self._call_with_hooks(
            state,
            interaction,
            app_cmd,
            app_cmd.call_invoke_slash,
            (state, interaction, new_option_data),
        )

    async def _call_with_hooks(
        self,
        state: ConnectionState,
        interaction: Interaction,
        app_cmd: Union[ApplicationSubcommand, ApplicationCommand],
        callback: Callable,
        args: Tuple[Any, ...],
    ) -> None:
        interaction._set_application_command(app_cmd)

        try:
            can_run = await app_cmd.application_command_can_run(interaction)
        except Exception as error:
            state.dispatch("application_command_error", interaction, error)
            await app_cmd.invoke_error(interaction, error)
            return

        if can_run:
            if app_cmd._application_command_before_invoke is not None:
                await app_cmd._application_command_before_invoke(interaction)

            cog_application_command_before_invoke = (
                app_cmd.cog_application_command_before_invoke
            )
            if cog_application_command_before_invoke is not None:
                await cog_application_command_before_invoke(interaction)

            if state._application_command_before_invoke is not None:
                await state._application_command_before_invoke(interaction)

            invoke_error = None
            try:
                await callback(*args)
            except Exception as error:
                state.dispatch(
                    "application_command_error",
                    interaction,
                    ApplicationInvokeError(error),
                )
                await app_cmd.invoke_error(interaction, error)
            finally:
                if app_cmd._application_command_after_invoke is not None:
                    await app_cmd._application_command_after_invoke(interaction)

                cog_application_command_after_invoke = (
                    app_cmd.cog_application_command_after_invoke
                )
                if cog_application_command_after_invoke is not None:
                    await cog_application_command_after_invoke(interaction)

                if state._application_command_after_invoke is not None:
                    await state._application_command_after_invoke(interaction)

    def _find_subcommand(
        self, option_data: List[Dict[str, Any]]
    ) -> Tuple[Union[ApplicationSubcommand, ApplicationCommand], List[Dict[str, Any]]]:
        if self.children:
            # Discord currently does not allow commands that have subcommands to be run. Therefore, if a command has
            # children, a subcommand must be being called.
            return self.children[option_data[0]["name"]]._find_subcommand(
                option_data[0].get("options", {})
            )
        elif self.type in (
            ApplicationCommandType.chat_input,
            ApplicationCommandOptionType.sub_command,
        ):
            # Slash commands are able to have subcommands, therefore that is handled here.
            return self, option_data
        else:
            # Anything that can't be handled in here should be raised for ApplicationCommand to handle.
            # TODO: Figure out how to hide this in exception trace log, people don't need to see it.
            raise InvalidCommandType(
                f"{self.type} is not a handled Application Command type."
            )

    async def call_invoke_slash(
        self,
        state: ConnectionState,
        interaction: Interaction,
        option_data: List[Dict[str, Any]],
    ) -> None:
        """|coro|
        Calls the callback associated with this command specifically for slash with the given interaction and option
        data.

        Parameters
        ----------
        state: :class:`ConnectionState`
            State to grab cached objects from.
        interaction: :class:`Interaction`
            Interaction associated with the application command event.
        option_data: List[Dict[:class:`str`, Any]]
            List of raw option data from Discord.
        """
        kwargs = {}
        uncalled_args = self.options.copy()
        for arg_data in option_data:
            if arg_data["name"] in uncalled_args:
                uncalled_args.pop(arg_data["name"])
                kwargs[
                    self.options[arg_data["name"]].functional_name
                ] = await self.options[arg_data["name"]].handle_slash_argument(
                    state, arg_data["value"], interaction
                )
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

    async def invoke_error(
        self, interaction: Interaction, error: ApplicationError
    ) -> None:

        if self.has_error_handler():
            if self._self_argument:
                await self.on_error(self._self_argument, interaction, error)
            else:
                await self.on_error(interaction, error)

    async def application_command_can_run(self, interaction: Interaction) -> bool:
        """|coro|

        Checks if the command can be executed by checking all the predicates
        inside the :attr:`~ApplicationCommand.checks` attribute, as well as all global and cog checks.

        Parameters
        -----------
        interaction: :class:`.Interaction`
            The interaction of the command currently being invoked.

        Raises
        -------
        :class:`ApplicationError`
            Any application command error that was raised during a check call will be propagated
            by this function.

        Returns
        --------
        :class:`bool`
            A boolean indicating if the command can be invoked.
        """
        # Global checks
        for check in interaction.client._connection._application_command_checks:
            try:
                check_result = await maybe_coroutine(check, interaction)
            # To catch any subclasses of ApplicationCheckFailure.
            except ApplicationCheckFailure:
                raise
            # If the check returns False, the command can't be run.
            else:
                if not check_result:
                    error = ApplicationCheckFailure(
                        f"The global check functions for application command {self.qualified_name} failed."
                    )
                    raise error

        # Cog check
        if self._self_argument:
            cog_check = ClientCog._get_overridden_method(
                self._self_argument.cog_application_command_check
            )
            if cog_check is not None and not await maybe_coroutine(
                cog_check, interaction
            ):
                raise ApplicationCheckFailure(
                    f"The cog check functions for application command {self.qualified_name} failed."
                )

        # Command checks
        for check in self.checks:
            try:
                check_result = await maybe_coroutine(check, interaction)
            # To catch any subclasses of ApplicationCheckFailure.
            except ApplicationCheckFailure as error:
                raise
            # If the check returns False, the command can't be run.
            else:
                if not check_result:
                    error = ApplicationCheckFailure(
                        f"The check functions for application command {self.qualified_name} failed."
                    )
                    raise error

        return True

    async def invoke_slash(self, interaction: Interaction, **kwargs) -> None:
        """|coro|
        Invokes the callback associated with this command specifically for slash with the given interaction and keyword
        arguments.

        Parameters
        ----------
        interaction: :class:`Interaction`
            Interaction associated with the autocomplete event.
        kwargs:
            Keyword arguments to forward to the callback.
        """
        if self._self_argument:
            await self.callback(self._self_argument, interaction, **kwargs)
        else:
            await self.callback(interaction, **kwargs)

    # Decorators

    def error(self, callback: ApplicationErrorCallback) -> Callable:
        """Decorates a function, setting it as a callback to be called when a :class:`ApplicationError` or any of its subclasses is raised inside the :class:`ApplicationCommand`.

        Parameters
        ----------
        callback: Callable[[:class:`Interaction`, :class:`ApplicationError`], :class:`asyncio.Awaitable[Any]`]
            The callback to call when an error occurs.
        """
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("The error handler must be a coroutine.")

        self.on_error = callback
        return callback

    def on_autocomplete(self, on_kwarg: str) -> Callable:
        """Decorates a function, adding it as the autocomplete callback for the given keyword argument that is inside
        the slash command.

        Parameters
        ----------
        on_kwarg: :class:`str`
            Name that corresponds to a keyword argument in the slash command.
        """
        if self.type not in (
            ApplicationCommandType.chat_input,
            ApplicationCommandOptionType.sub_command,
        ):
            # At this time, non-slash commands cannot have autocomplete.
            raise TypeError(f"{self.error_name} {self.type} cannot have autocomplete.")
        found = False
        for name, option in self.options.items():
            if option.functional_name == on_kwarg:
                found = True
                if option.autocomplete is MISSING:
                    # If autocomplete isn't set but they are trying to decorate it, auto-enable it.
                    option.autocomplete = True
                if option.autocomplete:

                    def decorator(func: Callable):
                        option.autocomplete_function = func
                        return func

                    return decorator
                else:
                    raise ValueError(
                        f"{self.error_name} autocomplete for kwarg {on_kwarg} not enabled, cannot add "
                        f"autocomplete function."
                    )
        if found is False:
            raise TypeError(
                f"{self.error_name} kwarg {on_kwarg} not found, cannot add autocomplete function."
            )

    def subcommand(
        self,
        name: str = MISSING,
        description: str = MISSING,
        inherit_hooks: bool = False,
    ) -> Callable:
        """Decorates a function, creating a subcommand with the given kwargs forwarded to it.

        Adding a subcommand will prevent the callback associated with this command from being called.

        Parameters
        ----------
        name: :class:`str`
            The name of the subcommand that users will see. If not set, the name of the callback will be used.
        description: :class:`str`
            The description of the subcommand that users will see. If not specified, the docstring will be used.
            If no docstring is found for the subcommand callback, it defaults to "No description provided".
        inherit_hooks: :class:`bool` default=False
            If ``True`` and this command has a parent :class:`ApplicationCommand` then this command
            will inherit all checks, application_command_before_invoke and application_command_after_invoke's defined on the the :class:`ApplicationCommand`

            .. note::
                Any ``application_command_before_invoke`` or ``application_command_after_invoke``'s defined on this will override parent ones.
        """

        def decorator(func: Callable):
            result = ApplicationSubcommand(
                callback=func,
                parent_command=self,
                cmd_type=ApplicationCommandOptionType.sub_command,
                name=name,
                description=description,
                inherit_hooks=inherit_hooks,
            )
            self.type = ApplicationCommandOptionType.sub_command_group
            self.children[result.name] = result
            return result

        return decorator

    def application_command_before_invoke(
        self, coro: ApplicationHook
    ) -> ApplicationHook:
        """A decorator that registers a coroutine as a pre-invoke hook.

        A pre-invoke hook is called directly before the command is
        called. This makes it a useful function to set up database
        connections or any type of set up required.

        This pre-invoke hook takes a sole parameter, a :class:`.Interaction`.

        See :meth:`.Client.application_command_before_invoke` for more info.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the pre-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("The pre-invoke hook must be a coroutine.")

        self._application_command_before_invoke = coro
        return coro

    def application_command_after_invoke(
        self, coro: ApplicationHook
    ) -> ApplicationHook:
        """A decorator that registers a coroutine as a post-invoke hook.

        A post-invoke hook is called directly after the command is
        called. This makes it a useful function to clean-up database
        connections or any type of clean up required.

        This post-invoke hook takes a sole parameter, a :class:`.Interaction`.

        See :meth:`.Client.application_command_after_invoke` for more info.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the post-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("The post-invoke hook must be a coroutine.")

        self._application_command_after_invoke = coro
        return coro


class ApplicationCommand(ApplicationSubcommand):
    """Represents an application command that can be or is registered with Discord.

    Parameters
    ----------
    callback: Callable
        Function or method to call when the application command is triggered. Must be a coroutine.
    cmd_type: :class:`ApplicationCommandType`
        Type of application command this should be.
    name: :class:`str`
        Name of the command that users will see. If not set, it defaults to the name of the callback.
    description: :class:`str`
        Description of the command that users will see. If not specified, the docstring will be used.
        If no docstring is found for the command callback, it defaults to "No description provided".
    guild_ids: Iterable[:class:`int`]
        IDs of :class:`Guild`'s to add this command to. If unset, this will be a global command.
    default_permission: :class:`bool`
        If users should be able to use this command by default or not. Defaults to Discords default.
    force_global: :class:`bool`
        If True, will force this command to register as a global command, even if `guild_ids` is set. Will still
        register to guilds. Has no effect if `guild_ids` are never set or added to.
    """

    def __init__(
        self,
        callback: Callable = MISSING,
        cmd_type: ApplicationCommandType = MISSING,
        name: str = MISSING,
        description: str = MISSING,
        guild_ids: Iterable[int] = MISSING,
        default_permission: bool = MISSING,
        force_global: bool = False,
        inherit_hooks: bool = False,
    ):
        super().__init__(
            callback=callback, cmd_type=cmd_type, name=name, description=description
        )
        self._state: Optional[ConnectionState] = None
        self.force_global: bool = force_global
        self.default_permission: bool = default_permission or True
        self._guild_ids_to_rollout: Set[int] = set(guild_ids) if guild_ids else set()
        self._guild_ids: Set[int] = set()
        # Guild ID is key (None is global), command ID is value.
        self._command_ids: Dict[Optional[int], int] = {}

    # Simple-ish getter + setters methods.

    @property
    def command_ids(self) -> Dict[Optional[int], int]:
        return self._command_ids

    @property
    def guild_ids(self) -> Tuple[int]:
        # People should not edit this, people are stupid.
        return tuple(self._guild_ids)

    @property
    def guild_ids_to_rollout(self) -> Tuple[int]:
        # I don't want people trying to stupidly edit it. Is that so wrong?
        # This also makes it so the implementation can be changed later and the API technically will not change.
        return tuple(self._guild_ids_to_rollout)

    def add_guild_rollout(self, guild: Union[int, Guild]) -> None:
        """Adds a Guild to the command to be rolled out when the rollout is run.

        Parameters
        ----------
        guild: Union[:class:`int`, :class:`Guild`]
            Guild or Guild ID to add this command to roll out to.
        """
        if isinstance(guild, Guild):
            # I don't like doing `guild = guild.id` and this keeps it extendable.
            guild_id = guild.id
        else:
            guild_id = guild
        self._guild_ids_to_rollout.add(guild_id)

    def remove_guild_rollout(self, guild: Union[int, Guild]) -> None:
        if isinstance(guild, Guild):
            guild_id = guild.id
        else:
            guild_id = guild
        self._guild_ids_to_rollout.remove(guild_id)

    @property
    def description(self) -> str:
        """
        Returns the description of the command. If the description is MISSING, the docstring will be used.
        If no docstring is found for the command callback, it defaults to "No description provided".
        For user and message commands, the description will always be the empty string.
        """
        if self.type in (ApplicationCommandType.user, ApplicationCommandType.message):
            return ""
        return super().description

    @property
    def global_payload(self) -> dict:
        """Returns a global application command payload ready to be sent to Discord."""
        return self._get_basic_application_payload()

    @property
    def is_guild(self) -> bool:
        """Returns True if any guild IDs have been added."""
        return True if (self._guild_ids or self._guild_ids_to_rollout) else False

    @property
    def is_global(self) -> bool:
        """Returns True if either force_global is True or no guild_ids are given."""
        return True if (self.force_global or not self.is_guild) else False

    def set_state(self, state: ConnectionState) -> ApplicationCommand:
        """Sets the ConnectionState object used for getting cached data."""
        self._state = state
        return self

    def get_guild_payload(self, guild_id: int) -> dict:
        """Returns a guild application command payload.

        Parameters
        ----------
        guild_id: :class:`int`
            Discord Guild ID to make the payload for.

        Returns
        -------
        :class:`dict`
            Guild application command payload ready to be serialized and sent to Discord.
        """
        partial_payload = self._get_basic_application_payload()
        partial_payload["guild_id"] = guild_id
        return partial_payload

    def get_signature(
        self, guild_id: Optional[int] = None
    ) -> Tuple[str, int, Optional[int]]:
        """Returns a basic signature for the application command.

        This signature is unique, in the sense that two application commands with the same signature cannot be
        registered with Discord at the same time.

        Parameters
        ----------
        guild_id: Optional[:class:`int`]
            Integer Guild ID for the signature. For a global application command, None is used.

        Returns
        -------
        Tuple[:class:`str`, :class:`int`, Optional[:class:`int`]]
            Name of the application command, :class:`ApplicationCommandType` value, and Guild ID. (None for global)
        """

        """Returns a basic signature for a given Guild ID. If None is given, then it is assumed Global."""
        return self.name, self.type.value, guild_id

    def get_signatures(self) -> Set[Tuple[str, int, Optional[int]]]:
        """Returns all basic signatures for this ApplicationCommand."""
        ret = set()
        if self.is_global:
            ret.add((self.name, self.type.value, None))
        if self.is_guild:
            for guild_id in self.guild_ids:
                ret.add((self.name, self.type.value, guild_id))
        return ret

    def get_rollout_signatures(self) -> Set[Tuple[str, int, Optional[int]]]:
        ret = set()
        if self.is_global:
            ret.add((self.name, self.type.value, None))
        for guild_id in self._guild_ids_to_rollout:
            ret.add((self.name, self.type.value, guild_id))
        return ret

    # Shortcuts for ApplicationCommand creation.

    @classmethod
    def from_callback(cls, callback: Callable) -> ApplicationCommand:
        """Returns an ApplicationCommand object created from the given callback.

        Overridden from ApplicationSubcommand for typing purposes.

        Parameters
        ----------
        callback: Callable
            Function or method to run when the command is called. Must be a coroutine.

        Returns
        -------
        :class:`ApplicationCommand`
            An application command created from the given callback with params set.
        """
        return cls()._from_callback(callback)

    # Data wrangling.

    def parse_discord_response(self, state: ConnectionState, data: dict) -> None:
        self.set_state(state)
        command_id = int(data["id"])
        if guild_id := data.get("guild_id", None):
            guild_id = int(guild_id)
            self._command_ids[guild_id] = command_id
            self._guild_ids.add(guild_id)
            self.add_guild_rollout(guild_id)
        else:
            self._command_ids[None] = command_id

    def _get_basic_application_payload(self) -> dict:
        """Bare minimum payload that both Global and Guild commands can use."""
        payload = super().payload
        if self.type is not ApplicationCommandType.chat_input and "options" in payload:
            payload.pop("options")
        if self.default_permission is not None:
            payload["default_permission"] = self.default_permission
        return payload

    def _handle_resolved_message(self, message_data: dict) -> Message:
        # TODO: This is garbage, find a better way to add a Message to the cache.
        #  It's not that I'm unhappy adding things to the cache, it's having to manually do it like this.
        # The interaction gives us message data, might as well use it and add it to the cache.
        channel, guild = self._state._get_guild_channel(message_data)

        message = Message(channel=channel, data=message_data, state=self._state)
        if cached_message := self._state._get_message(message.id):
            return cached_message
        else:
            if self._state._messages is not None:
                self._state._messages.append(message)
        return message

    def _handle_resolved_user(
        self, resolved_payload: dict, guild: Optional[Guild] = None
    ) -> Union[User, Member]:
        """Takes the raw user data payload from Discord and adds it to the state cache."""  # needs changing?
        user_id, user_payload = list(resolved_payload["users"].items())[0]
        if not guild:
            return self._state.store_user(user_payload)

        member = guild.get_member(int(user_id))
        if not member and "members" in resolved_payload:
            member_payload = list(resolved_payload["members"].values())[0]
            # This is required to construct the Member.
            member_payload["user"] = user_payload
            member = Member(data=member_payload, guild=guild, state=self._state)  # type: ignore
            guild._add_member(member)

        return member

    @property
    def payload(self) -> List[dict]:
        """Returns a list of Discord "Application Command Structure" payloads.

        Returns
        -------
        payloads: List[:class:`dict`]
            Returns a list containing the global command payload, if enabled, and payloads corresponding
            to every guild ID specified.
        """
        # TODO: This always returns a list, should it be "payloads"? Won't override subcommand payload though.
        partial_payload = self._get_basic_application_payload()

        ret = []
        if self.is_guild:
            for guild_id in self.guild_ids:
                # We don't need to make a deep copy as guild_id is on the top layer.
                temp = partial_payload.copy()
                temp["guild_id"] = guild_id
                ret.append(temp)
        if self.is_global:
            ret.append(partial_payload)
        return ret

    def check_against_raw_payload(
        self, raw_payload: dict, guild_id: Optional[int] = None
    ) -> bool:
        """Checks if `self.payload` values match with what the given raw payload has.

        This doesn't make sure they are equal. Instead, this checks if most key:value pairs inside our payload
        also exist inside the raw_payload.

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
        if guild_id:
            cmd_payload = self.get_guild_payload(guild_id)
            if cmd_payload["guild_id"] != int(raw_payload["guild_id"]):
                return False
        else:
            cmd_payload = self.global_payload

        if not check_dictionary_values(
            cmd_payload,
            raw_payload,
            "default_permission",
            "description",
            "type",
            "name",
        ):
            return False

        if len(cmd_payload.get("options", [])) != len(raw_payload.get("options", [])):
            return False

        for cmd_option in cmd_payload.get("options", []):
            # I absolutely do not trust Discord or us ordering things nicely, so check through both.
            found_correct_value = False
            for raw_option in raw_payload.get("options", []):
                if cmd_option["name"] == raw_option["name"]:
                    found_correct_value = True
                    # At this time, ApplicationCommand options are identical between locally-generated payloads and
                    # payloads from Discord. If that were to change, switch from a recursive setup and manually
                    # check_dictionary_values.
                    if not deep_dictionary_check(cmd_option, raw_option):
                        return False
                    break
            if not found_correct_value:
                return False
        return True

    def reverse_check_against_raw_payload(
        self, raw_payload: dict, guild_id: Optional[int] = None
    ) -> bool:
        """Checks if the given raw payload values match with what self.payload has.

        This doesn't make sure they are equal, and works opposite of check_against_raw_payload. This checks if all
        key:value's inside the raw_payload also exist inside one of our payloads.

        Parameters
        ----------
        raw_payload: :class:`dict`
            Dictionary payload to compare against our payloads.
        guild_id: Optional[:class:`int`]
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

    def verify_content(self):
        """This verifies the content of the command and raises errors for violations."""
        if not self.callback and not self.children:
            raise ValueError(f"{self.error_name} No callback assigned!")
        # Note that while having a callback and children is iffy, it's not worth raising an error.
        if not self.type:
            raise ValueError(f"{self.error_name} Command type needs to be set.")
        if not isinstance(self.type, ApplicationCommandType):
            raise ValueError(
                f"{self.error_name} Command type is not set to a valid type."
            )
        if (
            self.type in (ApplicationCommandType.user, ApplicationCommandType.message)
            and self.children
        ):
            raise ValueError(
                f"{self.error_name} This type of command cannot have children."
            )
        if self.description and self.type in (
            ApplicationCommandType.user,
            ApplicationCommandType.message,
        ):
            raise ValueError(
                f"{self.error_name} This type of command cannot have a description."
            )

    # Methods that can end up running the callback.

    async def call_autocomplete_from_interaction(self, interaction: Interaction):
        if not self._state:
            raise NotImplementedError("State hasn't been set, this isn't handled yet!")
        await self.call_autocomplete(
            self._state, interaction, interaction.data.get("options", {})
        )

    async def call_from_interaction(self, interaction: Interaction) -> None:
        if not self._state:
            raise NotImplementedError("State hasn't been set, this isn't handled yet!")
        await self.call(self._state, interaction, interaction.data.get("options", {}))

    async def call(
        self,
        state: ConnectionState,
        interaction: Interaction,
        option_data: List[Dict[str, Any]],
    ) -> None:
        try:
            await super().call(state, interaction, option_data)
            return
        except InvalidCommandType:
            if self.type is ApplicationCommandType.message:
                callback = self.call_invoke_message
            elif self.type is ApplicationCommandType.user:
                callback = self.call_invoke_user
            else:
                raise InvalidCommandType(
                    f"{self.type} is not a handled Application Command type."
                )

        await self._call_with_hooks(state, interaction, self, callback, (interaction,))

    async def call_invoke_message(self, interaction: Interaction) -> None:
        """|coro|
        Calls the callback as a message command using the given interaction.

        Parameters
        ----------
        interaction: :class:`Interaction`
            Interaction to get message data from and pass to the callback.
        """
        # TODO: Look into function arguments being autoconverted and given? Arg typed "Channel" gets filled with the
        #  channel?
        # Is this kinda dumb? Yeah, but at this time it can only return one message.
        message = self._handle_resolved_message(
            list(interaction.data["resolved"]["messages"].values())[0]
        )
        await self.invoke_message(interaction, message)

    async def invoke_message(
        self, interaction: Interaction, message: Message, **kwargs: Dict[Any, Any]
    ) -> None:
        if self._self_argument:
            await self.callback(self._self_argument, interaction, message, **kwargs)
        else:
            await self.callback(interaction, message, **kwargs)

    async def call_invoke_user(self, interaction: Interaction) -> None:
        """|coro|
        Calls the callback as a user command using the given interaction.

        Parameters
        ----------
        interaction: :class:`Interaction`
            Interaction to get user or member data from and pass to the callback.
        """
        # TODO: Look into function arguments being autoconverted and given? Arg typed "Channel" gets filled with the
        #  channel?
        # Is this kinda dumb? Yeah, but at this time it can only return one user.
        guild = interaction.guild or self._state.get_guild(interaction.guild_id)
        user = self._handle_resolved_user(interaction.data["resolved"], guild)
        await self.invoke_user(interaction, user)

    async def invoke_user(
        self,
        interaction: Interaction,
        member: Union[Member, User],
        **kwargs: Dict[Any, Any],
    ) -> None:
        """|coro|
        Invokes the callback with the given interaction, member/user, and any additional kwargs added.

        Parameters
        ----------
        interaction: :class:`Interaction`
            Interaction object to pass to the callback.
        member: Union[:class:`Member`, :class:`User`]
            Member/user object to pass to the callback.
        kwargs
            Any additional keyword arguments to pass to the callback.
        """
        if self._self_argument:
            await self.callback(self._self_argument, interaction, member, **kwargs)
        else:
            await self.callback(interaction, member, **kwargs)

    # Decorators.

    def subcommand(
        self,
        name: str = MISSING,
        description: str = MISSING,
        inherit_hooks: bool = False,
    ) -> Callable:
        """Decorates a function, creating a subcommand with the given kwargs forwarded to it.

        Adding a subcommand will prevent the callback associated with this command from being called.

        Parameters
        ----------
        name: :class:`str`
            The name of the subcommand that users will see. If not set, the name of the callback will be used.
        description: :class:`str`
            The description of the subcommand that users will see. If not specified, the docstring will be used.
            If no docstring is found for the subcommand callback, it defaults to "No description provided".
        inherit_hooks: :class:`bool` default=False
            If ``True`` and this command has a parent :class:`ApplicationCommand` then this command
            will inherit all checks, application_command_before_invoke and application_command_after_invoke's defined on the the :class:`ApplicationCommand`

            .. note::
                Any ``application_command_before_invoke`` or ``application_command_after_invoke``'s defined on this will override parent ones.
        """
        # At this time, non-slash commands cannot have Subcommands.
        if self.type != ApplicationCommandType.chat_input:
            raise TypeError(f"{self.error_name} {self.type} cannot have subcommands.")
        else:

            def decorator(func: Callable):
                result = ApplicationSubcommand(
                    callback=func,
                    parent_command=self,
                    cmd_type=ApplicationCommandOptionType.sub_command,
                    name=name,
                    description=description,
                    inherit_hooks=inherit_hooks,
                )
                self.children[result.name] = result
                return result

            return decorator


def slash_command(
    name: str = MISSING,
    description: str = MISSING,
    guild_ids: Iterable[int] = MISSING,
    default_permission: bool = MISSING,
    force_global: bool = False,
):
    """Creates a Slash application command from the decorated function.
    Used inside :class:`ClientCog`'s or something that subclasses it.

    Parameters
    ----------
    name: :class:`str`
        Name of the command that users will see. If not set, it defaults to the name of the callback.
    description: :class:`str`
        Description of the command that users will see. If not specified, the docstring will be used.
        If no docstring is found for the command callback, it defaults to "No description provided".
    guild_ids: Iterable[:class:`int`]
        IDs of :class:`Guild`'s to add this command to. If unset, this will be a global command.
    default_permission: :class:`bool`
        If users should be able to use this command by default or not. Defaults to Discords default, `True`.
    force_global: :class:`bool`
        If True, will force this command to register as a global command, even if `guild_ids` is set. Will still
        register to guilds. Has no effect if `guild_ids` are never set or added to.
    """

    def decorator(func: Callable) -> ApplicationCommand:
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        app_cmd = ApplicationCommand(
            callback=func,
            cmd_type=ApplicationCommandType.chat_input,
            name=name,
            description=description,
            guild_ids=guild_ids,
            default_permission=default_permission,
            force_global=force_global,
        )
        return app_cmd

    return decorator


def message_command(
    name: str = MISSING,
    guild_ids: Iterable[int] = MISSING,
    default_permission: bool = MISSING,
    force_global: bool = False,
):
    """Creates a Message context command from the decorated function.
    Used inside :class:`ClientCog`'s or something that subclasses it.

    Parameters
    ----------
    name: :class:`str`
        Name of the command that users will see. If not set, it defaults to the name of the callback.
    guild_ids: Iterable[:class:`int`]
        IDs of :class:`Guild`'s to add this command to. If unset, this will be a global command.
    default_permission: :class:`bool`
        If users should be able to use this command by default or not. Defaults to Discords default, `True`.
    force_global: :class:`bool`
        If True, will force this command to register as a global command, even if `guild_ids` is set. Will still
        register to guilds. Has no effect if `guild_ids` are never set or added to.
    """

    def decorator(func: Callable) -> ApplicationCommand:
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        app_cmd = ApplicationCommand(
            callback=func,
            cmd_type=ApplicationCommandType.message,
            name=name,
            guild_ids=guild_ids,
            default_permission=default_permission,
            force_global=force_global,
        )
        return app_cmd

    return decorator


def user_command(
    name: str = MISSING,
    guild_ids: Iterable[int] = MISSING,
    default_permission: bool = MISSING,
    force_global: bool = False,
):
    """Creates a User context command from the decorated function.
    Used inside :class:`ClientCog`'s or something that subclasses it.
    Parameters
    ----------
    name: :class:`str`
        Name of the command that users will see. If not set, it defaults to the name of the callback.
    guild_ids: Iterable[:class:`int`]
        IDs of :class:`Guild`'s to add this command to. If unset, this will be a global command.
    default_permission: :class:`bool`
        If users should be able to use this command by default or not. Defaults to Discords default, `True`.
    force_global: :class:`bool`
        If True, will force this command to register as a global command, even if `guild_ids` is set. Will still
        register to guilds. Has no effect if `guild_ids` are never set or added to.
    """

    def decorator(func: Callable) -> ApplicationCommand:
        if isinstance(func, ApplicationCommand):
            raise TypeError("Callback is already an ApplicationCommandRequest.")
        app_cmd = ApplicationCommand(
            callback=func,
            cmd_type=ApplicationCommandType.user,
            name=name,
            guild_ids=guild_ids,
            default_permission=default_permission,
            force_global=force_global,
        )
        return app_cmd

    return decorator


def check_dictionary_values(dict1: dict, dict2: dict, *keywords) -> bool:
    """Helper function to quickly check if 2 dictionaries share the equal value for the same keyword(s).
    Used primarily for checking against the registered command data from Discord.

    Will not work great if values inside the dictionary can be or are None.
    If both dictionaries lack the keyword(s), it can still return True.

    Parameters
    ----------
    dict1: :class:`dict`
        First dictionary to compare.
    dict2: :class:`dict`
        Second dictionary to compare.
    keywords: :class:`str`
        Words to compare both dictionaries to.

    Returns
    -------
    :class:`bool`
        True if keyword values in both dictionaries match, False otherwise.
    """
    for keyword in keywords:
        if dict1.get(keyword, None) != dict2.get(keyword, None):
            return False
    return True


def deep_dictionary_check(dict1: dict, dict2: dict) -> bool:
    """Used to check if all keys and values between two dicts are equal, and recurses if it encounters a nested dict."""
    if dict1.keys() != dict2.keys():
        return False
    for key in dict1:
        if isinstance(dict1[key], dict) and not deep_dictionary_check(
            dict1[key], dict2[key]
        ):
            return False
        elif dict1[key] != dict2[key]:
            return False
    return True
