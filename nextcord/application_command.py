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
import inspect
import logging
import typing
import warnings
from inspect import Parameter, signature
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import typing_extensions
from typing_extensions import Annotated

from .abc import GuildChannel
from .channel import (
    CategoryChannel,
    DMChannel,
    ForumChannel,
    GroupChannel,
    StageChannel,
    TextChannel,
    VoiceChannel,
)
from .enums import ApplicationCommandOptionType, ApplicationCommandType, ChannelType, Locale
from .errors import (
    ApplicationCheckFailure,
    ApplicationCommandOptionMissing,
    ApplicationError,
    ApplicationInvokeError,
)
from .guild import Guild
from .interactions import Interaction
from .member import Member
from .message import Attachment, Message
from .permissions import Permissions
from .role import Role
from .threads import Thread
from .types.interactions import ApplicationCommandInteractionData
from .types.member import MemberWithUser
from .user import User
from .utils import MISSING, find, maybe_coroutine, parse_docstring

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.checks import ApplicationCheck, ApplicationErrorCallback, ApplicationHook
    from .types.interactions import ApplicationCommand as ApplicationCommandPayload

    _CustomTypingMetaBase = Any
else:
    _CustomTypingMetaBase = object

__all__ = (
    "CallbackWrapper",
    "ApplicationCommandOption",
    "BaseCommandOption",
    "OptionConverter",
    "ClientCog",
    "CallbackMixin",
    "SlashOption",
    "SlashCommandOption",
    "BaseApplicationCommand",
    "SlashApplicationSubcommand",
    "SlashApplicationCommand",
    "UserApplicationCommand",
    "MessageApplicationCommand",
    "slash_command",
    "message_command",
    "user_command",
    "Mentionable",
)

_log = logging.getLogger(__name__)

# Maximum allowed length of a command or option description
_MAX_COMMAND_DESCRIPTION_LENGTH = 100
# Description to use for slash commands when the user doesn't provide one.
DEFAULT_SLASH_DESCRIPTION = "No description provided."

T = TypeVar("T")
FuncT = TypeVar("FuncT", bound=Callable[..., Any])


def _cog_special_method(func: FuncT) -> FuncT:
    func.__cog_special_method__ = None
    return func


class CallbackWrapper:
    """A class used to wrap a callback in a sane way to modify aspects of application commands.

    By creating a decorator that makes this class wrap a function or an application command, you can easily modify
    attributes of the command regardless if this wraps the callback or the application command, and without needing
    to make the application command object interpret arbitrarily set function attributes.

    The ``modify`` method must be overridden.

    This handles both multiple layers of wrappers, or if it wraps around a :class:`BaseApplicationCommand`

    Parameters
    ----------
    callback: Union[Callable, :class:`CallbackWrapper`, :class:`BaseApplicationCommand`]
        Callback, other callback wrapper, or application command to wrap and/or modify.

    Examples
    --------
    Creating a decorator that makes the description of the command uppercase, and offers an "override" argument: ::

        def upper_description(description_override: str = None):
            class UpperDescription(CallbackWrapper):
                def modify(self, app_cmd):
                    if description_override is not None:
                        app_cmd.description = description_override.upper()
                    elif app_cmd.description:
                        app_cmd.description = app_cmd.description.upper()

            def wrapper(func):
                return UpperDescription(func)

            return wrapper

        @client.slash_command(description="This will be made uppercase.")
        @upper_description()
        async def test(interaction):
            await interaction.send("The description of this command should be in all uppercase!")
    """

    def __new__(
        cls,
        callback: Union[
            Callable, CallbackWrapper, BaseApplicationCommand, SlashApplicationSubcommand
        ],
        *args,
        **kwargs,
    ) -> Union[CallbackWrapper, BaseApplicationCommand, SlashApplicationSubcommand]:
        wrapper = super(CallbackWrapper, cls).__new__(cls)
        wrapper.__init__(callback, *args, **kwargs)
        if isinstance(callback, (BaseApplicationCommand, SlashApplicationSubcommand)):
            callback.modify_callbacks.extend(wrapper.modify_callbacks)
            return callback
        else:
            return wrapper

    def __init__(self, callback: Union[Callable, CallbackWrapper], *args, **kwargs) -> None:
        # noinspection PyTypeChecker
        self.callback: Optional[Callable] = None
        self.modify_callbacks: List[Callable] = [self.modify]
        if isinstance(callback, CallbackWrapper):
            self.callback = callback.callback
            self.modify_callbacks += callback.modify_callbacks
        else:
            self.callback = callback

    def modify(self, app_cmd: BaseApplicationCommand):
        raise NotImplementedError


class CallbackWrapperMixin:
    def __init__(self, callback: Optional[Union[Callable, CallbackWrapper]]):
        """Adds very basic callback wrapper support.

        If you are a normal user, you shouldn't be using this.

        Parameters
        ----------
        callback: Union[Callable, :class:`CallbackWrapper`]
            Callback or ``CallbackWrapper`` that the application command is wrapping.
        """
        self.modify_callbacks: List[Callable] = []
        if isinstance(callback, CallbackWrapper):
            self.modify_callbacks += callback.modify_callbacks

    def modify(self) -> None:
        for modify_callback in self.modify_callbacks:
            modify_callback(self)


