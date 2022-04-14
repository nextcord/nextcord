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
import warnings
from inspect import signature, Parameter
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Type,
    TYPE_CHECKING,
    Tuple,
    Union,
    TypeVar,
)
import typing

from .abc import GuildChannel
from .enums import ApplicationCommandType, ApplicationCommandOptionType, ChannelType
from .errors import (
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
    _CustomTypingMetaBase = Any
else:
    _CustomTypingMetaBase = object

__all__ = (
    "CallbackWrapper",
    # "CallbackWrapperMixin",
    "ApplicationCommandOption",
    "BaseCommandOption",
    "OptionConverter",
    "ClientCog",
    "CallbackMixin",
    # "AutocompleteOptionMixin",
    # "AutocompleteCommandMixin",
    "SlashOption",
    "SlashCommandOption",
    # "SlashCommandMixin",
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

T = TypeVar("T")
FuncT = TypeVar("FuncT", bound=Callable[..., Any])


def _cog_special_method(func: FuncT) -> FuncT:
    func.__cog_special_method__ = None
    return func


DEFAULT_SLASH_DESCRIPTION = "No description provided."


class CallbackWrapper:
    def __new__(
            cls,
            callback: Union[Callable, CallbackWrapper, BaseApplicationCommand, SlashApplicationSubcommand],
            *args,
            **kwargs,
    ):
        wrapper = super(CallbackWrapper, cls).__new__(cls)
        wrapper.__init__(callback, *args, **kwargs)
        if isinstance(callback, (BaseApplicationCommand, SlashApplicationSubcommand)):
            callback.modify_callbacks += wrapper.modify_callbacks
            return callback
        else:
            return wrapper

    def __init__(self, callback: Union[Callable, CallbackWrapper]):
        """A class used to wrap a callback in a sane way to modify aspects of application commands. The
        ``modify`` method must be overridden.

        This handles both multiple layers of wrappers, or if it wraps around a :class:`BaseApplicationCommand`

        Parameters
        ----------
        callback: Union[Callable, :class:`CallbackWrapper`]
        """
        # noinspection PyTypeChecker
        self.callback: Callable = None
        self.modify_callbacks: List[Callable] = [self.modify]
        if isinstance(callback, CallbackWrapper):
            self.callback = callback.callback
            self.modify_callbacks += callback.modify_callbacks
        else:
            self.callback = callback

    def modify(self, app_cmd: BaseApplicationCommand):
        raise NotImplementedError


class CallbackWrapperMixin:
    def __init__(self, callback: Union[Callable, CallbackWrapper]):
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


class ApplicationCommandOption:
    def __init__(
            self,
            cmd_type: ApplicationCommandOptionType = None,
            name: str = None,
            description: str = None,
            required: bool = None,
            choices: Union[Dict[str, Union[str, int, float]], Iterable[Union[str, int, float]]] = None,
            channel_types: List[ChannelType] = None,
            min_value: Union[int, float] = None,
            max_value: Union[int, float] = None,
            autocomplete: bool = None,
    ):
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
        choices: Union[Dict[:class:`str`, Union[:class:`str`, :class:`int`, :class:`float`]],
                 Iterable[Union[:class:`str`, :class:`int`, :class:`float`]]]
            Either a dictionary of display name: value pairs, or an iterable list of values that will have identical
            display names and values.
        channel_types: List[:class:`ChannelType`]
            A list of ChannelType enums to allow the user to pick. Should only be set if this is a Channel option.
        min_value: Union[:class:`int`, :class:`float`]
            Minimum value the user can input. Should only be set if this is an integer or number option.
        max_value: Union[:class:`int`, :class:`float`]
            Minimum value the user can input. Should only be set if this is an integer or number option.
        autocomplete: :class:`bool`
            If the command option should have autocomplete enabled.
        """
        self.type: Optional[ApplicationCommandOptionType] = cmd_type
        self.name: Optional[str] = name
        self.description: Optional[str] = description
        self.required: Optional[bool] = required
        self.choices: Optional[Union[Dict[str, Union[str, int, float]], Iterable[Union[str, int, float]]]] = choices
        self.channel_types: Optional[List[ChannelType]] = channel_types
        self.min_value: Optional[Union[int, float]] = min_value
        self.max_value: Optional[Union[int, float]] = max_value
        self.autocomplete: Optional[bool] = autocomplete

    @property
    def payload(self) -> dict:
        """:class:`dict`: Returns a dict payload made of the attributes of the option to be sent to Discord."""
        # noinspection PyUnresolvedReferences
        ret = {"type": self.type.value, "name": self.name, "description": self.description}
        if self.required:  # We don't check if it's None because if it's False, we don't want to send it.
            ret["required"] = self.required
        if self.choices:
            # Discord returns the names as strings, might as well do it here so payload comparison is easy.
            if isinstance(self.choices, dict):
                ret["choices"] = [{"name": str(key), "value": value} for key, value in self.choices.items()]
            else:
                ret["choices"] = [{"name": str(value), "value": value} for value in self.choices]
        if self.channel_types:
            # noinspection PyUnresolvedReferences
            ret["channel_types"] = [channel_type.value for channel_type in self.channel_types]
        if self.min_value is not None:
            ret["min_value"] = self.min_value
        if self.max_value is not None:
            ret["max_value"] = self.max_value
        if self.autocomplete:
            ret["autocomplete"] = self.autocomplete
        return ret


class BaseCommandOption(ApplicationCommandOption):
    def __init__(
            self,
            parameter: Parameter,
            command: BaseApplicationCommand,
            parent_cog: Optional[ClientCog] = None
    ):
        """Represents an application command option, but takes a Parameter and ClientCog as an argument.

        Parameters
        ----------
        parameter: :class:`Parameter`
            Function parameter to construct the command option with.
        command: :class:`BaseApplicationCommand`
            Application Command this option is for.
        parent_cog: :class:`ClientCog`
            Class that the function the option is for resides in.
        """
        super().__init__()
        self.parameter: Parameter = parameter
        self.command: BaseApplicationCommand = command
        self.functional_name: str = parameter.name
        """Name of the kwarg in the function/method"""
        self.parent_cog: Optional[ClientCog] = parent_cog


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
        self.type: Union[type, ApplicationCommandOptionType] = option_type

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
            for elem, value in base.__dict__.items():
                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__
                # if isinstance(value, ApplicationCommand):
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
        return self.__cog_application_commands__

    def process_app_cmds(self) -> None:
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

    @property
    def to_register(self) -> List[BaseApplicationCommand]:
        warnings.warn(".to_register is deprecated, please use .application_commands instead.", stacklevel=2,
                      category=FutureWarning)
        # TODO: Remove at later date.
        return self.__cog_application_commands__


class CallbackMixin:
    name: str
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
        self.callback: Callable = callback
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
        if self.parent_cog:
            return self.callback(self.parent_cog, interaction, *args, **kwargs)
        else:
            return self.callback(interaction, *args, **kwargs)

    @property
    def error_name(self) -> str:
        """Returns a string containing the class name, command name, and the callback to use in raising exceptions.

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

    def from_callback(
            self,
            callback: Optional[Callable] = None,
            option_class: Optional[Type[BaseCommandOption]] = BaseCommandOption
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
        if self.name is None:
            self.name = self.callback.__name__
        try:
            if not asyncio.iscoroutinefunction(self.callback):
                raise TypeError("Callback must be a coroutine")
            # While this arguably is Slash Commands only, we could do some neat stuff in the future with it in other
            #  commands. While Discord doesn't support anything else having Options, we might be able to do something here.
            if option_class:
                first_arg = True
                typehints = typing.get_type_hints(self.callback)
                # self_skip = inspect.ismethod(self.callback)  # Getting the callback as a method was problematic. Look
                #  into this in the future, it's better than just checking if self.parent_cog exists.
                self_skip = True if self.parent_cog else False
                for name, param in signature(self.callback).parameters.items():
                    # self_skip = name == "self"  # If self.parent_cog isn't reliable enough for some reason, use this.

                    if first_arg:
                        if not self_skip:
                            first_arg = False
                        else:
                            self_skip = False
                    else:
                        if isinstance(param.annotation, str):
                            # Thank you Disnake for the guidance to use this.
                            param = param.replace(annotation=typehints.get(name, param.empty))
                        arg = option_class(param, self, parent_cog=self.parent_cog)
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
                check_result = await maybe_coroutine(check, interaction)
            # To catch any subclasses of ApplicationCheckFailure.
            except ApplicationCheckFailure:
                raise
            # If the check returns False, the command can't be run.
            else:
                if not check_result:
                    error = ApplicationCheckFailure(
                        f"The global check functions for application command {self.error_name} failed."
                    )
                    raise error

        # Cog check
        if self.parent_cog:
            cog_check = ClientCog._get_overridden_method(
                self.parent_cog.cog_application_command_check
            )
            if cog_check is not None and not await maybe_coroutine(
                    cog_check, interaction
            ):
                raise ApplicationCheckFailure(
                    f"The cog check functions for application command {self.error_name} failed."
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
                        f"The check functions for application command {self.error_name} failed."
                    )
                    raise error

        return True

    async def invoke_callback_with_hooks(
            self, state: ConnectionState, interaction: Interaction, *args, **kwargs
    ) -> None:
        """|coro|
        Invokes the callback with all hooks and checks.
        """
        interaction._set_application_command(self)
        try:
            can_run = await self.can_run(interaction)
        except Exception as error:
            state.dispatch("application_command_error", interaction, error)
            await self.invoke_error(interaction, error)
            return

        if can_run:

            if self._callback_before_invoke is not None:
                await self._callback_before_invoke(interaction)

            if (before_invoke := self.cog_before_invoke) is not None:
                await before_invoke(interaction)
            if (before_invoke := state._application_command_before_invoke) is not None:
                await before_invoke(interaction)

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
            finally:
                if self._callback_after_invoke is not None:
                    await self._callback_after_invoke(interaction)

                if (after_invoke := self.cog_after_invoke) is not None:
                    await after_invoke(interaction)

                if (after_invoke := state._application_command_after_invoke) is not None:
                    await after_invoke(interaction)

    async def invoke_callback(self, interaction: Interaction, *args, **kwargs) -> None:
        """|coro|
        Invokes the callback, injecting ``self`` if available.
        """
        await self(interaction, *args, **kwargs)

    async def invoke_error(self, interaction: Interaction, error: ApplicationError) -> None:
        """|coro|
        Invokes the error handler if available.
        """
        if self.has_error_handler():
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

    def callback_before_invoke(self, coro: Callable[[Interaction], Coroutine]) -> Callable[[Interaction], Coroutine]:
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

    def callback_after_invoke(self, coro: Callable[[Interaction], Coroutine]) -> Callable[[Interaction], Coroutine]:
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
    def __init__(self, autocomplete_callback: Callable = None, parent_cog: ClientCog = None):
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

    def from_autocomplete_callback(self, callback: Callable) -> SlashCommandOption:
        """Parses a callback meant to be the autocomplete function."""
        self.autocomplete_callback = callback
        if not asyncio.iscoroutinefunction(self.autocomplete_callback):
            raise TypeError("Callback must be a coroutine")
        skip_count = 2  # We skip the first and second args, they are always the Interaction and
        #  the primary autocomplete value.
        if self.parent_cog:
            # If there's a parent cog, there should be a self. Skip it too.
            skip_count += 1
        for name, param in signature(self.autocomplete_callback).parameters.items():
            if skip_count:
                skip_count -= 1
            else:
                self.autocomplete_options.add(name)
        return self

    async def invoke_autocomplete_callback(
            self,
            interaction: Interaction,
            option_value: Any,
            **kwargs
    ) -> None:
        """|coro|
        Invokes the autocomplete callback, injecting ``self`` if available.
        """
        if self.parent_cog:
            return await self.autocomplete_callback(self.parent_cog, interaction, option_value, **kwargs)
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
        self._temp_autocomplete_callbacks: Dict[str, Callable] = {}
        """
        Why does this exist, and why is it "temp", you may ask? :class:`SlashCommandOption`'s are only available after 
        the callback is fully parsed when the :class:`Client` or :class:`ClientCog` runs the from_callback method, thus 
        we have to hold the decorated autocomplete callbacks temporarily until then.
        """

    async def call_autocomplete_from_interaction(self, interaction: Interaction) -> None:
        """|coro|
        Calls the autocomplete callback with the given interaction.
        """
        await self.call_autocomplete(self._state, interaction)

    async def call_autocomplete(
            self,
            state: ConnectionState,
            interaction: Interaction,
            option_data: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """|coro|
        Calls the autocomplete callback with the given interaction and option data.
        """
        if not option_data:
            option_data = interaction.data.get("options", {})
        if self.children:
            await self.children[option_data[0]["name"]].call_autocomplete(
                state, interaction, option_data[0].get("options", {})
            )
        else:
            focused_option_name = None
            for arg in option_data:
                if arg.get("focused", None) is True:
                    if focused_option_name:
                        raise ValueError("Multiple options are focused, is that supposed to be possible?")
                    focused_option_name = arg["name"]

            if not focused_option_name:
                raise ValueError("There's supposed to be a focused option, but it's not found?")
            focused_option = self.options[focused_option_name]
            if focused_option.autocomplete_callback is None:
                raise ValueError(f"{self.error_name} Autocomplete called for option {focused_option.functional_name} "
                                 f"but it doesn't have an autocomplete function?")

            kwargs = {}
            uncalled_options = focused_option.autocomplete_options.copy()
            uncalled_options.discard(focused_option.name)
            focused_option_value = None
            for arg_data in option_data:
                if (option := self.options.get(arg_data["name"], None)) and option.functional_name in uncalled_options:
                    uncalled_options.discard(option.functional_name)
                    kwargs[option.functional_name] = await option.handle_value(state, arg_data["value"], interaction)
                elif arg_data["name"] == focused_option.name:
                    focused_option_value = await focused_option.handle_value(state, arg_data["value"], interaction)
            for option_name in uncalled_options:
                kwargs[option_name] = None
            value = await focused_option.invoke_autocomplete_callback(interaction, focused_option_value, **kwargs)
            if value and not interaction.response.is_done():
                await interaction.response.send_autocomplete(value)

    def from_autocomplete(self) -> None:
        """

        Returns
        -------

        """
        for arg_name, callback in self._temp_autocomplete_callbacks.items():
            found = False
            for name, option in self.options.items():
                if option.functional_name == arg_name:
                    if option.autocomplete is None:
                        # If autocomplete isn't set, enable it for them.
                        option.autocomplete = True
                    if option.autocomplete:
                        # option.autocomplete_callback = callback
                        option.from_autocomplete_callback(callback)
                        found = True
            if found:
                continue
            # If it hasn't returned yet, it didn't find a valid kwarg. Raise it.
            raise ValueError(f"{self.error_name} kwarg \"{arg_name}\" for autocomplete not found.")

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
            name: str = None,
            description: str = None,
            required: bool = None,
            choices: Union[
                Dict[str, Union[str, int, float]], Iterable[Union[str, int, float]]
            ] = None,
            channel_types: List[ChannelType] = None,
            min_value: Union[int, float] = None,
            max_value: Union[int, float] = None,
            autocomplete: bool = None,
            autocomplete_callback: Callable = None,
            default: Any = MISSING,
            verify: bool = True,
    ):
        super().__init__(name=name, description=description, required=required, choices=choices,
                         channel_types=channel_types, min_value=min_value, max_value=max_value,
                         autocomplete=autocomplete)
        self.autocomplete_callback: Callable = autocomplete_callback
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
    option_types = {
        str: ApplicationCommandOptionType.string,
        int: ApplicationCommandOptionType.integer,
        bool: ApplicationCommandOptionType.boolean,
        User: ApplicationCommandOptionType.user,
        Member: ApplicationCommandOptionType.user,
        GuildChannel: ApplicationCommandOptionType.channel,
        Role: ApplicationCommandOptionType.role,
        Mentionable: ApplicationCommandOptionType.mentionable,
        float: ApplicationCommandOptionType.number,
        Attachment: ApplicationCommandOptionType.attachment,
    }
    """Maps Python annotations/typehints to Discord Application Command type values."""
    def __init__(
            self,
            parameter: Parameter,
            commmand: Union[SlashApplicationCommand, SlashApplicationSubcommand],
            parent_cog: Optional[ClientCog] = None
    ):
        BaseCommandOption.__init__(self, parameter, commmand, parent_cog)
        SlashOption.__init__(self)  # We subclassed SlashOption because we must handle all attributes it has.
        AutocompleteOptionMixin.__init__(self, parent_cog=parent_cog)
        # self.functional_name = parameter.name

        if isinstance(parameter.default, SlashOption):
            # Remember: Values that the user provided in SlashOption should override any logic.
            #  Verify can raise errors on incompatible values.
            cmd_arg = parameter.default
            cmd_arg_given = True
        else:
            cmd_arg = SlashOption()
            cmd_arg_given = False

        self.name = cmd_arg.name or parameter.name
        self._description = cmd_arg.description
        if cmd_arg.required is not None:  # If the user manually set it...
            self.required = cmd_arg.required
        elif type(None) in typing.get_args(parameter.annotation):  # If it's typed as Optional/None...
            self.required = False
        elif cmd_arg.default is not MISSING:  # If the SlashOption has a default...
            self.required = False
        elif parameter.default is not parameter.empty and not cmd_arg_given:
            # If a default was given AND it's not SlashOption...
            self.required = False
        else:  # Parameters in Python, by default, are required. While Discord defaults to not-required, this is Python.
            self.required = True
        self.choices = cmd_arg.choices
        self.min_value = cmd_arg.min_value
        self.max_value = cmd_arg.max_value
        self.autocomplete = cmd_arg.autocomplete
        self.autocomplete_callback = cmd_arg.autocomplete_callback
        if self.autocomplete_callback and self.autocomplete is None:
            self.autocomplete = True

        if self.autocomplete_callback:
            if not asyncio.iscoroutinefunction(self.autocomplete_callback):
                raise TypeError(f"Given autocomplete callback for kwarg {self.functional_name} isn't a coroutine.")

        if cmd_arg_given is False and parameter.default is not parameter.empty:
            # If we weren't given a SlashOption, but we were given something else, set the default to that.
            self.default = parameter.default
        else:
            # Else, just set the default to whatever cmd_arg is set to. Either None, or something set by the user.
            self.default = cmd_arg.default
        if self.default is MISSING:
            self.default = None

        self.converter: Optional[OptionConverter] = None

        if isinstance(parameter.annotation, OptionConverter):  # If annotated with an instantiated OptionConverter...
            self.converter = parameter.annotation
        elif inspect.isclass(parameter.annotation) and issubclass(parameter.annotation, OptionConverter):
            # If annotated with OptionConverter...
            self.converter = parameter.annotation()
        else:
            for t in typing.get_args(parameter.annotation):
                if issubclass(t, OptionConverter):
                    # If annotated with OptionConverter inside of Optional...
                    self.converter = t()  # Optional cannot have instantiated objects in it apparently?
                    break

        if self.converter:
            self.type: ApplicationCommandOptionType = self.get_type(self.converter)

        else:
            self.type: ApplicationCommandOptionType = self.get_type(parameter.annotation)


        if self.converter:
            self.converter.modify(self)
        # noinspection PyProtectedMember
        if cmd_arg._verify:
            self.verify()

    @property
    def description(self) -> str:
        """:class:`str`: If no description is set, it returns "No description provided" """
        # noinspection PyProtectedMember
        if self._description is not None:
            return self._description
        elif docstring := self.command._parsed_docstring["args"].get(self.functional_name):
            return docstring
        else:
            return DEFAULT_SLASH_DESCRIPTION

    @description.setter
    def description(self, value: str):
        self._description = value

    def get_type(self, param_typing: Union[type, OptionConverter]) -> ApplicationCommandOptionType:
        if isinstance(param_typing, OptionConverter):
            if isinstance(param_typing.type, type):
                param_typing = param_typing.type
            else:
                return param_typing.type
        # noinspection PyTypeChecker,PyUnboundLocalVariable
        if param_typing is self.parameter.empty:
            return ApplicationCommandOptionType.string
        elif valid_type := self.option_types.get(param_typing, None):
            return valid_type
        elif (
            type(None) in typing.get_args(param_typing)
            and (inner_type := find(lambda t: t is not type(None), typing.get_args(param_typing)))
            and (valid_type := self.option_types.get(inner_type, None))
        ):
            return valid_type
        else:
            raise NotImplementedError(f'{self.command.error_name} Type "{param_typing}" isn\'t a supported typing for Application Commands.')

    def verify(self) -> None:
        """This should run through :class:`SlashOption` variables and raise errors when conflicting data is given."""
        super().verify()
        if self.channel_types and self.type is not ApplicationCommandOptionType.channel:
            raise ValueError("channel_types can only be given when the var is typed as nextcord.abc.GuildChannel")
        if self.min_value is not None and type(self.min_value) not in (int, float):
            raise ValueError("min_value must be an int or float.")
        if self.max_value is not None and type(self.max_value) not in (int, float):
            raise ValueError("max_value must be an int or float.")
        if (self.min_value is not None or self.max_value is not None) and self.type not in (
                ApplicationCommandOptionType.integer, ApplicationCommandOptionType.number):
            raise ValueError("min_value or max_value can only be set if the type is integer or number.")

    async def handle_value(self, state: ConnectionState, value: Any, interaction: Interaction) -> Any:
        if self.type is ApplicationCommandOptionType.channel:
            value = state.get_channel(int(value))
        elif self.type is ApplicationCommandOptionType.user:
            user_id = int(value)
            user_dict = {user.id: user for user in get_users_from_interaction(state, interaction)}
            value = user_dict[user_id]
        elif self.type is ApplicationCommandOptionType.role:
            value = interaction.guild.get_role(int(value))
        elif self.type is ApplicationCommandOptionType.integer:
            value = int(value) if value != '' else None
        elif self.type is ApplicationCommandOptionType.number:
            value = float(value)
        elif self.type is ApplicationCommandOptionType.attachment:
            resolved_attachment_data: dict = interaction.data["resolved"]["attachments"][value]
            value = Attachment(data=resolved_attachment_data, state=state)
        elif self.type is ApplicationCommandOptionType.mentionable:
            user_role_list = get_users_from_interaction(state, interaction) + \
                             get_roles_from_interaction(state, interaction)
            mentionables = {mentionable.id: mentionable for mentionable in user_role_list}
            value = mentionables[int(value)]

        if self.converter:
            return await self.converter.convert(interaction, value)
        # if value is MISSING:
        #     return None
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
        elif docstring := self._parsed_docstring["description"]:
            return docstring
        else:
            return DEFAULT_SLASH_DESCRIPTION

    def from_callback(
            self,
            callback: Optional[Callable] = None,
            option_class: Optional[Type[SlashCommandOption]] = SlashCommandOption
    ):
        CallbackMixin.from_callback(self, callback=callback, option_class=option_class)
        # Right now, only slash commands can have descriptions. If User/Message commands gain descriptions, move
        #  this to CallbackMixin.
        self._parsed_docstring = parse_docstring(callback, _MAX_COMMAND_DESCRIPTION_LENGTH)

    async def call_slash(
            self, state: ConnectionState, interaction: Interaction, option_data: List[Dict[str, Any]] = None
    ):
        if option_data is None:
            option_data = interaction.data.get("options", {})
        if self.children:
            await self.children[option_data[0]["name"]].call_slash(
                state, interaction, option_data[0].get("options", {})
            )
        else:
            kwargs = {}
            uncalled_args = self.options.copy()
            for arg_data in option_data:
                if arg_data["name"] in uncalled_args:
                    uncalled_args.pop(arg_data["name"])
                    kwargs[self.options[arg_data["name"]].functional_name] = \
                        await self.options[arg_data["name"]].handle_value(state, arg_data["value"],
                                                                          interaction)
                else:
                    # TODO: Handle this better.
                    raise NotImplementedError(
                        f"An argument was provided that wasn't already in the function, did you"
                        f"recently change it?\nRegistered Options: {self.options}, Discord-sent"
                        f"args: {interaction.data['options']}, broke on {arg_data}"
                    )
            for uncalled_arg in uncalled_args.values():
                kwargs[uncalled_arg.functional_name] = uncalled_arg.default
            # await self.invoke_callback(interaction, **kwargs)
            await self.invoke_callback_with_hooks(state, interaction, **kwargs)


class BaseApplicationCommand(CallbackMixin, CallbackWrapperMixin):
    def __init__(
            self,
            name: str = None,
            description: str = None,
            callback: Callable = None,
            cmd_type: ApplicationCommandType = None,
            guild_ids: Iterable[int] = None,
            default_permission: Optional[bool] = None,
            parent_cog: Optional[ClientCog] = None,
            force_global: bool = False
    ):
        """Base application command class that all specific application command classes should subclass. All common
        behavior should be here, with subclasses either adding on or overriding specific aspects of this class.

        Parameters
        ----------
        name: :class:`str`
            Name of the command.
        description: :class:`str`
            Description of the command.
        callback: Callable
            Callback to make the application command from, and to run when the application command is called.
        cmd_type: :class:`ApplicationCommandType`
            Type of application command. This should be set by subclasses.
        guild_ids: Iterable[:class:`int`]
            An iterable list/set/whatever of guild ID's that the application command should register to.
        default_permission: Optional[:class:`bool`]
            # TODO: See Discord documentation.
            See Discord documentation.
        parent_cog: Optional[:class:`ClientCog`]
            ``ClientCog`` to forward to the callback as the ``self`` argument.
        force_global: :class:`bool`
            If this command should be registered as a global command, ALONG WITH all guild IDs set.
        """
        CallbackWrapperMixin.__init__(self, callback)
        CallbackMixin.__init__(self, callback=callback, parent_cog=parent_cog)
        self._state: Optional[ConnectionState] = None
        self.type: Optional[ApplicationCommandType] = cmd_type
        self.name: Optional[str] = name
        self._description: Optional[str] = description
        self.guild_ids_to_rollout: Set[int] = set(guild_ids) if guild_ids else set()
        self.default_permission: Optional[bool] = default_permission
        self.force_global: bool = force_global

        self.command_ids: Dict[Optional[int], int] = {}  # {Guild ID (None for global): command ID}
        self.options: Dict[str, SlashOption] = {}

    # Simple-ish getter + setter methods.

    @property
    def description(self) -> str:
        """The description the command should have in Discord. Should be 1-100 characters long."""
        return self._description

    @description.setter
    def description(self, new_description: str):
        self._description = new_description

    @property
    def is_guild(self) -> bool:
        """:class:`bool`: Returns ``True`` if this command is or should be registered to any guilds."""
        guild_only_ids = set(self.command_ids.keys())
        guild_only_ids.discard(None)
        return True if (self.guild_ids_to_rollout or guild_only_ids) else None

    @property
    def guild_ids(self) -> Set[int]:
        """Returns a :class:`set` containing all guild ID's this command is registered to."""
        # TODO Is this worthwhile?
        guild_only_ids = set(self.command_ids.keys())
        guild_only_ids.discard(None)
        return guild_only_ids

    def add_guild_rollout(self, guild: Union[int, Guild]) -> None:
        """Adds a Guild to the command to be rolled out to when the rollout is run.

        Parameters
        ----------
        guild: Union[:class:`int`, :class:`Guild`]
            Guild or Guild ID to add this command to roll out to.
        """
        # TODO: Is this worth doing? People can just do guild_ids_to_rollout.add(guild.id)
        if isinstance(guild, Guild):
            # I don't like doing `guild = guild.id` and this keeps it extendable.
            guild_id = guild.id
        else:
            guild_id = guild
        self.guild_ids_to_rollout.add(guild_id)

    @property
    def is_global(self) -> bool:
        """:class:`bool`: Returns ``True`` if this command is or should be a global command."""
        return True if (self.force_global or not self.is_guild or None in self.command_ids) else False

    def get_signature(self, guild_id: Optional[int] = None) -> Tuple[str, int, Optional[int]]:
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
            "name": str(self.name),  # Might as well stringify the name, will come in handy if people try using numbers.
            "description": self.description,
        }
        if self.default_permission is not None:
            ret["default_permission"] = self.default_permission
        else:
            ret["default_permission"] = True
        if guild_id:
            ret["guild_id"] = guild_id
        return ret

    def parse_discord_response(self, state: ConnectionState, data: dict) -> None:
        """Parses the application command creation/update response from Discord.

        Parameters
        ----------
        state: :class:`ConnectionState`
            Connection state to use internally in the command.
        data: :class:`dict`
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

    def is_payload_valid(self, raw_payload: dict, guild_id: Optional[int] = None) -> bool:
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
            return False
        if not check_dictionary_values(cmd_payload, raw_payload, "default_permission", "description", "type", "name"):
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
            cmd_options = cmd_pos.get("options")
            our_options = {opt["name"]: opt for opt in cmd_options}
            if len(inter_options) == 1 and (  # If the length is only 1, it might be a subcommand (group).
                inter_options[0]["type"] in (
                    ApplicationCommandOptionType.sub_command.value,
                    ApplicationCommandOptionType.sub_command_group.value
                    )) and (  # This checks if it's a subcommand (group).
                found_opt := our_options.get(inter_options[0]["name"])  # This checks if the name matches an option.
            ) and inter_options[0]["type"] == found_opt["type"]:  # And this makes sure both are the same type.
                return _recursive_subcommand_check(inter_options[0], found_opt)  # If all of the above pass, recurse.
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
                        if inter_opt["name"] == our_opt["name"] and inter_opt["type"] == our_opt["type"]:
                            all_our_options_copy.pop(our_opt_name)
                            all_inter_options_copy.pop(our_opt_name)
                        else:
                            _log.debug("%s Required option don't match name and/or type.", self.error_name)
                            return False  # Options don't match name and/or type.

                    else:
                        _log.debug("%s Inter missing required option.", self.error_name)
                        return False  # Required option wasn't found.
                # Begin checking optional arguments.
                for inter_opt_name, inter_opt in all_inter_options_copy:  # Should only contain optionals now.
                    if our_opt := all_our_options_copy.get(inter_opt_name):
                        if inter_opt["name"] == our_opt["name"] and inter_opt["type"] == our_opt["type"]:
                            pass
                        else:
                            _log.debug("%s Optional option don't match name and/or type.", self.error_name)
                            return False  # Options don't match name and/or type.
                    else:
                        _log.debug("%s Inter has option that we don't.", self.error_name)
                        return False  # They have an option name that we don't.
            else:
                _log.debug(
                    "%s We have less options than them: %s vs %s",
                    self.error_name, all_our_options, all_inter_options
                )
                return False  # Interaction has more options than we do.
            return True  # No checks failed.

        if not check_dictionary_values(our_payload, data, "name", "guild_id", "type"):
            _log.debug("%s Failed basic dictionary check.", self.error_name)
            return False
        else:
            data_options = data.get("options")
            payload_options = our_payload.get("options")
            if data_options and payload_options:
                return _recursive_subcommand_check(data, our_payload)
            elif data_options is None and payload_options is None:
                return True  # User and Message commands don't have options.
            else:
                _log.debug(
                    "%s Mismatch between data and payload options: %s vs %s",
                    self.error_name, data_options, payload_options
                )
                # There is a mismatch between the two, fail it.
                return False

    def from_callback(
            self,
            callback: Optional[Callable] = None,
            option_class: Optional[Type[BaseCommandOption]] = BaseCommandOption
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
        await self.call(self._state, interaction)

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

    def check_against_raw_payload(self, raw_payload: dict, guild_id: Optional[int] = None) -> bool:
        warnings.warn(
            ".check_against_raw_payload() is deprecated, please use .is_payload_valid instead.",
            stacklevel=2,
            category=FutureWarning
        )
        return self.is_payload_valid(raw_payload, guild_id)

    def get_guild_payload(self, guild_id: int):
        warnings.warn(".get_guild_payload is deprecated, use .get_payload(guild_id) instead.", stacklevel=2, category=FutureWarning)
        return self.get_payload(guild_id)

    @property
    def global_payload(self) -> dict:
        warnings.warn(".global_payload is deprecated, use .get_payload(None) instead.", stacklevel=2,
                      category=FutureWarning)
        return self.get_payload(None)


class SlashApplicationSubcommand(SlashCommandMixin, AutocompleteCommandMixin, CallbackWrapperMixin):
    def __init__(
            self,
            name: str = None,
            description: str = None,
            callback: Callable = None,
            parent_cmd: Union[SlashApplicationCommand, SlashApplicationSubcommand] = None,
            cmd_type: ApplicationCommandOptionType = None,
            parent_cog: Optional[ClientCog] = None,
    ):
        """Slash Application Subcommand, supporting additional subcommands and autocomplete.

        Parameters
        ----------
        name: :class:`str`
            Name of the subcommand (group). No capital letters or spaces. Defaults to the name of the callback.
        description: :class:`str`
            Description of the subcommand (group). Must be between 1-100 characters. If not provided, a default value
            will be given.
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
        """
        SlashCommandMixin.__init__(self, callback=callback, parent_cog=parent_cog)
        AutocompleteCommandMixin.__init__(self, parent_cog)
        CallbackWrapperMixin.__init__(self, callback)

        self.name: str = name
        self._description: str = description
        self.type: ApplicationCommandOptionType = cmd_type
        self.parent_cmd: Union[SlashApplicationCommand, SlashApplicationSubcommand] = parent_cmd

        self.options: Dict[str, SlashCommandOption] = {}
        self.children: Dict[str, SlashApplicationSubcommand] = {}

    async def call(self, state: ConnectionState, interaction: Interaction, option_data: List[dict]) -> None:
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
            await self.children[option_data[0]["name"]].call(state, interaction, option_data[0].get("options", {}))
        else:
            await self.call_slash(state, interaction, option_data)

    @property
    def payload(self) -> dict:
        """Returns a dict payload made of the attributes of the subcommand (group) to be sent to Discord."""
        # noinspection PyUnresolvedReferences
        ret = {
            "type": self.type.value,
            "name": str(self.name),  # Might as well stringify the name, will come in handy if people try using numbers.
            "description": self.description,
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
            call_children: bool = True
    ) -> None:
        SlashCommandMixin.from_callback(self, callback=callback, option_class=option_class)
        if call_children:
            if self.children:
                for child in self.children.values():
                    child.from_callback(callback=child.callback, option_class=option_class, call_children=call_children)
        for modify_callback in self.modify_callbacks:
            modify_callback(self)
        super().from_autocomplete()

    def subcommand(
            self,
            name: str = None,
            description: str = None
    ) -> Callable[[Callable], SlashApplicationSubcommand]:
        """Takes a decorated callback and turns it into a :class:`SlashApplicationSubcommand` added as a subcommand.

        Parameters
        ----------
        name: :class:`str`
            Name of the slash subcommand. No capital letters, no spaces.
        description: :class:`str`
            Description of the slash subcommand. Must be 1-100 characters. If not provided, a default will be given.
        """
        def decorator(func: Callable) -> SlashApplicationSubcommand:
            ret = SlashApplicationSubcommand(
                name=name, description=description, callback=func, parent_cmd=self,
                cmd_type=ApplicationCommandOptionType.sub_command, parent_cog=self.parent_cog
            )
            self.children[ret.name] = ret
            return ret
        if isinstance(self.parent_cmd, SlashApplicationSubcommand):  # Discord limitation, no groups in groups.
            raise TypeError(f"{self.error_name} Subcommand groups cannot be nested inside subcommand groups.")
        self.type = ApplicationCommandOptionType.sub_command_group
        return decorator


class SlashApplicationCommand(SlashCommandMixin, BaseApplicationCommand, AutocompleteCommandMixin):
    def __init__(
            self,
            name: str = None,
            description: str = None,
            callback: Callable = None,
            guild_ids: Iterable[int] = None,
            default_permission: bool = None,
            parent_cog: Optional[ClientCog] = None,
            force_global: bool = False
    ):
        """Represents a Slash Application Command built from the given callback, able to be registered to multiple
        guilds or globally.

        Parameters
        ----------
        name: :class:`str`
            Name of the command. Must be lowercase with no spaces.
        description: :class:`str`
            Description of the command. Must be between 1 to 100 characters, or defaults
        callback: Callable
            Callback to make the application command from, and to run when the application command is called.
        guild_ids: Iterable[:class:`int`]
            An iterable list of guild ID's that the application command should register to.
        default_permission: Optional[:class:`bool`]
            # TODO: See Discord documentation.
            See Discord documentation.
        parent_cog: Optional[:class:`ClientCog`]
            ``ClientCog`` to forward to the callback as the ``self`` argument.
        force_global: :class:`bool`
            If this command should be registered as a global command, ALONG WITH all guild IDs set.
        """
        BaseApplicationCommand.__init__(self, name=name, description=description, callback=callback,
                                        cmd_type=ApplicationCommandType.chat_input, guild_ids=guild_ids,
                                        default_permission=default_permission, parent_cog=parent_cog,
                                        force_global=force_global)
        AutocompleteCommandMixin.__init__(self, parent_cog=parent_cog)
        SlashCommandMixin.__init__(self, callback=callback, parent_cog=parent_cog)

    @property
    def description(self) -> str:
        return super().description  # Required to grab the correct description function.

    def get_payload(self, guild_id: Optional[int]):
        ret = super().get_payload(guild_id)
        if self.children:
            ret["options"] = [child.payload for child in self.children.values()]
        else:
            ret["options"] = [parameter.payload for parameter in self.options.values()]
        return ret

    async def call(self, state: ConnectionState, interaction: Interaction) -> None:
        option_data = interaction.data.get("options", {})
        if self.children:
            await self.children[option_data[0]["name"]].call(state, interaction, option_data[0].get("options", {}))
        else:
            await self.call_slash(state, interaction, option_data)

    def from_callback(
            self,
            callback: Optional[Callable] = None,
            option_class: Type[SlashCommandOption] = SlashCommandOption,
            call_children: bool = True
    ):
        BaseApplicationCommand.from_callback(self, callback=callback, option_class=option_class)
        SlashCommandMixin.from_callback(self, callback=callback)
        AutocompleteCommandMixin.from_autocomplete(self)
        if call_children and self.children:
            for child in self.children.values():
                child.from_callback(callback=child.callback, option_class=option_class, call_children=call_children)
        for modify_callback in self.modify_callbacks:
            modify_callback(self)

    def subcommand(
            self,
            name: str = None,
            description: str = None
    ) -> Callable[[Callable], SlashApplicationSubcommand]:
        """Takes a decorated callback and turns it into a :class:`SlashApplicationSubcommand` added as a subcommand.

        Parameters
        ----------
        name: :class:`str`
            Name of the slash subcommand. No capital letters, no spaces.
        description: :class:`str`
            Description of the slash subcommand. Must be 1-100 characters. If not provided, a default will be given.
        """
        def decorator(func: Callable) -> SlashApplicationSubcommand:
            ret = SlashApplicationSubcommand(
                name=name, description=description, callback=func, parent_cmd=self,
                cmd_type=ApplicationCommandOptionType.sub_command, parent_cog=self.parent_cog
            )
            self.children[ret.name] = ret
            return ret
        return decorator


class UserApplicationCommand(BaseApplicationCommand):
    def __init__(
            self,
            name: str = None,
            callback: Callable = None,
            guild_ids: Iterable[int] = None,
            default_permission: bool = None,
            parent_cog: Optional[ClientCog] = None,
            force_global: bool = False
    ):
        """Represents a User Application Command that will give the user to the given callback, able to be registered to
        multiple guilds or globally.

        Parameters
        ----------
        name: :class:`str`
            Name of the command. Can be uppercase with spaces.
        callback: Callable
            Callback to run with the application command is called.
        guild_ids: Iterable[:class:`int`]
            An iterable list of guild ID's that the application command should register to.
        default_permission: Optional[:class:`bool`]
            # TODO: See Discord documentation.
            See Discord documentation.
        parent_cog: Optional[:class:`ClientCog`]
            ``ClientCog`` to forward to the callback as the ``self`` argument.
        force_global: :class:`bool`
            If this command should be registered as a global command, ALONG WITH all guild IDs set.
        """
        super().__init__(name=name, description="", callback=callback,
                         cmd_type=ApplicationCommandType.user, guild_ids=guild_ids,
                         default_permission=default_permission, parent_cog=parent_cog, force_global=force_global)

    async def call(self, state: ConnectionState, interaction: Interaction):
        await self.invoke_callback_with_hooks(state, interaction, get_users_from_interaction(state, interaction)[0])

    def from_callback(
            self,
            callback: Optional[Callable] = None,
            option_class: Optional[Type[BaseCommandOption]] = None):
        super().from_callback(callback, option_class=option_class)


class MessageApplicationCommand(BaseApplicationCommand):
    def __init__(
            self,
            name: str = None,
            callback: Callable = None,
            guild_ids: Iterable[int] = None,
            default_permission: bool = None,
            parent_cog: Optional[ClientCog] = None,
            force_global: bool = False
    ):
        """Represents a Message Application Command that will give the message to the given callback, able to be
        registered to multiple guilds or globally.

        Parameters
        ----------
        name: :class:`str`
            Name of the command. Can be uppercase with spaces.
        callback: Callable
            Callback to run with the application command is called.
        guild_ids: Iterable[:class:`int`]
            An iterable list of guild ID's that the application command should register to.
        default_permission: Optional[:class:`bool`]
            # TODO: See Discord documentation.
            See Discord documentation.
        parent_cog: Optional[:class:`ClientCog`]
            ``ClientCog`` to forward to the callback as the ``self`` argument.
        force_global: :class:`bool`
            If this command should be registered as a global command, ALONG WITH all guild IDs set.
        """
        super().__init__(name=name, description="", callback=callback,
                         cmd_type=ApplicationCommandType.message, guild_ids=guild_ids,
                         default_permission=default_permission, parent_cog=parent_cog, force_global=force_global)

    async def call(self, state: ConnectionState, interaction: Interaction):
        await self.invoke_callback_with_hooks(state, interaction, get_messages_from_interaction(state, interaction)[0])

    def from_callback(
            self,
            callback: Optional[Callable] = None,
            option_class: Optional[Type[BaseCommandOption]] = None):
        super().from_callback(callback, option_class=option_class)


def slash_command(
    name: str = None,
    description: str = None,
    guild_ids: Iterable[int] = None,
    default_permission: Optional[bool] = None,
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
    default_permission: Optional[:class:`bool`]
        If users should be able to use this command by default or not. Defaults to Discords default, `True`.
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
            description=description,
            guild_ids=guild_ids,
            default_permission=default_permission,
            force_global=force_global,
        )
        return app_cmd

    return decorator


def message_command(
    name: str = None,
    guild_ids: Iterable[int] = None,
    default_permission: Optional[bool] = None,
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
    default_permission: Optional[:class:`bool`]
        If users should be able to use this command by default or not. Defaults to Discords default, `True`.
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
            guild_ids=guild_ids,
            default_permission=default_permission,
            force_global=force_global,
        )
        return app_cmd

    return decorator


def user_command(
    name: str = None,
    guild_ids: Iterable[int] = None,
    default_permission: Optional[bool] = None,
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
    default_permission: Optional[:class:`bool`]
        If users should be able to use this command by default or not. Defaults to Discord's default, `True`.
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


def get_users_from_interaction(state: ConnectionState, interaction: Interaction) -> List[Union[User, Member]]:
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
    ret = []
    # Return a Member object if the required data is available, otherwise fall back to User.
    if "members" in data["resolved"]:
        member_payloads = data["resolved"]["members"]
        # Because the payload is modified further down, a copy is made to avoid affecting methods or
        #  users that read from interaction.data further down the line.
        for member_id, member_payload in member_payloads.copy().items():
            # If a member isn't in the cache, construct a new one.
            if not (member := interaction.guild.get_member(int(member_id))):
                user_payload = interaction.data["resolved"]["users"][member_id]
                # This is required to construct the Member.
                member_payload["user"] = user_payload
                member = Member(data=member_payload, guild=interaction.guild, state=state)
                interaction.guild._add_member(member)
            ret.append(member)
    elif "users" in data["resolved"]:
        resolved_users_payload = interaction.data["resolved"]["users"]
        ret = [state.store_user(user_payload) for user_payload in resolved_users_payload.values()]
    else:
        pass  # Do nothing, we can't get users or members from this interaction.
    return ret


def get_messages_from_interaction(state: ConnectionState, interaction: Interaction) -> List[Message]:
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
    if "messages" in data["resolved"]:
        message_payloads = data["resolved"]["messages"]

        for msg_id, msg_payload in message_payloads.items():
            if not (message := state._get_message(msg_id)):
                message = Message(channel=interaction.channel, data=msg_payload, state=state)
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
    if "roles" in data["resolved"]:
        role_payloads = data["resolved"]["roles"]
        for role_id, role_payload in role_payloads.items():
            # if True:  # Use this for testing payload -> Role
            if not (role := interaction.guild.get_role(role_id)):
                role = Role(guild=interaction.guild, state=state, data=role_payload)
            ret.append(role)
    return ret