class ApplicationCommandOption:
    """This represents the `Application Command Option Structure
    <https://discord.com/developers/docs/interactions/application-commands#application-command-object-application-command-option-structure>`_
    with no frills added.

    Parameters
    ----------
    cmd_type: :class:`ApplicationCommandOptionType`
        Type of option the command should have.
    name: :class:`str`
        Display name of the option. Must be lowercase with no spaces, 1-32 characters.
    description: :class:`str`
        Description of the option. Must be 1-100 characters.
    required: :class:`bool`
        If the option is required or optional.
    name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
        Name(s) of the subcommand for users of specific locales. The locale code should be the key, with the
        localized name as the value
    description_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
        Description(s) of the subcommand for users of specific locales. The locale code should be the key, with the
        localized description as the value.
    choices: Union[Dict[:class:`str`, Union[:class:`str`, :class:`int`, :class:`float`]],
             Iterable[Union[:class:`str`, :class:`int`, :class:`float`]]]
        Either a dictionary of display name: value pairs, or an iterable list of values that will have identical
        display names and values.
    choice_localizations: Dict[:class:`str`, Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]]
        A dictionary of choice display names as the keys, and dictionaries of locale: localized name as the values.
    channel_types: List[:class:`ChannelType`]
        A list of ChannelType enums to allow the user to pick. Should only be set if this is a Channel option.
    min_value: Union[:class:`int`, :class:`float`]
        Minimum value the user can input. Should only be set if this is an integer or number option.
    max_value: Union[:class:`int`, :class:`float`]
        Minimum value the user can input. Should only be set if this is an integer or number option.
    min_length: :class:`int`
        Minimum length of a string the user can input. Should only be set if this is a string option.

        .. versionadded:: 2.1
    max_length: :class:`int`
        Maximum length of a string the user can input. Should only be set if this is a string option.

        .. versionadded:: 2.1
    autocomplete: :class:`bool`
        If the command option should have autocomplete enabled.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        required: Optional[bool] = None,
        *,
        cmd_type: Optional[ApplicationCommandOptionType] = None,
        name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        description_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        choices: Union[
            Dict[str, Union[str, int, float]], Iterable[Union[str, int, float]], None
        ] = None,
        choice_localizations: Optional[Dict[str, Dict[Union[Locale, str], str]]] = None,
        channel_types: Optional[List[ChannelType]] = None,
        min_value: Union[int, float, None] = None,
        max_value: Union[int, float, None] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        autocomplete: Optional[bool] = None,
    ):
        self.type: Optional[ApplicationCommandOptionType] = cmd_type
        self.name: Optional[str] = name
        self.name_localizations: Optional[Dict[Union[str, Locale], str]] = name_localizations
        self.description: Optional[str] = description
        self.description_localizations: Optional[
            Dict[Union[str, Locale], str]
        ] = description_localizations
        self.required: Optional[bool] = required
        self.choices: Optional[
            Union[Dict[str, Union[str, int, float]], Iterable[Union[str, int, float]]]
        ] = choices
        self.choice_localizations: Optional[
            Dict[str, Dict[Union[Locale, str], str]]
        ] = choice_localizations
        self.channel_types: Optional[List[ChannelType]] = channel_types
        self.min_value: Optional[Union[int, float]] = min_value
        self.max_value: Optional[Union[int, float]] = max_value
        self.min_length: Optional[int] = min_length
        self.max_length: Optional[int] = max_length
        self.autocomplete: Optional[bool] = autocomplete

    def get_name_localization_payload(self) -> Optional[Dict[str, str]]:
        if not self.name_localizations:
            return None

        return {str(locale): name for locale, name in self.name_localizations.items()}

    def get_description_localization_payload(self) -> Optional[Dict[str, str]]:
        if not self.description_localizations:
            return None

        return {
            str(locale): description
            for locale, description in self.description_localizations.items()
        }

    def get_choices_localized_payload(self) -> List[Dict[str, Union[str, int, float, dict, None]]]:
        if self.choices is None:
            return []
        elif isinstance(self.choices, dict):
            choices = self.choices
        else:
            choices = {value: value for value in self.choices}

        ret: List[Dict[str, Union[str, int, float, dict, None]]] = []
        for display_name, value in choices.items():
            # Discord returns the names as strings, might as well do it here so payload comparison is easy.
            temp: Dict[str, Union[str, int, float, dict, None]] = {
                "name": str(display_name),
                "value": value,
            }
            # The annotation prevents PyCharm from flipping the table and putting orange underlines under all of this.
            if self.choice_localizations and (
                locales := self.choice_localizations.get(str(display_name), None)
            ):
                temp["name_localizations"] = {
                    str(locale): description for locale, description in locales.items()
                }
            else:
                temp["name_localizations"] = None
            ret.append(temp)

        return ret

    @property
    def payload(self) -> dict:
        """:class:`dict`: Returns a dict payload made of the attributes of the option to be sent to Discord."""
        if self.type is None:
            raise ValueError(f"The option type must be set before obtaining the payload.")

        # noinspection PyUnresolvedReferences
        ret: Dict[str, Any] = {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "name_localizations": self.get_name_localization_payload(),
            "description_localizations": self.get_description_localization_payload(),
        }
        # We don't check if it's None because if it's False, we don't want to send it.
        if self.required:
            ret["required"] = self.required

        if self.choices:
            ret["choices"] = self.get_choices_localized_payload()

        if self.channel_types:
            # noinspection PyUnresolvedReferences
            ret["channel_types"] = [channel_type.value for channel_type in self.channel_types]

        if self.min_value is not None:
            ret["min_value"] = self.min_value

        if self.max_value is not None:
            ret["max_value"] = self.max_value

        if self.min_length is not None:
            ret["min_length"] = self.min_length

        if self.max_length is not None:
            ret["max_length"] = self.max_length

        if self.autocomplete:
            ret["autocomplete"] = self.autocomplete

        return ret


class BaseCommandOption(ApplicationCommandOption):
    """Represents an application command option, but takes a :class:`Parameter` and :class:`ClientCog` as
    an argument.

    Parameters
    ----------
    parameter: :class:`Parameter`
        Function parameter to construct the command option with.
    command: Union[:class:`BaseApplicationCommand`, :class:`SlashApplicationSubcommand`]
        Application Command this option is for.
    parent_cog: :class:`ClientCog`
        Class that the function the option is for resides in.
    """

    def __init__(
        self,
        parameter: Parameter,
        command: Union[BaseApplicationCommand, SlashApplicationSubcommand],
        parent_cog: Optional[ClientCog] = None,
    ):
        ApplicationCommandOption.__init__(self)
        self.parameter: Parameter = parameter
        self.command: Union[BaseApplicationCommand, SlashApplicationSubcommand] = command
        self.functional_name: str = parameter.name
        """Name of the kwarg in the function/method"""
        self.parent_cog: Optional[ClientCog] = parent_cog

    @property
    def error_name(self) -> str:
        return f"{self.__class__.__name__} {self.name} of command {self.command.error_name}"


class OptionConverter(_CustomTypingMetaBase):
    def __init__(self, option_type: Union[type, ApplicationCommandOptionType] = str) -> None:
        """Based on, in basic functionality, the ``ext.commands`` Converter. Users subclass this and use convert to
        provide custom "typings" for slash commands.

        The ``convert`` method MUST be overridden to convert the value from Discord to the desired value.
        The ``modify`` method MAY be overridden to modify the :class:`BaseCommandOption`.

        Parameters
        ----------
        option_type: Union[:class:`type`, :class:`ApplicationCommandOptionType`]
            Option type to forward to Discord.
        """
        self.type = option_type

    async def convert(self, interaction: Interaction, value: Any) -> Any:
        """|coro|
        Called to convert a value received from Discord to the desired value.

        If you do not wish to do any conversion, simply ``return`` the ``value``

        Parameters
        ----------
        interaction: :class:`Interaction`
            Interaction associated with the usage of the application command.
        value: Any
            Value received from Discord.

        Returns
        -------
        Any
            Converted value to forward to the callback.
        """
        raise NotImplementedError

    def modify(self, option: BaseCommandOption) -> None:
        """Called when the command is being parsed to allow for option modification.

        Parameters
        ----------
        option: :class:`BaseCommandOption`
            Command option that's being created.
        """
        pass


class Mentionable(OptionConverter):
    """When a parameter is typehinted with this, it allows users to select both roles and members."""

    def __init__(self):
        super().__init__(ApplicationCommandOptionType.mentionable)

    async def convert(self, interaction: Interaction, value: Any) -> Any:
        return value


class ClientCog:
    # TODO: I get it's a terrible name, I just don't want it to duplicate current Cog right now.
    # __cog_application_commands__: List[ApplicationCommand]
    # __cog_to_register__: List[ApplicationCommand]
    __cog_application_commands__: List[BaseApplicationCommand]

    def __new__(cls, *args: Any, **kwargs: Any):
        new_cls = super(ClientCog, cls).__new__(cls)
        new_cls._read_application_commands()
        return new_cls

    def _read_application_commands(self) -> None:
        """Iterates through the application (sub)commands contained within the ClientCog, runs their from_callback
        methods, then adds them to the internal list of application commands for this cog.
        """
        self.__cog_application_commands__ = []
        for base in reversed(self.__class__.__mro__):
            for _, value in base.__dict__.items():
                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__

                if isinstance(value, SlashApplicationCommand):
                    value.parent_cog = self
                    value.from_callback(value.callback, call_children=False)
                    self.__cog_application_commands__.append(value)
                elif isinstance(value, SlashApplicationSubcommand):
                    # As subcommands are part of a parent command and
                    #  not usable on their own, we don't add them to the command list, but do set the self_argument and
                    #  run them from the callback.
                    value.parent_cog = self
                    value.from_callback(value.callback, call_children=False)
                elif isinstance(value, BaseApplicationCommand):
                    value.parent_cog = self
                    value.from_callback(value.callback)
                    self.__cog_application_commands__.append(value)

    @property
    def application_commands(self) -> List[BaseApplicationCommand]:
        """Provides the list of application commands in this cog. Subcommands are not included."""
        return self.__cog_application_commands__

    def process_app_cmds(self) -> None:
        """Formats all added application commands with their callback."""
        # TODO: Find better name, check conflicts with actual cogs.
        for app_cmd in self.application_commands:
            app_cmd.from_callback(app_cmd.callback)

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
    async def cog_application_command_before_invoke(self, interaction: Interaction) -> None:
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
    async def cog_application_command_after_invoke(self, interaction: Interaction) -> None:
        """A special method that acts as a cog local post-invoke hook.

        This is similar to :meth:`.Command.after_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        interaction: :class:`.Interaction`
            The invocation interaction.
        """
        pass


class CallbackMixin:
    name: Optional[str]
    options: Dict[str, BaseCommandOption]

    def __init__(self, callback: Optional[Callable] = None, parent_cog: Optional[ClientCog] = None):
        """Contains code specific for adding callback support to a command class.

        If you are a normal user, you shouldn't be using this.

        Parameters
        ----------
        callback: Optional[Callable]
            Callback to create options from and invoke. If provided, it must be a coroutine function.
        parent_cog: Optional[:class:`ClientCog`]
            Class that the callback resides on. Will be passed into the callback if provided.
        """
        self.callback: Optional[Callable] = callback
        self._callback_before_invoke: Optional[ApplicationHook] = None
        self._callback_after_invoke: Optional[ApplicationHook] = None
        self.error_callback: Optional[Callable] = None
        self.checks: List[ApplicationCheck] = []
        if self.callback:
            if isinstance(callback, CallbackWrapper):
                self.callback = callback.callback

            if not asyncio.iscoroutinefunction(self.callback):
                raise TypeError(f"{self.error_name} Callback must be a coroutine")

        self.parent_cog = parent_cog

    def __call__(self, interaction: Interaction, *args, **kwargs):
        """Invokes the callback, injecting ``self`` if available."""
        if self.callback is None:
            raise ValueError("Cannot call callback when it is not set.")
        elif self.parent_cog:
            return self.callback(self.parent_cog, interaction, *args, **kwargs)
        else:
            return self.callback(interaction, *args, **kwargs)

    @property
    def error_name(self) -> str:
        """Returns a string containing the class name, command name, and the callback to use in raising exceptions.

        Examples
        --------
        >>> print(app_cmd.error_name)
        SlashApplicationCommand reloadme <function TinyTest.reloadme at 0x7f4b3b563e20>


        Returns
        -------
        :class:`str`
            String containing the class name, command name, and callback object.
        """
        return f"{self.__class__.__name__} {self.name} {self.callback}"

    @property
    def cog_before_invoke(self) -> Optional[ApplicationHook]:
        """Returns the cog_application_command_before_invoke method for the cog that this command is in.
        Returns ``None`` if not the method is not found.

        Returns
        -------
        Optional[:class:`ApplicationHook`]
            ``before_invoke`` method from the parent cog. ``None`` if not the method is not found.
        """
        if not self.parent_cog:
            return None

        return ClientCog._get_overridden_method(
            self.parent_cog.cog_application_command_before_invoke
        )

    @property
    def cog_after_invoke(self) -> Optional[ApplicationHook]:
        """Returns the cog_application_command_after_invoke method for the cog that this command is in.

        Returns
        -------
        Optional[:class:`ApplicationHook`]
            ``after_invoke`` method from the parent cog. ``None`` if not the method is not found.
        """
        if not self.parent_cog:
            return None

        return ClientCog._get_overridden_method(
            self.parent_cog.cog_application_command_after_invoke
        )

    def has_error_handler(self) -> bool:
        """:class:`bool`: Checks whether the command has an error handler registered."""
        return self.error_callback is not None

    def add_check(self, func: ApplicationCheck) -> CallbackMixin:
        """Adds a check to the application command. Returns the application command for method chaining.

        Parameters
        ----------
        func: :class:`ApplicationCheck`
            The function that will be used as a check.
        """
        self.checks.append(func)
        return self

    def remove_check(self, func: ApplicationCheck) -> CallbackMixin:
        """Removes a check from the ApplicationCommand. Returns the application command for method chaining.

        This function is idempotent and will not raise an exception
        if the function is not in the command's checks.

        Parameters
        ----------
        func: :class:`ApplicationCheck`
            The function to remove from the checks.
        """
        try:
            self.checks.remove(func)
        except ValueError:
            pass

        return self

    def from_callback(
        self,
        callback: Optional[Callable] = None,
        option_class: Optional[Type[BaseCommandOption]] = BaseCommandOption,
    ) -> None:
        """Creates objects of type `option_class` with the parameters of the function, and stores them in
        the options attribute.

        Parameters
        ----------
        callback: Optional[Callable]
            Callback to create options from. Must be a coroutine function.
        option_class: Optional[Type[:class:`BaseCommandOption`]]
            Class to create the options using. Should either be or subclass :class:`BaseCommandOption`. Defaults
            to :class:`BaseCommandOption`.

        Returns
        -------
        :class:`CallbackMixin`
            Self for possible chaining.

        """
        if callback is not None:
            self.callback = callback

        if not self.callback:
            raise ValueError("Unable to get name and options from a callback if it is None")

        if self.name is None:
            self.name = self.callback.__name__

        try:
            if not asyncio.iscoroutinefunction(self.callback):
                raise TypeError("Callback must be a coroutine")
            # While this arguably is Slash Commands only, we could do some neat stuff in the future with it in other
            #  commands. While Discord doesn't support anything else having Options, we
            #  might be able to do something here.
            if option_class:
                skip_counter = 1
                typehints = typing.get_type_hints(self.callback)
                # Getting the callback with `self_skip = inspect.ismethod(self.callback)` was problematic due to the
                #  decorator going into effect before the class is instantiated, thus being a function at the time.
                #  Try to look into fixing that in the future?
                #  If self.parent_cog isn't reliable enough, we can possibly check if the first parameter name is `self`
                if self.parent_cog:
                    skip_counter += 1

                for name, param in signature(self.callback).parameters.items():
                    if skip_counter:
                        skip_counter -= 1
                    else:
                        if isinstance(param.annotation, str):
                            # Thank you Disnake for the guidance to use this.
                            param = param.replace(annotation=typehints.get(name, param.empty))

                        arg = option_class(param, self, parent_cog=self.parent_cog)  # type: ignore
                        # this is a mixin, so `self` would be odd here

                        if not arg.name:
                            raise ValueError("Cannot store an argument's type if the name is None")

                        self.options[arg.name] = arg

        except Exception as e:
            _log.error(f"Error creating from callback %s: %s", self.error_name, e)
            raise e

    async def can_run(self, interaction: Interaction) -> bool:
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
                check_result = await maybe_coroutine(check, interaction)  # type: ignore
            # To catch any subclasses of ApplicationCheckFailure.
            except ApplicationCheckFailure:
                raise
            # If the check returns False, the command can't be run.
            else:
                if not check_result:
                    raise ApplicationCheckFailure(
                        f"The global check functions for application command {self.error_name} failed."
                    )

        # Cog check
        if self.parent_cog:
            cog_check = ClientCog._get_overridden_method(
                self.parent_cog.cog_application_command_check
            )
            if cog_check is not None and not await maybe_coroutine(cog_check, interaction):
                raise ApplicationCheckFailure(
                    f"The cog check functions for application command {self.error_name} failed."
                )

        # Command checks
        for check in self.checks:
            try:
                check_result = await maybe_coroutine(check, interaction)  # type: ignore
            # To catch any subclasses of ApplicationCheckFailure.
            except ApplicationCheckFailure:
                raise
            # If the check returns False, the command can't be run.
            else:
                if not check_result:
                    raise ApplicationCheckFailure(
                        f"The check functions for application command {self.error_name} failed."
                    )

        return True

    async def invoke_callback_with_hooks(
        self, state: ConnectionState, interaction: Interaction, *args, **kwargs
    ) -> None:
        """|coro|
        Invokes the callback with all hooks and checks.
        """
        interaction._set_application_command(self)  # type: ignore
        try:
            can_run = await self.can_run(interaction)
        except Exception as error:
            state.dispatch("application_command_error", interaction, error)
            await self.invoke_error(interaction, error)
            return

        if can_run:
            if self._callback_before_invoke is not None:
                await self._callback_before_invoke(interaction)  # type: ignore

            if (before_invoke := self.cog_before_invoke) is not None:
                await before_invoke(interaction)  # type: ignore

            if (before_invoke := state._application_command_before_invoke) is not None:
                await before_invoke(interaction)  # type: ignore

            try:
                # await self.invoke_callback(interaction, *args, **kwargs)
                await self(interaction, *args, **kwargs)
            except Exception as error:
                state.dispatch(
                    "application_command_error",
                    interaction,
                    ApplicationInvokeError(error),
                )
                await self.invoke_error(interaction, error)
            else:
                state.dispatch("application_command_completion", interaction)
            finally:
                if self._callback_after_invoke is not None:
                    await self._callback_after_invoke(interaction)  # type: ignore

                if (after_invoke := self.cog_after_invoke) is not None:
                    await after_invoke(interaction)  # type: ignore

                if (after_invoke := state._application_command_after_invoke) is not None:
                    await after_invoke(interaction)  # type: ignore

    async def invoke_callback(self, interaction: Interaction, *args, **kwargs) -> None:
        """|coro|
        Invokes the callback, injecting ``self`` if available.
        """
        await self(interaction, *args, **kwargs)

    async def invoke_error(self, interaction: Interaction, error: Exception) -> None:
        """|coro|
        Invokes the error handler if available.
        """
        if self.has_error_handler() and self.error_callback is not None:
            if self.parent_cog:
                await self.error_callback(self.parent_cog, interaction, error)
            else:
                await self.error_callback(interaction, error)

    def error(self, callback: ApplicationErrorCallback) -> Callable:
        """Decorates a function, setting it as a callback to be called when a :class:`ApplicationError` or any of
        its subclasses is raised inside the :class:`ApplicationCommand`.

        Parameters
        ----------
        callback: Callable[[:class:`Interaction`, :class:`ApplicationError`], :class:`asyncio.Awaitable[Any]`]
            The callback to call when an error occurs.
        """
        if not asyncio.iscoroutinefunction(callback):
            raise TypeError("The error handler must be a coroutine.")

        self.error_callback = callback
        return callback

    def before_invoke(
        self, coro: Callable[[Interaction], Coroutine]
    ) -> Callable[[Interaction], Coroutine]:
        """Sets the callback that should be run before the command callback is invoked.

        Parameters
        ----------
        coro: Callable[[:class:`Interaction`], Coroutine]
            Coroutine to set as the before_invoke hook.

        Returns
        -------
        Callable[[:class:`Interaction`], Coroutine]
            The coroutine to allow multiple commands to share the function.
        """
        self._callback_before_invoke = coro
        return coro

    def after_invoke(
        self, coro: Callable[[Interaction], Coroutine]
    ) -> Callable[[Interaction], Coroutine]:
        """Sets the callback that should be run after the command callback is invoked.

        Parameters
        ----------
        coro: Callable[[:class:`Interaction`], Coroutine]
            Coroutine to set as the after_invoke hook.

        Returns
        -------
        Callable[[:class:`Interaction`], Coroutine]
            The coroutine to allow multiple commands to share the function.
        """
        self._callback_after_invoke = coro
        return coro


class AutocompleteOptionMixin:
    def __init__(
        self,
        autocomplete_callback: Optional[Callable] = None,
        parent_cog: Optional[ClientCog] = None,
    ):
        """Contains code for providing autocomplete support, specifically for options.

        If you are a normal user, you shouldn't be using this.

        Parameters
        ----------
        autocomplete_callback: `Callable`
            Callback to create options from and invoke. If provided, it must be a coroutine function.
        parent_cog: Optional[:class:`ClientCog`]
            Class that the callback resides on. Will be passed into the callback if provided.

        """
        self.autocomplete_callback: Optional[Callable] = autocomplete_callback
        self.autocomplete_options: Set[str] = set()
        self.parent_cog: Optional[ClientCog] = parent_cog

    def from_autocomplete_callback(self, callback: Callable) -> AutocompleteOptionMixin:
        """Parses a callback meant to be the autocomplete function."""
        self.autocomplete_callback = callback
        if not asyncio.iscoroutinefunction(self.autocomplete_callback):
            raise TypeError("Callback must be a coroutine")

        skip_count = 2  # We skip the first and second args, they are always the Interaction and
        #  the primary autocomplete value.
        if self.parent_cog:
            # If there's a parent cog, there should be a self. Skip it too.
            skip_count += 1

        for name, _ in signature(self.autocomplete_callback).parameters.items():
            if skip_count:
                skip_count -= 1
            else:
                self.autocomplete_options.add(name)

        return self

    async def invoke_autocomplete_callback(
        self, interaction: Interaction, option_value: Any, **kwargs
    ) -> None:
        """|coro|
        Invokes the autocomplete callback, injecting ``self`` if available.
        """
        if self.autocomplete_callback is None:
            raise ValueError("Autocomplete hasn't been set for this function.")

        if self.parent_cog:
            return await self.autocomplete_callback(
                self.parent_cog, interaction, option_value, **kwargs
            )
        else:
            return await self.autocomplete_callback(interaction, option_value, **kwargs)


class AutocompleteCommandMixin:
    options: Dict[str, SlashCommandOption]
    children: Dict[str, SlashApplicationSubcommand]
    _state: ConnectionState

    def __init__(self, parent_cog: Optional[ClientCog] = None):
        """Contains code for providing autocomplete support, specifically for application commands.

        If you are a normal user, you shouldn't be using this.

        Parameters
        ----------
        parent_cog: Optional[:class:`ClientCog`]
            Class that the callback resides on. Will be passed into the callback if provided.
        """
        self.parent_cog = parent_cog
        # Why does this exist, and why is it "temp", you may ask? :class:`SlashCommandOption`'s are only available
        # after the callback is fully parsed when the :class:`Client` or :class:`ClientCog` runs the from_callback
        # method, thus we have to hold the decorated autocomplete callbacks temporarily until then.
        self._temp_autocomplete_callbacks: Dict[str, Callable] = {}

    async def call_autocomplete_from_interaction(self, interaction: Interaction) -> None:
        """|coro|
        Calls the autocomplete callback with the given interaction.
        """
        await self.call_autocomplete(self._state, interaction)

    async def call_autocomplete(
        self,
        state: ConnectionState,
        interaction: Interaction,
        option_data: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """|coro|
        Calls the autocomplete callback with the given interaction and option data.
        """
        if not option_data:
            if interaction.data is None:
                raise ValueError("Discord did not provide us interaction data")

            # pyright does not want to lose typeddict specificity but we do not care here
            option_data = interaction.data.get("options", {})  # type: ignore

            if not option_data:
                raise ValueError("Discord did not provide us option data")

        if self.children:
            await self.children[option_data[0]["name"]].call_autocomplete(
                state, interaction, option_data[0].get("options", {})
            )
        else:
            focused_option_name = None
            for arg in option_data:
                if arg.get("focused", None) is True:
                    if focused_option_name:
                        raise ValueError(
                            "Multiple options are focused, is that supposed to be possible?"
                        )

                    focused_option_name = arg["name"]

            if not focused_option_name:
                raise ValueError("There's supposed to be a focused option, but it's not found?")

            focused_option = self.options[focused_option_name]
            if focused_option.autocomplete_callback is None:
                raise ValueError(
                    f"{self.error_name} Autocomplete called for option {focused_option.functional_name} but it doesn't "
                    f"have an autocomplete function?"
                )

            kwargs = {}
            uncalled_options = focused_option.autocomplete_options.copy()

            if focused_option.name is not None:
                uncalled_options.discard(focused_option.name)

            focused_option_value = None
            for arg_data in option_data:
                if (
                    option := self.options.get(arg_data["name"], None)
                ) and option.functional_name in uncalled_options:
                    uncalled_options.discard(option.functional_name)
                    kwargs[option.functional_name] = await option.handle_value(
                        state, arg_data["value"], interaction
                    )
                elif arg_data["name"] == focused_option.name:
                    focused_option_value = await focused_option.handle_value(
                        state, arg_data["value"], interaction
                    )

            for option_name in uncalled_options:
                kwargs[option_name] = None

            value = await focused_option.invoke_autocomplete_callback(
                interaction, focused_option_value, **kwargs
            )
            if value and not interaction.response.is_done():
                await interaction.response.send_autocomplete(value)

    def from_autocomplete(self) -> None:
        """Processes the found autocomplete callbacks and associates them to their corresponding options.

        Raises
        ------
        :class:`ValueError`
            If a found arg name doesn't correspond to an autocomplete function.
        """
        # TODO: You should probably add the ability to provide a dict/kwargs of callbacks to override whatever was set
        #  earlier, right?
        for arg_name, callback in self._temp_autocomplete_callbacks.items():
            found = False
            for _, option in self.options.items():
                if option.functional_name == arg_name:
                    if option.autocomplete is None:
                        # If autocomplete isn't set, enable it for them.
                        option.autocomplete = True

                    if option.autocomplete:
                        option.from_autocomplete_callback(callback)
                        found = True

            if found:
                continue
            # If it hasn't returned yet, it didn't find a valid kwarg. Raise it.
            raise ValueError(f'{self.error_name} kwarg "{arg_name}" for autocomplete not found.')

    def on_autocomplete(self, on_kwarg: str):
        def decorator(func: Callable):
            self._temp_autocomplete_callbacks[on_kwarg] = func
            return func

        return decorator

    @property
    def error_name(self) -> str:
        # Signals that this mixin needs this.
        raise NotImplementedError


# Extends Any so that type checkers won't complain that it's a default for a parameter of a different type
class SlashOption(ApplicationCommandOption, _CustomTypingMetaBase):
    """Provides Discord with information about an option in a command.

    When this class is set as the default argument of a parameter in an Application Command, additional information
    about the parameter is sent to Discord for the user to see.

    Parameters
    ----------
    name: :class:`str`
        The name of the Option on Discords side. If left as None, it defaults to the parameter name.
    description: :class:`str`
        The description of the Option on Discords side. If left as None, it defaults to "".
    required: :class:`bool`
        If a user is required to provide this argument before sending the command.
    name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
        Name(s) of the subcommand for users of specific locales. The locale code should be the key, with the
        localized name as the value
    description_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
        Description(s) of the subcommand for users of specific locales. The locale code should be the key, with the
        localized description as the value
    choices: Union[Dict[:class:`str`, Union[:class:`str`, :class:`int`, :class:`float`]],
             Iterable[Union[:class:`str`, :class:`int`, :class:`float`]]]
        A list of choices that a user must choose.
        If a :class:`dict` is given, the keys are what the users are able to see, the values are what is sent back
        to the bot.
        Otherwise, it is treated as an `Iterable` where what the user sees and is sent back to the bot are the same.
    choice_localizations: Dict[:class:`str`, Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]]
        A dictionary of choice display names as the keys, and dictionaries of locale: localized name as the values.
    channel_types: List[:class:`ChannelType`]
        List of `ChannelType` enums, limiting the users choice to only those channel types. The parameter must be
        typed as :class:`GuildChannel` for this to function.
    min_value: Union[:class:`int`, :class:`float`]
        Minimum integer or floating point value the user is allowed to input. The parameter must be typed as an
        :class:`int` or :class:`float` for this to function.
    max_value: Union[:class:`int`, :class:`float`]
        Maximum integer or floating point value the user is allowed to input. The parameter must be typed as an
        :class:`int` or :class:`float` for this to function.
    min_length: :class:`int`
        Minimum length for a string value the user is allowed to input. The parameter must be typed as a
        :class:`str` for this to function.

        .. versionadded:: 2.1
    max_length: :class:`int`
        Maximum length for a string value the user is allowed to input. The parameter must be typed as a
        :class:`str` for this to function.

        .. versionadded:: 2.1
    autocomplete: :class:`bool`
        If this parameter has an autocomplete function decorated for it. If unset, it will automatically be `True`
        if an autocomplete function for it is found.
    autocomplete_callback: Optional[:class:`Callable`]
        The function that will be used to autocomplete this parameter. If not specified, it will be looked for
        using the :meth:`~SlashApplicationSubcommand.on_autocomplete` decorator.
    default: Any
        When required is not True and the user doesn't provide a value for this Option, this value is given instead.
    verify: :class:`bool`
        If True, the given values will be checked to ensure that the payload to Discord is valid.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        required: Optional[bool] = None,
        *,
        name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        description_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        choices: Union[
            Dict[str, Union[str, int, float]], Iterable[Union[str, int, float]], None
        ] = None,
        choice_localizations: Optional[Dict[str, Dict[Union[Locale, str], str]]] = None,
        channel_types: Optional[List[ChannelType]] = None,
        min_value: Union[int, float, None] = None,
        max_value: Union[int, float, None] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        autocomplete: Optional[bool] = None,
        autocomplete_callback: Optional[Callable] = None,
        default: Any = MISSING,
        verify: bool = True,
    ):
        super().__init__(
            name=name,
            name_localizations=name_localizations,
            description=description,
            description_localizations=description_localizations,
            required=required,
            choices=choices,
            choice_localizations=choice_localizations,
            channel_types=channel_types,
            min_value=min_value,
            max_value=max_value,
            min_length=min_length,
            max_length=max_length,
            autocomplete=autocomplete,
        )

        self.autocomplete_callback: Optional[Callable] = autocomplete_callback
        self.default: Any = default
        self._verify: bool = verify
        if self._verify:
            self.verify()

    def verify(self) -> bool:
        """Checks if the given values conflict with one another or are invalid."""
        if self.choices and self.autocomplete:  # Incompatible according to Discord Docs.
            raise ValueError("Autocomplete may not be set to true if choices are present.")

        return True


class SlashCommandOption(BaseCommandOption, SlashOption, AutocompleteOptionMixin):
    command: Union[SlashApplicationCommand, SlashApplicationSubcommand]
    option_types: Dict[type, ApplicationCommandOptionType] = {
        str: ApplicationCommandOptionType.string,
        int: ApplicationCommandOptionType.integer,
        bool: ApplicationCommandOptionType.boolean,
        User: ApplicationCommandOptionType.user,
        Member: ApplicationCommandOptionType.user,
        GuildChannel: ApplicationCommandOptionType.channel,
        CategoryChannel: ApplicationCommandOptionType.channel,
        DMChannel: ApplicationCommandOptionType.channel,
        ForumChannel: ApplicationCommandOptionType.channel,
        GroupChannel: ApplicationCommandOptionType.channel,
        StageChannel: ApplicationCommandOptionType.channel,
        TextChannel: ApplicationCommandOptionType.channel,
        VoiceChannel: ApplicationCommandOptionType.channel,
        Thread: ApplicationCommandOptionType.channel,
        Role: ApplicationCommandOptionType.role,
        Mentionable: ApplicationCommandOptionType.mentionable,
        float: ApplicationCommandOptionType.number,
        Attachment: ApplicationCommandOptionType.attachment,
    }
    """Maps Python annotations/typehints to Discord Application Command type values."""

    channel_mapping: Dict[type, Tuple[ChannelType, ...]] = {
        CategoryChannel: (ChannelType.category,),
        DMChannel: (ChannelType.private,),
        ForumChannel: (ChannelType.forum,),
        GroupChannel: (ChannelType.group,),
        StageChannel: (ChannelType.stage_voice,),
        TextChannel: (
            ChannelType.text,
            ChannelType.news,
        ),
        Thread: (
            ChannelType.news_thread,
            ChannelType.public_thread,
            ChannelType.private_thread,
        ),
        VoiceChannel: (ChannelType.voice,),
    }
    """Maps Python channel annotations/typehints to Discord ChannelType values."""

    def __init__(
        self,
        parameter: Parameter,
        command: Union[SlashApplicationCommand, SlashApplicationSubcommand],
        parent_cog: Optional[ClientCog] = None,
    ):
        BaseCommandOption.__init__(self, parameter, command, parent_cog)
        SlashOption.__init__(self)
        # We subclassed SlashOption because we must handle all attributes it has.
        AutocompleteOptionMixin.__init__(self, parent_cog=parent_cog)

        if isinstance(parameter.default, SlashOption):
            # Remember: Values that the user provided in SlashOption should override any logic.
            #  Verify can raise errors on incompatible values.
            cmd_arg = parameter.default
            cmd_arg_given = True
        else:
            cmd_arg = SlashOption()
            cmd_arg_given = False

        self.name = cmd_arg.name or parameter.name
        # Use the given name, or default to the parameter name.
        # typehint_origin = typing.get_origin(parameter.annotation)  # TODO: Once Python 3.10 is standard, use this.
        typehint_origin = typing_extensions.get_origin(parameter.annotation)

        annotation_type: ApplicationCommandOptionType
        annotation_required = True
        annotation_choices: List[Union[str, int, float]] = []
        annotation_channel_types: List[ChannelType] = []
        annotation_converters: List[OptionConverter] = []

        if typehint_origin is Literal:
            # If they use the Literal typehint as their base. This currently should only support int, float, str, and
            #  technically None for setting it to be optional.
            found_type = MISSING
            found_choices = []
            # for lit in typing.get_args(parameter.annotation):  # TODO: Once Python 3.10 is standard, use this.
            for lit in typing_extensions.get_args(parameter.annotation):
                lit = unpack_annotated(lit, list(self.option_types.keys()))
                lit_type = type(lit)
                if lit is None:
                    # If None is included, they want it to be optional. But we don't want None added to the choices.
                    annotation_required = False

                elif lit_type in (int, str, float):
                    if found_type is MISSING:
                        # If we haven't set the type of the annotation, set it.
                        found_type = self.get_type(lit_type)
                    elif self.get_type(lit_type) is not found_type:
                        raise ValueError(
                            f"{self.error_name} | Literal {lit} is incompatible with {found_type}"
                        )
                    found_choices.append(lit)

                else:
                    raise ValueError(
                        f"{self.error_name} Invalid type for choices: {type(lit)}: {lit}"
                    )

            if found_type is MISSING:
                raise NotImplementedError(
                    "This behavior currently isn't handled in Nextcord. Please join the Nextcord Discord server and "
                    "explain what you are doing to get this error and why we would support it."
                )

            annotation_type = found_type
            annotation_choices = found_choices
        elif typehint_origin in (Union, Optional, Annotated, None):
            # If the typehint base is Union, Optional, or not any grouping...
            found_type = MISSING
            found_channel_types: List[ChannelType] = []

            if typehint_origin is None:
                unpacked_annotations: List[type] = [
                    parameter.annotation,
                ]
                literals: List[Annotated[OptionConverter, object]] = []
            else:
                unpacked_annotations, literals = unpack_annotation(
                    parameter.annotation, list(self.option_types.keys())
                )
            # Make sure that all literals are only OptionConverters and nothing else.
            for lit in literals:
                if not isinstance(lit, OptionConverter) or lit is not None:
                    raise ValueError(
                        f"{self.error_name} You cannot use non-OptionConverter literals when the base annotation is "
                        f"not Literal."
                    )

            # Pyright gets upset at appending these lists together, but not upset when .extend is used?
            # grouped_annotations: List[Union[type, Annotated[object, OptionConverter]]] = unpacked_annotations + \
            #                                                                              literals
            grouped_annotations: List[
                Union[type, Annotated[Optional[OptionConverter], object], Type[None]]
            ] = []
            grouped_annotations.extend(unpacked_annotations)
            grouped_annotations.extend(literals)
            # The only literals in this should be OptionConverters. Anything else should have triggered the ValueError.
            for anno in grouped_annotations:
                if isinstance(anno, object) and isinstance(anno, OptionConverter):
                    # If the annotation is instantiated, add it to the converters and set the anno to the type it has.
                    annotation_converters.append(anno)
                    anno = anno.type
                elif isinstance(anno, type) and issubclass(anno, OptionConverter):
                    # If the annotation is NOT instantiated, instantiate it and do the above.
                    made_converter = anno()
                    annotation_converters.append(made_converter)
                    anno = made_converter.type

                if anno is None or anno is type(None):
                    # If None is included, they want it to be optional. But we don't want None processed fully as anno.
                    annotation_required = False
                else:
                    if found_type is MISSING:
                        # If we haven't set the type of the annotation, set it.
                        found_type = self.get_type(anno)
                    elif self.get_type(anno) is not found_type:
                        raise ValueError(
                            f"{self.error_name} | Annotation {anno} is incompatible with {found_type} \n| {typehint_origin}\n| {parameter.annotation}\n| {grouped_annotations}"
                        )

                    if not (
                        isinstance(anno, ApplicationCommandOptionType)
                        or isinstance(anno, OptionConverter)
                    ) and (channel_types := self.channel_mapping.get(anno)):
                        found_channel_types.extend(channel_types)

            annotation_type = found_type
            if found_channel_types:
                annotation_channel_types = found_channel_types

        else:
            raise ValueError(
                f"{self.error_name} Invalid annotation origin: {typehint_origin} \n"
                f"| {type(typehint_origin)} \n| {typing_extensions.get_origin(typehint_origin)} \n"
                f"| {parameter.annotation}"
            )

        self.name_localizations = cmd_arg.name_localizations
        self._description = cmd_arg.description
        self.description_localizations = cmd_arg.description_localizations
        self.choice_localizations = cmd_arg.choice_localizations

        self.min_value = cmd_arg.min_value
        self.max_value = cmd_arg.max_value
        self.min_length = cmd_arg.min_length
        self.max_length = cmd_arg.max_length
        self.autocomplete = cmd_arg.autocomplete
        self.autocomplete_callback = cmd_arg.autocomplete_callback
        if self.autocomplete_callback and self.autocomplete is None:
            # If they didn't explicitly enable autocomplete but did add an autocomplete callback...
            self.autocomplete = True
        if self.autocomplete_callback:
            if not asyncio.iscoroutinefunction(self.autocomplete_callback):
                raise TypeError(
                    f"Given autocomplete callback for kwarg {self.functional_name} isn't a coroutine."
                )

        if cmd_arg.required is not None:
            # If the user manually set if it's required...
            self.required = cmd_arg.required
        elif annotation_required is False:
            # If the user annotated it as Optional or None...
            self.required = False
        elif cmd_arg.default is not MISSING:
            # If the user provided a default in the SlashOption...
            self.required = False
        elif parameter.default is not parameter.empty and not cmd_arg_given:
            # If the default isn't SlashOption, but was provided...
            self.required = False
        else:
            # Unlike Discord, parameters in Python are required by default. With this being a Python library, we should
            # remain intuitive by following that standard.
            self.required = True

        self.type = annotation_type
        self.choices = cmd_arg.choices or annotation_choices or None
        self.channel_types = cmd_arg.channel_types or annotation_channel_types or None
        self.converters: List[OptionConverter] = annotation_converters

        if cmd_arg_given is False and parameter.default is not parameter.empty:
            self.default = parameter.default
        else:
            self.default = None if cmd_arg.default is MISSING else cmd_arg.default

        for converter in self.converters:
            converter.modify(self)

        # noinspection PyProtectedMember
        if cmd_arg._verify:
            self.verify()

    @property
    def description(self) -> str:
        """:class:`str`: If no description is set, it returns "No description provided" """
        # noinspection PyProtectedMember
        if self._description is not None:
            return self._description
        elif self.command._parsed_docstring and (
            docstring := self.command._parsed_docstring["args"].get(self.functional_name)
        ):
            return docstring
        else:
            return DEFAULT_SLASH_DESCRIPTION

    @description.setter
    def description(self, value: str):
        self._description = value

    def get_type(
        self,
        param_typing: Union[type, OptionConverter, ApplicationCommandOptionType],
    ) -> ApplicationCommandOptionType:
        if isinstance(param_typing, OptionConverter):
            if isinstance(param_typing.type, type):
                param_typing = param_typing.type
            else:
                return param_typing.type
        elif isinstance(param_typing, ApplicationCommandOptionType):
            return param_typing

        # noinspection PyTypeChecker,PyUnboundLocalVariable
        if param_typing is self.parameter.empty:
            return ApplicationCommandOptionType.string
        elif valid_type := self.option_types.get(param_typing, None):
            return valid_type
        elif (
            # type(None) in typing.get_args(param_typing)  # TODO: Once Python 3.10 is standard, use this
            type(None) in typing_extensions.get_args(param_typing)
            and (
                inner_type := find(
                    lambda t: t is not type(None), typing_extensions.get_args(param_typing)
                )
            )
            and (valid_type := self.option_types.get(inner_type, None))
        ):
            return valid_type
        else:
            raise ValueError(
                f"{self.error_name} Type `{param_typing}` isn't a supported typehint for Application Commands."
            )

    def verify(self) -> bool:
        """This should run through :class:`SlashOption` variables and raise errors when conflicting data is given."""
        super().verify()
        if self.channel_types and self.type is not ApplicationCommandOptionType.channel:
            raise ValueError(
                "channel_types can only be given when the var is typed as nextcord.abc.GuildChannel"
            )

        if self.min_value is not None and type(self.min_value) not in (int, float):
            raise ValueError("min_value must be an int or float.")

        if self.max_value is not None and type(self.max_value) not in (int, float):
            raise ValueError("max_value must be an int or float.")

        if (self.min_value is not None or self.max_value is not None) and self.type not in (
            ApplicationCommandOptionType.integer,
            ApplicationCommandOptionType.number,
        ):
            raise ValueError(
                "min_value or max_value can only be set if the type is integer or number."
            )

        if self.min_length is not None and not isinstance(self.min_length, int):
            raise ValueError("min_length must be an int.")

        if self.max_length is not None and not isinstance(self.max_length, int):
            raise ValueError("max_length must be an int.")

        if self.min_length is not None and self.min_length < 0:
            raise ValueError("min_length must be greater than or equal to 0.")

        if self.max_length is not None and self.max_length < 1:
            raise ValueError("max_length must be greater than or equal to 1.")

        # we check this ourselves because Discord doesn't do it yet
        # see here: https://github.com/discord/discord-api-docs/issues/5149
        if (
            self.min_length is not None and self.max_length is not None
        ) and self.min_length > self.max_length:
            raise ValueError("min_length must be less than or equal to max_length")

        if (self.min_length is not None or self.max_length is not None) and self.type is not (
            ApplicationCommandOptionType.string
        ):
            raise ValueError("min_length or max_length can only be set if the type is a string.")

        return True

    async def handle_value(
        self, state: ConnectionState, value: Any, interaction: Interaction
    ) -> Any:
        if self.type is ApplicationCommandOptionType.channel:
            value = state.get_channel(int(value))
        elif self.type is ApplicationCommandOptionType.user:
            user_id = int(value)
            user_dict = {user.id: user for user in get_users_from_interaction(state, interaction)}
            value = user_dict[user_id]
        elif self.type is ApplicationCommandOptionType.role:
            if interaction.guild is None:
                raise TypeError("Unable to handle a Role type when guild is None")

            value = interaction.guild.get_role(int(value))
        elif self.type is ApplicationCommandOptionType.integer:
            value = int(value) if value != "" else None
        elif self.type is ApplicationCommandOptionType.number:
            value = float(value)
        elif self.type is ApplicationCommandOptionType.attachment:
            try:
                # this looks messy but is too much effort to handle
                # feel free to use typing.cast and if statements and raises
                resolved_attachment_data = interaction.data["resolved"]["attachments"][value]  # type: ignore
            except (AttributeError, ValueError, IndexError):
                raise ValueError("Discord did not provide us interaction data for the attachment")

            value = Attachment(data=resolved_attachment_data, state=state)
        elif self.type is ApplicationCommandOptionType.mentionable:
            user_role_list: List[Union[User, Member, Role]] = get_users_from_interaction(
                state, interaction
            ) + get_roles_from_interaction(
                state, interaction
            )  # pyright: ignore
            # pyright is so sure that you cant add role + user | member
            # when the resulting type is right
            mentionables = {mentionable.id: mentionable for mentionable in user_role_list}
            value = mentionables[int(value)]

        if self.converters:
            ret = value
            for converter in self.converters:
                ret = await converter.convert(interaction, ret)
            return ret
        else:
            return value


class SlashCommandMixin(CallbackMixin):
    _description: Optional[str]

    def __init__(self, callback: Optional[Callable], parent_cog: Optional[ClientCog]):
        CallbackMixin.__init__(self, callback=callback, parent_cog=parent_cog)
        self.options: Dict[str, SlashCommandOption] = {}
        self.children: Dict[str, SlashApplicationSubcommand] = {}
        self._parsed_docstring: Optional[Dict[str, Any]] = None

    @property
    def description(self) -> str:
        if self._description is not None:
            return self._description
        elif self._parsed_docstring and (docstring := self._parsed_docstring["description"]):
            return docstring
        else:
            return DEFAULT_SLASH_DESCRIPTION

    def from_callback(
        self,
        callback: Optional[Callable] = None,
        option_class: Optional[Type[SlashCommandOption]] = SlashCommandOption,
    ):
        CallbackMixin.from_callback(self, callback=callback, option_class=option_class)
        # Right now, only slash commands can have descriptions. If User/Message commands gain descriptions, move
        #  this to CallbackMixin.
        if callback is None:
            raise TypeError("Cannot parse docstring of a callback that is None")

        self._parsed_docstring = parse_docstring(callback, _MAX_COMMAND_DESCRIPTION_LENGTH)

    async def get_slash_kwargs(
        self,
        state: ConnectionState,
        interaction: Interaction,
        option_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        # interaction.data = cast(, interaction.data)

        if option_data is None:
            # pyright does not want to lose typeddict specificity but we do not care here
            option_data = interaction.data.get("options", {})  # type: ignore

            if not option_data:
                raise ValueError("Discord did not provide us any options data")

        kwargs = {}
        uncalled_args = self.options.copy()
        for arg_data in option_data:
            if arg_data["name"] in uncalled_args:
                uncalled_args.pop(arg_data["name"])
                kwargs[self.options[arg_data["name"]].functional_name] = await self.options[
                    arg_data["name"]
                ].handle_value(state, arg_data["value"], interaction)
            else:
                # TODO: Handle this better.
                raise ApplicationCommandOptionMissing(
                    f"An argument was provided that wasn't already in the function, did you recently change it and "
                    f"did not resync?\nRegistered Options: {self.options}, "
                    f"Discord-sent args: {interaction.data['options']}, broke on {arg_data}"  # type: ignore
                )

        for uncalled_arg in uncalled_args.values():
            kwargs[uncalled_arg.functional_name] = uncalled_arg.default

        return kwargs

    async def call_slash(
        self,
        state: ConnectionState,
        interaction: Interaction,
        option_data: Optional[List[Dict[str, Any]]] = None,
    ):
        if option_data is None:
            if interaction.data is None:
                raise ValueError("Discord did not provide us interaction data")

            # pyright does not want to lose typeddict specificity but we do not care here
            option_data = interaction.data.get("options", {})  # type: ignore

            if not option_data:
                raise ValueError("Discord did not provide us any options data")

        if self.children:
            await self.children[option_data[0]["name"]].call_slash(
                state, interaction, option_data[0].get("options", {})
            )
        else:
            kwargs = await self.get_slash_kwargs(state, interaction, option_data)
            await self.invoke_callback_with_hooks(state, interaction, **kwargs)


class BaseApplicationCommand(CallbackMixin, CallbackWrapperMixin):
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        *,
        cmd_type: ApplicationCommandType,
        name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        description_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        callback: Optional[Callable] = None,
        guild_ids: Optional[Iterable[int]] = None,
        dm_permission: Optional[bool] = None,
        default_member_permissions: Optional[Union[Permissions, int]] = None,
        parent_cog: Optional[ClientCog] = None,
        force_global: bool = False,
    ):
        """Base application command class that all specific application command classes should subclass. All common
        behavior should be here, with subclasses either adding on or overriding specific aspects of this class.

        Parameters
        ----------
        cmd_type: :class:`ApplicationCommandType`
            Type of application command. This should be set by subclasses.
        name: :class:`str`
            Name of the command.
        description: :class:`str`
            Description of the command.
        name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Name(s) of the command for users of specific locales. The locale code should be the key, with the localized
            name as the value.
        description_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Description(s) of the command for users of specific locales. The locale code should be the key, with the
            localized description as the value.
        callback: Callable
            Callback to make the application command from, and to run when the application command is called.
        guild_ids: Iterable[:class:`int`]
            An iterable list/set/whatever of guild ID's that the application command should register to.
        dm_permission: :class:`bool`
            If the command should be usable in DMs or not. Setting to ``False`` will disable the command from being
            usable in DMs. Only for global commands, but will not error on guild.
        default_member_permissions: Optional[Union[:class:`Permissions`, :class:`int`]]
            Permission(s) required to use the command. Inputting ``8`` or ``Permissions(administrator=True)`` for
            example will only allow Administrators to use the command. If set to 0, nobody will be able to use it by
            default. Server owners CAN override the permission requirements.
        parent_cog: Optional[:class:`ClientCog`]
            ``ClientCog`` to forward to the callback as the ``self`` argument.
        force_global: :class:`bool`
            If this command should be registered as a global command, ALONG WITH all guild IDs set.
        """
        CallbackWrapperMixin.__init__(self, callback)
        CallbackMixin.__init__(self, callback=callback, parent_cog=parent_cog)
        self._state: Optional[ConnectionState] = None
        self.type = cmd_type or ApplicationCommandType(1)
        self.name: Optional[str] = name
        self.name_localizations: Optional[Dict[Union[str, Locale], str]] = name_localizations
        self._description: Optional[str] = description
        self.description_localizations: Optional[
            Dict[Union[str, Locale], str]
        ] = description_localizations
        self.guild_ids_to_rollout: Set[int] = set(guild_ids) if guild_ids else set()
        self.dm_permission: Optional[bool] = dm_permission
        self.default_member_permissions: Optional[
            Union[Permissions, int]
        ] = default_member_permissions

        self.force_global: bool = force_global

        self.command_ids: Dict[Optional[int], int] = {}
        """
        Dict[Optional[:class:`int`], :class:`int`]:
            Command IDs that this application command currently has. Schema: {Guild ID (None for global): command ID}
        """
        self.options: Dict[str, ApplicationCommandOption] = {}

    # Simple-ish getter + setter methods.

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Retrieves the fully qualified command name.

        .. versionadded:: 2.1
        """
        return str(self.name)

    @property
    def description(self) -> str:
        """The description the command should have in Discord. Should be 1-100 characters long."""
        return self._description or DEFAULT_SLASH_DESCRIPTION

    @description.setter
    def description(self, new_description: str):
        self._description = new_description

    @property
    def is_guild(self) -> bool:
        """:class:`bool`: Returns ``True`` if this command is or should be registered to any guilds."""
        guild_only_ids = set(self.command_ids.keys())
        guild_only_ids.discard(None)
        return True if (self.guild_ids_to_rollout or guild_only_ids) else False

    @property
    def guild_ids(self) -> Set[int]:
        """Returns a :class:`set` containing all guild ID's this command is registered to."""
        # TODO Is this worthwhile?
        guild_only_ids = set(self.command_ids.keys())
        guild_only_ids.discard(None)
        # ignore explanation: Mypy says that guild_only_ids can contain None due to self.command_ids.keys() having
        #  None being typehinted, but we remove None before returning it.
        return guild_only_ids  # type: ignore

    def add_guild_rollout(self, guild: Union[int, Guild]) -> None:
        """Adds a Guild to the command to be rolled out to when the rollout is run.

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

        self.guild_ids_to_rollout.add(guild_id)

    @property
    def is_global(self) -> bool:
        """:class:`bool`: Returns ``True`` if this command is or should be a global command."""
        return (
            True if (self.force_global or not self.is_guild or None in self.command_ids) else False
        )

    def get_signature(
        self, guild_id: Optional[int] = None
    ) -> Tuple[Optional[str], int, Optional[int]]:
        """Returns a command signature with the given guild ID.

        Parameters
        ----------
        guild_id: Optional[:class:`None`]
            Guild ID to make the signature for. If set to ``None``, it acts as a global command signature.

        Returns
        -------
        Tuple[:class:`str`, :class:`int`, Optional[:class:`int`]]
            A tuple that acts as a signature made up of the name, type, and guild ID.
        """
        # noinspection PyUnresolvedReferences
        return self.name, self.type.value, guild_id

    def get_rollout_signatures(self) -> Set[Tuple[str, int, Optional[int]]]:
        """Returns all signatures that this command wants to roll out to.

        Command signatures are made up of the command name, command type, and Guild ID (``None`` for global).

        Returns
        -------
        Set[Tuple[:class:`str`, :class:`int`, Optional[:class:`int`]]]
            A set of tuples that act as signatures.
        """
        ret = set()
        if self.is_global:
            ret.add(self.get_signature(None))

        for guild_id in self.guild_ids_to_rollout:
            ret.add(self.get_signature(guild_id))

        return ret

    def get_signatures(self) -> Set[Tuple[str, int, Optional[int]]]:
        """Returns all the signatures that this command has.

        Command signatures are made up of the command name, command type, and Guild ID (``None`` for global).

        Returns
        -------
        Set[Tuple[:class:`str`, :class:`int`, Optional[:class:`int`]]]
            A set of tuples that act as signatures.
        """
        ret = set()
        if self.is_global:
            ret.add(self.get_signature(None))

        if self.is_guild:
            for guild_id in self.guild_ids:
                ret.add(self.get_signature(guild_id))

        return ret

    def get_name_localization_payload(self) -> Optional[Dict[str, str]]:
        if self.name_localizations:
            ret = {}
            for locale, name in self.name_localizations.items():
                if isinstance(locale, Locale):
                    # noinspection PyUnresolvedReferences
                    ret[locale.value] = name
                else:
                    ret[locale] = name
            return ret
        else:
            return None

    def get_description_localization_payload(self) -> Optional[dict]:
        if self.description_localizations:
            ret = {}
            for locale, description in self.description_localizations.items():
                if isinstance(locale, Locale):
                    # noinspection PyUnresolvedReferences
                    ret[locale.value] = description
                else:
                    ret[locale] = description
            return ret
        else:
            return None

    def get_default_member_permissions_value(self) -> Optional[int]:
        if (
            isinstance(self.default_member_permissions, int)
            or self.default_member_permissions is None
        ):
            return self.default_member_permissions
        else:
            return self.default_member_permissions.value

    def get_payload(self, guild_id: Optional[int]) -> dict:
        """Makes an Application Command payload for this command to upsert to Discord with the given Guild ID.

        Parameters
        ----------
        guild_id: Optional[:class:`int`]
            Guild ID that this payload is for. If set to ``None``, it will be a global command payload instead.

        Returns
        -------
        :class:`dict`
            Dictionary payload to upsert to Discord.
        """
        # Below is to make PyCharm stop complaining that self.type.value isn't valid.
        # noinspection PyUnresolvedReferences
        ret = {
            "type": self.type.value,
            "name": str(
                self.name
            ),  # Might as well stringify the name, will come in handy if people try using numbers.
            "description": str(self.description),  # Might as well do the same with the description.
            "name_localizations": self.get_name_localization_payload(),
            "description_localizations": self.get_description_localization_payload(),
        }

        if self.default_member_permissions is not None:
            # While Discord accepts it as an int, they will respond back with the permissions value as a string because
            #  the permissions bitfield can get too big for them. Stringify it for easy payload-comparison.
            ret["default_member_permissions"] = str(self.get_default_member_permissions_value())

        if guild_id:  # Guild-command specific payload options.
            ret["guild_id"] = guild_id
        else:  # Global command specific payload options.
            if self.dm_permission is not None:
                ret["dm_permission"] = self.dm_permission
            else:
                # Discord seems to send back the DM permission as True regardless if we sent it or not, so we send as
                #  the default (True) to ensure payload parity for comparisons.
                ret["dm_permission"] = True

        return ret

    def parse_discord_response(
        self,
        state: ConnectionState,
        data: Union[ApplicationCommandInteractionData, ApplicationCommandPayload],
    ) -> None:
        """Parses the application command creation/update response from Discord.

        Parameters
        ----------
        state: :class:`ConnectionState`
            Connection state to use internally in the command.
        data: Union[:class:`ApplicationCommandInteractionData`, :class:`ApplicationCommand`]
            Raw dictionary data from Discord.
        """
        self._state = state
        command_id = int(data["id"])
        if guild_id := data.get("guild_id", None):
            guild_id = int(guild_id)
            self.command_ids[guild_id] = command_id
            self.guild_ids_to_rollout.add(guild_id)
        else:
            self.command_ids[None] = command_id

    def is_payload_valid(
        self, raw_payload: ApplicationCommandPayload, guild_id: Optional[int] = None
    ) -> bool:
        """Checks if the given raw application command interaction payload from Discord is possibly valid for
        this command.
        Note that while this may return ``True`` for a given payload, that doesn't mean that the payload is fully
        correct for this command. Discord doesn't send data for parameters that are optional and aren't supplied by
        the user.

        Parameters
        ----------
        raw_payload: :class:`dict`
            Application command interaction payload from Discord.
        guild_id: Optional[:class:`int`]
            Guild ID that the payload is from. If it's from a global command, this should be ``None``

        Returns
        -------
        :class:`bool`
            ``True`` if the given payload is possibly valid for this command. ``False`` otherwise.
        """
        cmd_payload = self.get_payload(guild_id)
        if cmd_payload.get("guild_id", 0) != int(raw_payload.get("guild_id", 0)):
            _log.debug("Guild ID doesn't match raw payload, not valid payload.")
            return False

        if not check_dictionary_values(
            cmd_payload,
            raw_payload,  # type: ignore  # specificity of typeddicts doesnt matter in validation
            "default_member_permissions",
            "description",
            "type",
            "name",
            "name_localizations",
            "description_localizations",
            "dm_permission",
        ):
            _log.debug("Failed check dictionary values, not valid payload.")
            return False

        if len(cmd_payload.get("options", [])) != len(raw_payload.get("options", [])):
            _log.debug("Option amount between commands not equal, not valid payload.")
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
                    if not deep_dictionary_check(cmd_option, raw_option):  # type: ignore
                        # its a dict check so typeddicts do not matter
                        _log.debug("Options failed deep dictionary checks, not valid payload.")
                        return False

                    break

            if not found_correct_value:
                _log.debug("Discord is missing an option we have, not valid payload.")
                return False

        return True

    def is_interaction_valid(self, interaction: Interaction) -> bool:
        """Checks if the interaction given is possibly valid for this command.
        If the command has more parameters (especially optionals) than the interaction coming in, this may cause a
        desync between your bot and Discord.

        Parameters
        ----------
        interaction: :class:`Interaction`
            Interaction to validate.

        Returns
        -------
        :class:`bool`
            ``True`` If the interaction could possibly be for this command, ``False`` otherwise.
        """
        data = interaction.data

        if data is None:
            raise ValueError("Discord did not provide us with interaction data")

        our_payload = self.get_payload(data.get("guild_id", None))

        def _recursive_subcommand_check(inter_pos: dict, cmd_pos: dict) -> bool:
            """A small recursive wrapper that checks for subcommand(s) (group(s)).

            Parameters
            ----------
            inter_pos: :class:`dict`
                Current command position from the payload in the interaction.
            cmd_pos: :class:`dict`
                Current command position from the payload for the local command.

            Returns
            -------
            :class:`bool`
                ``True`` if the payloads match, ``False`` otherwise.
            """
            inter_options = inter_pos.get("options")
            cmd_options = cmd_pos.get("options", {})

            if inter_options is None:
                raise ValueError("Interaction options was not provided")

            our_options = {opt["name"]: opt for opt in cmd_options}
            if (
                len(inter_options) == 1
                and (  # If the length is only 1, it might be a subcommand (group).
                    inter_options[0]["type"]
                    in (
                        ApplicationCommandOptionType.sub_command.value,
                        ApplicationCommandOptionType.sub_command_group.value,
                    )
                )
                and (  # This checks if it's a subcommand (group).
                    found_opt := our_options.get(
                        inter_options[0]["name"]
                    )  # This checks if the name matches an option.
                )
                and inter_options[0]["type"] == found_opt["type"]
            ):  # And this makes sure both are the same type.
                return _recursive_subcommand_check(
                    inter_options[0], found_opt
                )  # If all of the above pass, recurse.
            else:
                # It isn't a subcommand (group), run normal option checks.
                return _option_check(inter_options, cmd_options)

        def _option_check(inter_options: dict, cmd_options: dict) -> bool:
            """Checks if the two given command payloads have matching options.

            Parameters
            ----------
            inter_options: :class`dict`
                Command option data from the interaction.
            cmd_options: :class:`dict`
                Command option data from the local command.

            Returns
            -------
            :class:`bool`
                ``True`` if the options match, ``False`` otherwise.
            """
            all_our_options = {}
            required_options = {}
            for our_opt in cmd_options:
                all_our_options[our_opt["name"]] = our_opt
                if our_opt.get("required"):
                    required_options[our_opt["name"]] = our_opt

            all_inter_options = {inter_opt["name"]: inter_opt for inter_opt in inter_options}

            if len(all_our_options) >= len(all_inter_options):
                # If we have more options (including options) than the interaction, we are good to proceed.
                all_our_options_copy = all_our_options.copy()
                all_inter_options_copy = all_inter_options.copy()
                # Begin checking required options.
                for our_opt_name, our_opt in required_options.items():
                    if inter_opt := all_inter_options.get(our_opt_name):
                        if (
                            inter_opt["name"] == our_opt["name"]
                            and inter_opt["type"] == our_opt["type"]
                        ):
                            all_our_options_copy.pop(our_opt_name)
                            all_inter_options_copy.pop(our_opt_name)
                        else:
                            _log.debug(
                                "%s Required option don't match name and/or type.", self.error_name
                            )
                            return False  # Options don't match name and/or type.

                    else:
                        _log.debug("%s Inter missing required option.", self.error_name)
                        return False  # Required option wasn't found.
                # Begin checking optional arguments.
                for (
                    inter_opt_name,
                    inter_opt,
                ) in all_inter_options_copy:  # Should only contain optionals now.
                    if our_opt := all_our_options_copy.get(inter_opt_name):
                        if not (
                            inter_opt["name"] == our_opt["name"]
                            and inter_opt["type"] == our_opt["type"]
                        ):
                            _log.debug(
                                "%s Optional option don't match name and/or type.", self.error_name
                            )
                            return False  # Options don't match name and/or type.

                    else:
                        _log.debug("%s Inter has option that we don't.", self.error_name)
                        return False  # They have an option name that we don't.

            else:
                _log.debug(
                    "%s We have less options than them: %s vs %s",
                    self.error_name,
                    all_our_options,
                    all_inter_options,
                )
                return False  # Interaction has more options than we do.
            return True  # No checks failed.

        # caring  about typeddict specificity will cause issues down the line
        if not check_dictionary_values(our_payload, data, "name", "guild_id", "type"):  # type: ignore
            _log.debug("%s Failed basic dictionary check.", self.error_name)
            return False
        else:
            data_options = data.get("options")
            payload_options = our_payload.get("options")
            if data_options and payload_options:
                return _recursive_subcommand_check(data, our_payload)  # type: ignore
            elif data_options is None and payload_options is None:
                return True  # User and Message commands don't have options.
            else:
                _log.debug(
                    "%s Mismatch between data and payload options: %s vs %s",
                    self.error_name,
                    data_options,
                    payload_options,
                )
                # There is a mismatch between the two, fail it.
                return False

    def from_callback(
        self,
        callback: Optional[Callable] = None,
        option_class: Optional[Type[BaseCommandOption]] = BaseCommandOption,
    ) -> None:
        super().from_callback(callback=callback, option_class=option_class)

    async def call_from_interaction(self, interaction: Interaction) -> None:
        """|coro|
        Calls the callback via the given :class:`Interaction`, relying on the locally
        stored :class:`ConnectionState` object.

        Parameters
        ----------
        interaction: :class:`Interaction`
            Interaction corresponding to the use of the command.
        """
        await self.call(self._state, interaction)  # type: ignore

    async def call(self, state: ConnectionState, interaction: Interaction) -> None:
        """|coro|
        Calls the callback via the given :class:`Interaction`, using the given :class:`ConnectionState` to get resolved
        objects if needed and available.

        Parameters
        ----------
        state: :class:`ConnectionState`
            State object to get resolved objects from.
        interaction: :class:`Interaction`
            Interaction corresponding to the use of the command.
        """
        raise NotImplementedError

    def check_against_raw_payload(
        self, raw_payload: ApplicationCommandPayload, guild_id: Optional[int] = None
    ) -> bool:
        warnings.warn(
            ".check_against_raw_payload() is deprecated, please use .is_payload_valid instead.",
            stacklevel=2,
            category=FutureWarning,
        )
        return self.is_payload_valid(raw_payload, guild_id)

    def get_guild_payload(self, guild_id: int):
        warnings.warn(
            ".get_guild_payload is deprecated, use .get_payload(guild_id) instead.",
            stacklevel=2,
            category=FutureWarning,
        )
        return self.get_payload(guild_id)

    @property
    def global_payload(self) -> dict:
        warnings.warn(
            ".global_payload is deprecated, use .get_payload(None) instead.",
            stacklevel=2,
            category=FutureWarning,
        )
        return self.get_payload(None)


class SlashApplicationSubcommand(SlashCommandMixin, AutocompleteCommandMixin, CallbackWrapperMixin):
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        *,
        cmd_type: ApplicationCommandOptionType,
        name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        description_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        callback: Optional[Callable] = None,
        parent_cmd: Union[SlashApplicationCommand, SlashApplicationSubcommand, None] = None,
        parent_cog: Optional[ClientCog] = None,
        inherit_hooks: bool = False,
    ):
        """Slash Application Subcommand, supporting additional subcommands and autocomplete.

        Parameters
        ----------
        name: :class:`str`
            Name of the subcommand (group). No capital letters or spaces. Defaults to the name of the callback.
        name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Name(s) of the subcommand for users of specific locales. The locale code should be the key, with the
            localized name as the value.
        description: :class:`str`
            Description of the subcommand (group). Must be between 1-100 characters. If not provided, a default value
            will be given.
        description_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Description(s) of the subcommand for users of specific locales. The locale code should be the key, with the
            localized description as the value.
        callback: :class:`str`
            Callback to create the command from, and run when the command is called. If provided, it
            must be a coroutine. If this subcommand has subcommands, the callback will never be called.
        parent_cmd: Union[:class:`SlashApplicationCommand`, :class:`SlashApplicationSubcommand`]
            Parent (sub)command for this subcommand.
        cmd_type: :class:`ApplicationCommandOptionType`
            Should either be ``ApplicationCommandOptionType.sub_command`` or
            ``ApplicationCommandOptionType.sub_command_group``
        parent_cog: Optional[:class:`ClientCog`]
            Parent cog for the callback, if it exists. If provided, it will be given to the callback as ``self``.
        inherit_hooks: :class:`bool`
            If this subcommand should inherit the parent (sub)commands ``before_invoke`` and ``after_invoke`` callbacks.
            Defaults to ``False``..
        """
        SlashCommandMixin.__init__(self, callback=callback, parent_cog=parent_cog)
        AutocompleteCommandMixin.__init__(self, parent_cog)
        CallbackWrapperMixin.__init__(self, callback)

        self.name: Optional[str] = name
        self.name_localizations: Optional[Dict[Union[str, Locale], str]] = name_localizations
        self._description: Optional[str] = description
        self.description_localizations: Optional[
            Dict[Union[str, Locale], str]
        ] = description_localizations
        self.type = cmd_type
        self.parent_cmd = parent_cmd
        self._inherit_hooks: bool = inherit_hooks

        self.options: Dict[str, SlashCommandOption] = {}
        self.children: Dict[str, SlashApplicationSubcommand] = {}

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Retrieve the command name including all parents space separated.

        An example of the output would be ``parent group subcommand``.

        .. versionadded:: 2.1
        """
        return (
            f"{self.parent_cmd.qualified_name} {self.name}" if self.parent_cmd else str(self.name)
        )

    async def call(
        self, state: ConnectionState, interaction: Interaction, option_data: List[dict]
    ) -> None:
        """|coro|
        Calls the callback via the given :class:`Interaction`, using the given :class:`ConnectionState` to get resolved
        objects if needed and available and the given option data.

        Parameters
        ----------
        state: :class:`ConnectionState`
            State object to get resolved objects from.
        interaction: :class:`Interaction`
            Interaction corresponding to the use of the subcommand.
        option_data: List[:class:`dict`]
            List of raw option data from Discord.
        """
        if self.children:
            await self.children[option_data[0]["name"]].call(
                state, interaction, option_data[0].get("options", {})
            )
        else:
            await self.call_slash(state, interaction, option_data)

    def get_name_localization_payload(self) -> Optional[dict]:
        if self.name_localizations:
            ret = {}
            for locale, name in self.name_localizations.items():
                if isinstance(locale, Locale):
                    # noinspection PyUnresolvedReferences
                    ret[locale.value] = name
                else:
                    ret[locale] = name
            return ret
        else:
            return None

    def get_description_localization_payload(self) -> Optional[dict]:
        if self.description_localizations:
            ret = {}
            for locale, description in self.description_localizations.items():
                if isinstance(locale, Locale):
                    # noinspection PyUnresolvedReferences
                    ret[locale.value] = description
                else:
                    ret[locale] = description
            return ret
        else:
            return None

    @property
    def payload(self) -> dict:
        """Returns a dict payload made of the attributes of the subcommand (group) to be sent to Discord."""
        # noinspection PyUnresolvedReferences
        ret = {
            "type": self.type.value,
            "name": str(
                self.name
            ),  # Might as well stringify the name, will come in handy if people try using numbers.
            "description": str(self.description),  # Might as well do the same with the description.
            "name_localizations": self.get_name_localization_payload(),
            "description_localizations": self.get_description_localization_payload(),
        }

        if self.children:
            ret["options"] = [child.payload for child in self.children.values()]
        elif self.options:
            ret["options"] = [parameter.payload for parameter in self.options.values()]

        return ret

    def from_callback(
        self,
        callback: Optional[Callable] = None,
        option_class: Type[SlashCommandOption] = SlashCommandOption,
        call_children: bool = True,
    ) -> None:
        SlashCommandMixin.from_callback(self, callback=callback, option_class=option_class)
        if call_children:
            for child in self.children.values():
                child.from_callback(
                    callback=child.callback,
                    option_class=option_class,
                    call_children=call_children,
                )

        if self.error_callback is None:
            self.error_callback = self.parent_cmd.error_callback if self.parent_cmd else None

        if self._inherit_hooks and self.parent_cmd:
            self.checks.extend(self.parent_cmd.checks)
            self._callback_before_invoke = self.parent_cmd._callback_before_invoke
            self._callback_after_invoke = self.parent_cmd._callback_after_invoke

        super().from_autocomplete()
        CallbackWrapperMixin.modify(self)

    def subcommand(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        *,
        name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        description_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        inherit_hooks: bool = False,
    ) -> Callable[[Callable], SlashApplicationSubcommand]:
        """Takes the decorated callback and turns it into a :class:`SlashApplicationSubcommand` added as a subcommand.

        Parameters
        ----------
        name: :class:`str`
            Name of the command that users will see. If not set, it defaults to the name of the callback.
        description: :class:`str`
            Description of the command that users will see. If not specified, the docstring will be used.
            If no docstring is found for the command callback, it defaults to "No description provided".
        name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Name(s) of the command for users of specific locales. The locale code should be the key, with the localized
            name as the value.
        description_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Description(s) of the subcommand for users of specific locales. The locale code should be the key, with the
            localized description as the value.
        inherit_hooks: :class:`bool`
            If the subcommand should inherit the parent subcommands ``before_invoke`` and ``after_invoke`` callbacks.
            Defaults to ``False``.
        """

        def decorator(func: Callable) -> SlashApplicationSubcommand:
            ret = SlashApplicationSubcommand(
                name=name,
                name_localizations=name_localizations,
                description=description,
                description_localizations=description_localizations,
                callback=func,
                parent_cmd=self,
                cmd_type=ApplicationCommandOptionType.sub_command,
                parent_cog=self.parent_cog,
                inherit_hooks=inherit_hooks,
            )
            self.children[
                ret.name
                or (func.callback.__name__ if isinstance(func, CallbackWrapper) else func.__name__)
            ] = ret
            return ret

        if isinstance(
            self.parent_cmd, SlashApplicationSubcommand
        ):  # Discord limitation, no groups in groups.
            raise TypeError(
                f"{self.error_name} Subcommand groups cannot be nested inside subcommand groups."
            )

        self.type = ApplicationCommandOptionType.sub_command_group
        return decorator


class SlashApplicationCommand(SlashCommandMixin, BaseApplicationCommand, AutocompleteCommandMixin):
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        *,
        name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        description_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        callback: Optional[Callable] = None,
        guild_ids: Optional[Iterable[int]] = None,
        dm_permission: Optional[bool] = None,
        default_member_permissions: Optional[Union[Permissions, int]] = None,
        parent_cog: Optional[ClientCog] = None,
        force_global: bool = False,
    ):
        """Represents a Slash Application Command built from the given callback, able to be registered to multiple
        guilds or globally.

        Parameters
        ----------
        name: :class:`str`
            Name of the command. Must be lowercase with no spaces.
        description: :class:`str`
            Description of the command. Must be between 1 to 100 characters, or defaults to a set string.
        name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Name(s) of the subcommand for users of specific locales. The locale code should be the key, with the
            localized name as the value.
        description_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Description(s) of the subcommand for users of specific locales. The locale code should be the key, with the
            localized description as the value.
        callback: Callable
            Callback to make the application command from, and to run when the application command is called.
        guild_ids: Iterable[:class:`int`]
            An iterable list of guild ID's that the application command should register to.
        dm_permission: :class:`bool`
            If the command should be usable in DMs or not. Setting to ``False`` will disable the command from being
            usable in DMs. Only for global commands.
        default_member_permissions: Optional[Union[:class:`Permissions`, :class:`int`]]
            Permission(s) required to use the command. Inputting ``8`` or ``Permissions(administrator=True)`` for
            example will only allow Administrators to use the command. If set to 0, nobody will be able to use it by
            default. Server owners CAN override the permission requirements.
        parent_cog: Optional[:class:`ClientCog`]
            ``ClientCog`` to forward to the callback as the ``self`` argument.
        force_global: :class:`bool`
            If this command should be registered as a global command, ALONG WITH all guild IDs set.
        """
        BaseApplicationCommand.__init__(
            self,
            name=name,
            name_localizations=name_localizations,
            description=description,
            description_localizations=description_localizations,
            callback=callback,
            cmd_type=ApplicationCommandType.chat_input,
            guild_ids=guild_ids,
            default_member_permissions=default_member_permissions,
            dm_permission=dm_permission,
            parent_cog=parent_cog,
            force_global=force_global,
        )
        AutocompleteCommandMixin.__init__(self, parent_cog=parent_cog)
        SlashCommandMixin.__init__(self, callback=callback, parent_cog=parent_cog)

    @property
    def description(self) -> str:
        return super().description  # Required to grab the correct description function.

    @description.setter
    def description(self, new_desc: str):
        self._description = new_desc

    def get_payload(self, guild_id: Optional[int]):
        ret = super().get_payload(guild_id)
        if self.children:
            ret["options"] = [child.payload for child in self.children.values()]
        else:
            ret["options"] = [parameter.payload for parameter in self.options.values()]
        return ret

    async def call(self, state: ConnectionState, interaction: Interaction) -> None:
        if interaction.data is None:
            raise ValueError("Discord did not provide us interaction data")

        # pyright does not want to lose typeddict specificity but we do not care here
        option_data = interaction.data.get("options", [])

        if self.children:
            if not option_data:
                raise ValueError("Discord did not provide us any options data")

            await self.children[option_data[0]["name"]].call(
                state, interaction, option_data[0].get("options", [])
            )
        else:
            await self.call_slash(state, interaction, option_data)

    def from_callback(
        self,
        callback: Optional[Callable] = None,
        option_class: Type[SlashCommandOption] = SlashCommandOption,
        call_children: bool = True,
    ):
        BaseApplicationCommand.from_callback(self, callback=callback, option_class=option_class)
        SlashCommandMixin.from_callback(self, callback=callback)
        AutocompleteCommandMixin.from_autocomplete(self)
        if call_children and self.children:
            for child in self.children.values():
                child.from_callback(
                    callback=child.callback, option_class=option_class, call_children=call_children
                )

        CallbackWrapperMixin.modify(self)

    def subcommand(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        *,
        name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        description_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        inherit_hooks: bool = False,
    ) -> Callable[[Callable], SlashApplicationSubcommand]:
        """Takes the decorated callback and turns it into a :class:`SlashApplicationSubcommand` added as a subcommand.

        Parameters
        ----------
        name: :class:`str`
            Name of the command that users will see. If not set, it defaults to the name of the callback.
        description: :class:`str`
            Description of the command that users will see. If not specified, the docstring will be used.
            If no docstring is found for the command callback, it defaults to "No description provided".
        name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Name(s) of the command for users of specific locales. The locale code should be the key, with the localized
            name as the value.
        description_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Description(s) of the subcommand for users of specific locales. The locale code should be the key, with the
            localized description as the value.
        inherit_hooks: :class:`bool`
            If the subcommand should inherit the parent commands ``before_invoke`` and ``after_invoke`` callbacks.
            Defaults to ``False``.
        """

        def decorator(func: Callable) -> SlashApplicationSubcommand:
            ret = SlashApplicationSubcommand(
                name=name,
                name_localizations=name_localizations,
                description=description,
                description_localizations=description_localizations,
                callback=func,
                parent_cmd=self,
                cmd_type=ApplicationCommandOptionType.sub_command,
                parent_cog=self.parent_cog,
                inherit_hooks=inherit_hooks,
            )
            self.children[
                ret.name
                or (func.callback.__name__ if isinstance(func, CallbackWrapper) else func.__name__)
            ] = ret
            return ret

        return decorator


class UserApplicationCommand(BaseApplicationCommand):
    def __init__(
        self,
        name: Optional[str] = None,
        *,
        name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        callback: Optional[Callable] = None,
        guild_ids: Optional[Iterable[int]] = None,
        dm_permission: Optional[bool] = None,
        default_member_permissions: Optional[Union[Permissions, int]] = None,
        parent_cog: Optional[ClientCog] = None,
        force_global: bool = False,
    ):
        """Represents a User Application Command that will give the user to the given callback, able to be registered to
        multiple guilds or globally.

        Parameters
        ----------
        name: :class:`str`
            Name of the command. Can be uppercase with spaces.
        name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Name(s) of the subcommand for users of specific locales. The locale code should be the key, with the
            localized name as the value.
        callback: Callable
            Callback to run with the application command is called.
        guild_ids: Iterable[:class:`int`]
            An iterable list of guild ID's that the application command should register to.
        dm_permission: :class:`bool`
            If the command should be usable in DMs or not. Setting to ``False`` will disable the command from being
            usable in DMs. Only for global commands, but will not error on guild.
        default_member_permissions: Optional[Union[:class:`Permissions`, :class:`int`]]
            Permission(s) required to use the command. Inputting ``8`` or ``Permissions(administrator=True)`` for
            example will only allow Administrators to use the command. If set to 0, nobody will be able to use it by
            default. Server owners CAN override the permission requirements.
        parent_cog: Optional[:class:`ClientCog`]
            ``ClientCog`` to forward to the callback as the ``self`` argument.
        force_global: :class:`bool`
            If this command should be registered as a global command, ALONG WITH all guild IDs set.
        """
        super().__init__(
            name=name,
            name_localizations=name_localizations,
            description="",
            callback=callback,
            cmd_type=ApplicationCommandType.user,
            guild_ids=guild_ids,
            dm_permission=dm_permission,
            default_member_permissions=default_member_permissions,
            parent_cog=parent_cog,
            force_global=force_global,
        )

    @property
    def description(self) -> str:
        return ""

    @description.setter
    def description(self, new_desc: str):
        raise ValueError("UserApplicationCommands cannot have a description set.")

    async def call(self, state: ConnectionState, interaction: Interaction):
        await self.invoke_callback_with_hooks(
            state, interaction, get_users_from_interaction(state, interaction)[0]
        )

    def from_callback(
        self,
        callback: Optional[Callable] = None,
        option_class: Optional[Type[BaseCommandOption]] = None,
    ):
        super().from_callback(callback, option_class=option_class)
        CallbackWrapperMixin.modify(self)


class MessageApplicationCommand(BaseApplicationCommand):
    def __init__(
        self,
        name: Optional[str] = None,
        *,
        name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
        callback: Optional[Callable] = None,
        guild_ids: Optional[Iterable[int]] = None,
        dm_permission: Optional[bool] = None,
        default_member_permissions: Optional[Union[Permissions, int]] = None,
        parent_cog: Optional[ClientCog] = None,
        force_global: bool = False,
    ):
        """Represents a Message Application Command that will give the message to the given callback, able to be
        registered to multiple guilds or globally.

        Parameters
        ----------
        name: :class:`str`
            Name of the command. Can be uppercase with spaces.
        name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
            Name(s) of the subcommand for users of specific locales. The locale code should be the key, with the
            localized name as the value.
        callback: Callable
            Callback to run with the application command is called.
        guild_ids: Iterable[:class:`int`]
            An iterable list of guild ID's that the application command should register to.
        dm_permission: :class:`bool`
            If the command should be usable in DMs or not. Setting to ``False`` will disable the command from being
            usable in DMs. Only for global commands, but will not error on guild.
        default_member_permissions: Optional[Union[:class:`Permissions`, :class:`int`]]
            Permission(s) required to use the command. Inputting ``8`` or ``Permissions(administrator=True)`` for
            example will only allow Administrators to use the command. If set to 0, nobody will be able to use it by
            default. Server owners CAN override the permission requirements.
        parent_cog: Optional[:class:`ClientCog`]
            ``ClientCog`` to forward to the callback as the ``self`` argument.
        force_global: :class:`bool`
            If this command should be registered as a global command, ALONG WITH all guild IDs set.
        """
        super().__init__(
            name=name,
            name_localizations=name_localizations,
            description="",
            callback=callback,
            cmd_type=ApplicationCommandType.message,
            guild_ids=guild_ids,
            dm_permission=dm_permission,
            default_member_permissions=default_member_permissions,
            parent_cog=parent_cog,
            force_global=force_global,
        )

    @property
    def description(self) -> str:
        return ""

    @description.setter
    def description(self, new_desc: str):
        raise ValueError("MessageApplicationCommands cannot have a description set.")

    async def call(self, state: ConnectionState, interaction: Interaction):
        await self.invoke_callback_with_hooks(
            state, interaction, get_messages_from_interaction(state, interaction)[0]
        )

    def from_callback(
        self,
        callback: Optional[Callable] = None,
        option_class: Optional[Type[BaseCommandOption]] = None,
    ):
        super().from_callback(callback, option_class=option_class)
        CallbackWrapperMixin.modify(self)


def slash_command(
    name: Optional[str] = None,
    description: Optional[str] = None,
    *,
    name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
    description_localizations: Optional[Dict[Union[Locale, str], str]] = None,
    guild_ids: Optional[Iterable[int]] = None,
    dm_permission: Optional[bool] = None,
    default_member_permissions: Optional[Union[Permissions, int]] = None,
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
    name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
        Name(s) of the command for users of specific locales. The locale code should be the key, with the localized
        name as the value.
    description_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
        Description(s) of the subcommand for users of specific locales. The locale code should be the key, with the
        localized description as the value.
    guild_ids: Iterable[:class:`int`]
        IDs of :class:`Guild`'s to add this command to. If unset, this will be a global command.
    dm_permission: :class:`bool`
        If the command should be usable in DMs or not. Setting to ``False`` will disable the command from being
        usable in DMs. Only for global commands, but will not error on guild.
    default_member_permissions: Optional[Union[:class:`Permissions`, :class:`int`]]
        Permission(s) required to use the command. Inputting ``8`` or ``Permissions(administrator=True)`` for
        example will only allow Administrators to use the command. If set to 0, nobody will be able to use it by
        default. Server owners CAN override the permission requirements.
    force_global: :class:`bool`
        If True, will force this command to register as a global command, even if `guild_ids` is set. Will still
        register to guilds. Has no effect if `guild_ids` are never set or added to.
    """

    def decorator(func: Callable) -> SlashApplicationCommand:
        if isinstance(func, BaseApplicationCommand):
            raise TypeError("Callback is already an application command.")

        app_cmd = SlashApplicationCommand(
            callback=func,
            name=name,
            name_localizations=name_localizations,
            description=description,
            description_localizations=description_localizations,
            guild_ids=guild_ids,
            dm_permission=dm_permission,
            default_member_permissions=default_member_permissions,
            force_global=force_global,
        )
        return app_cmd

    return decorator


def message_command(
    name: Optional[str] = None,
    *,
    name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
    guild_ids: Optional[Iterable[int]] = None,
    dm_permission: Optional[bool] = None,
    default_member_permissions: Optional[Union[Permissions, int]] = None,
    force_global: bool = False,
):
    """Creates a Message context command from the decorated function.
    Used inside :class:`ClientCog`'s or something that subclasses it.

    Parameters
    ----------
    name: :class:`str`
        Name of the command that users will see. If not set, it defaults to the name of the callback.
    name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
        Name(s) of the command for users of specific locales. The locale code should be the key, with the localized
        name as the value
    guild_ids: Iterable[:class:`int`]
        IDs of :class:`Guild`'s to add this command to. If unset, this will be a global command.
    dm_permission: :class:`bool`
        If the command should be usable in DMs or not. Setting to ``False`` will disable the command from being
        usable in DMs. Only for global commands, but will not error on guild.
    default_member_permissions: Optional[Union[:class:`Permissions`, :class:`int`]]
        Permission(s) required to use the command. Inputting ``8`` or ``Permissions(administrator=True)`` for
        example will only allow Administrators to use the command. If set to 0, nobody will be able to use it by
        default. Server owners CAN override the permission requirements.
    force_global: :class:`bool`
        If True, will force this command to register as a global command, even if `guild_ids` is set. Will still
        register to guilds. Has no effect if `guild_ids` are never set or added to.
    """

    def decorator(func: Callable) -> MessageApplicationCommand:
        if isinstance(func, BaseApplicationCommand):
            raise TypeError("Callback is already an application command.")

        app_cmd = MessageApplicationCommand(
            callback=func,
            name=name,
            name_localizations=name_localizations,
            guild_ids=guild_ids,
            dm_permission=dm_permission,
            default_member_permissions=default_member_permissions,
            force_global=force_global,
        )
        return app_cmd

    return decorator


def user_command(
    name: Optional[str] = None,
    *,
    name_localizations: Optional[Dict[Union[Locale, str], str]] = None,
    guild_ids: Optional[Iterable[int]] = None,
    dm_permission: Optional[bool] = None,
    default_member_permissions: Optional[Union[Permissions, int]] = None,
    force_global: bool = False,
):
    """Creates a User context command from the decorated function.
    Used inside :class:`ClientCog`'s or something that subclasses it.

    Parameters
    ----------
    name: :class:`str`
        Name of the command that users will see. If not set, it defaults to the name of the callback.
    name_localizations: Dict[Union[:class:`Locale`, :class:`str`], :class:`str`]
        Name(s) of the command for users of specific locales. The locale code should be the key, with the localized
        name as the value
    guild_ids: Iterable[:class:`int`]
        IDs of :class:`Guild`'s to add this command to. If unset, this will be a global command.
    dm_permission: :class:`bool`
        If the command should be usable in DMs or not. Setting to ``False`` will disable the command from being
        usable in DMs. Only for global commands, but will not error on guild.
    default_member_permissions: Optional[Union[:class:`Permissions`, :class:`int`]]
        Permission(s) required to use the command. Inputting ``8`` or ``Permissions(administrator=True)`` for
        example will only allow Administrators to use the command. If set to 0, nobody will be able to use it by
        default. Server owners CAN override the permission requirements.
    force_global: :class:`bool`
        If True, will force this command to register as a global command, even if `guild_ids` is set. Will still
        register to guilds. Has no effect if `guild_ids` are never set or added to.
    """

    def decorator(func: Callable) -> UserApplicationCommand:
        if isinstance(func, BaseApplicationCommand):
            raise TypeError("Callback is already an application command.")

        app_cmd = UserApplicationCommand(
            callback=func,
            name=name,
            name_localizations=name_localizations,
            guild_ids=guild_ids,
            dm_permission=dm_permission,
            default_member_permissions=default_member_permissions,
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
            _log.debug(
                "Failed basic dictionary value check for key %s:\n %s vs %s",
                keyword,
                dict1.get(keyword, None),
                dict2.get(keyword, None),
            )
            return False

    return True


def deep_dictionary_check(dict1: dict, dict2: dict) -> bool:
    """Used to check if all keys and values between two dicts are equal, and recurses if it encounters a nested dict."""
    if dict1.keys() != dict2.keys():
        _log.debug(
            "Dict1 and Dict2 keys are not equal, not valid payload.\n %s vs %s",
            dict1.keys(),
            dict2.keys(),
        )
        return False

    for key in dict1:
        if (
            isinstance(dict1[key], dict)
            and isinstance(dict2[key], dict)
            and not deep_dictionary_check(dict1[key], dict2[key])
        ):
            return False
        elif dict1[key] != dict2[key]:
            _log.debug(
                "Dict1 and Dict2 values are not equal, not valid payload.\n Key: %s, values %s vs %s",
                key,
                dict1[key],
                dict2[key],
            )
            return False

    return True


def get_users_from_interaction(
    state: ConnectionState, interaction: Interaction
) -> List[Union[User, Member]]:
    """Tries to get a list of resolved :class:`User` objects from the interaction data.

    If possible, it will get resolved :class:`Member` objects instead.

    Parameters
    ----------
    state: :class:`ConnectionState`
        State object to construct members with.
    interaction: :class:`Interaction`
        Interaction object to attempt to get users/members from.

    Returns
    -------
    List[Union[:class:`User`, :class:`Member`]]
        List of resolved users, or members if possible
    """
    data = interaction.data
    ret: List[Union[User, Member]] = []

    data = cast(ApplicationCommandInteractionData, data)

    if data is None:
        raise ValueError("Discord did not provide us with interaction data")

    # Return a Member object if the required data is available, otherwise fall back to User.
    if "resolved" in data and "members" in data["resolved"]:
        member_payloads = data["resolved"]["members"]
        # Because the payload is modified further down, a copy is made to avoid affecting methods or
        #  users that read from interaction.data further down the line.
        for member_id, member_payload in member_payloads.copy().items():
            if interaction.guild is None:
                raise TypeError("Cannot resolve members if Interaction.guild is None")

            # If a member isn't in the cache, construct a new one.
            if (
                not (member := interaction.guild.get_member(int(member_id)))
                and "users" in data["resolved"]
            ):
                user_payload = data["resolved"]["users"][member_id]
                # This is required to construct the Member.
                member_payload["user"] = user_payload
                member = Member(data=member_payload, guild=interaction.guild, state=state)  # type: ignore
                interaction.guild._add_member(member)

            if member is not None:
                ret.append(member)

    elif "resolved" in data and "users" in data["resolved"]:
        resolved_users_payload = data["resolved"]["users"]
        ret = [state.store_user(user_payload) for user_payload in resolved_users_payload.values()]

    return ret


def get_messages_from_interaction(
    state: ConnectionState, interaction: Interaction
) -> List[Message]:
    """Tries to get a list of resolved :class:`Message` objects from the interaction data.

    Parameters
    ----------
    state: :class:`ConnectionState`
        State object to construct messages with.
    interaction: :class:`Interaction`
        Interaction object to attempt to get resolved messages from.

    Returns
    -------
    List[:class:`Message`]
        A list of resolved messages.
    """
    data = interaction.data
    ret = []

    data = cast(ApplicationCommandInteractionData, data)

    if data is None:
        raise ValueError("Discord did not provide us with interaction data")

    if "resolved" in data and "messages" in data["resolved"]:
        message_payloads = data["resolved"]["messages"]
        for msg_id, msg_payload in message_payloads.items():
            if not (message := state._get_message(int(msg_id))):
                message = Message(channel=interaction.channel, data=msg_payload, state=state)  # type: ignore  # interaction.channel can be VoiceChannel somehow

            ret.append(message)

    return ret


def get_roles_from_interaction(state: ConnectionState, interaction: Interaction) -> List[Role]:
    """Tries to get a list of resolved :class:`Role` objects from the interaction .data

    Parameters
    ----------
    state: :class:`ConnectionState`
        State object to construct roles with.
    interaction: :class:`Interaction`
        Interaction object to attempt to get resolved roles from.

    Returns
    -------
    List[:class:`Role`]
        A list of resolved roles.
    """
    data = interaction.data
    ret = []

    if data is None:
        raise ValueError("Discord did not provide us with interaction data")

    data = cast(ApplicationCommandInteractionData, data)

    if "resolved" in data and "roles" in data["resolved"]:
        role_payloads = data["resolved"]["roles"]
        for role_id, role_payload in role_payloads.items():
            # if True:  # Use this for testing payload -> Role
            if interaction.guild is None:
                raise TypeError("Interaction.guild is None when resolving a Role")

            if not (role := interaction.guild.get_role(int(role_id))):
                role = Role(guild=interaction.guild, state=state, data=role_payload)

            ret.append(role)

    return ret


def unpack_annotated(given_annotation: Any, resolve_list: list[type] = []) -> type:
    """Takes an annotation. If the origin is Annotated, it will attempt to resolve it using the given list of accepted
    types, going from the last type and working up to the first. If no matches to the given list is found, the last
    type specified in the Annotated typehint will be returned.

    If the origin is not Annotated, the typehint will be returned as-is.

    Parameters
    ----------
    given_annotation
        Annotation to attempt to resolve.
    resolve_list
        List of types the annotation can resolve to.

    Returns
    -------
    :class:`type`
        Resolved annotation.
    """
    # origin = typing.get_origin(given_annotation)  # TODO: Once Python 3.10 is standard, use this.
    origin = typing_extensions.get_origin(given_annotation)
    if origin is Annotated:
        located_annotation = MISSING
        # arg_list = typing.get_args(given_annotation)  # TODO: Once Python 3.10 is standard, use this
        arg_list = typing_extensions.get_args(given_annotation)
        for arg in arg_list[1:]:
            if arg in resolve_list:
                located_annotation = arg
                break

        if located_annotation is MISSING:
            located_annotation = arg_list[-1]

        return located_annotation
    else:
        return given_annotation


def unpack_annotation(
    given_annotation: Any, annotated_list: List[type] = []
) -> Tuple[List[type], list]:
    """Unpacks the given parameter annotation into its components.

    Parameters
    ----------
    given_annotation: Any
        Given annotation to unpack. Should be from ``parameter.annotation``
    annotated_list: List[:class:`type`]
        List that the ``Annotated`` annotation should attempt to resolve to, from the 2nd arg to the right.

    Returns
    -------
    Tuple[List[:class:`type`], :class:`list`]
        A list of unpacked type annotations,
        and a list of unpacked literal arguments.

    """
    type_ret = []
    literal_ret = []
    # origin = typing.get_origin(given_annotation)  # TODO: Once Python 3.10 is standard, use this.
    origin = typing_extensions.get_origin(given_annotation)
    if origin is None:
        # It doesn't have a fancy origin, just a normal type/object.
        if isinstance(given_annotation, type):
            type_ret.append(given_annotation)
        else:
            # If it's not a type and the origin is None, it's probably a literal.
            literal_ret.append(given_annotation)

    elif origin is Annotated:
        located_annotation = unpack_annotated(given_annotation, annotated_list)

        unpacked_type, unpacked_literal = unpack_annotation(located_annotation, annotated_list)
        type_ret.extend(unpacked_type)
        literal_ret.extend(unpacked_literal)
    elif origin in (Union, Optional, Literal):
        # for anno in typing.get_args(given_annotation):  # TODO: Once Python 3.10 is standard, use this.
        for anno in typing_extensions.get_args(given_annotation):
            unpacked_type, unpacked_literal = unpack_annotation(anno, annotated_list)
            type_ret.extend(unpacked_type)
            literal_ret.extend(unpacked_literal)

    else:
        raise ValueError(f"Given Annotation {given_annotation} has an unhandled origin: {origin}")

    return type_ret, literal_ret
