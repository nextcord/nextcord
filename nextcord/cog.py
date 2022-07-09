"""
The MIT License (MIT)

Copyright (c) 2022-present tag-epic

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
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

from .enums import ApplicationCommandOptionType, ApplicationCommandType
from .utils import MISSING

if TYPE_CHECKING:
    from .application_command import BaseApplicationCommand
    from .interactions import Interaction

__all__ = (
    "CogMeta",
    "Cog",
)

FuncT = TypeVar("FuncT", bound=Callable[..., Any])


def _cog_special_method(func: FuncT) -> FuncT:
    func.__cog_special_method__ = None
    return func


class CogMeta(type):
    """A metaclass for defining a cog.

    Note that you should probably not use this directly. It is exposed
    purely for documentation purposes along with making custom metaclasses to intermix
    with other metaclasses such as the :class:`abc.ABCMeta` metaclass.

    For example, to create an abstract cog mixin class, the following would be done.

    .. code-block:: python3

        import abc

        class CogABCMeta(nextcord.CogMeta, abc.ABCMeta):
            pass

        class SomeMixin(metaclass=abc.ABCMeta):
            pass

        class SomeCogMixin(SomeMixin, nextcord.Cog, metaclass=CogABCMeta):
            pass

    .. note::

        When passing an attribute of a metaclass that is documented below, note
        that you must pass it as a keyword-only argument to the class creation
        like the following example:

        .. code-block:: python3

            class MyCog(nextcord.Cog, name='My Cog'):
                pass

    Attributes
    -----------
    name: :class:`str`
        The cog name. By default, it is the name of the class with no modification.
    description: :class:`str`
        The cog description. By default, it is the cleaned docstring of the class.

        .. versionadded:: 1.6
    """

    __cog_name__: str

    def __new__(cls: Type[CogMeta], *args: Any, **kwargs: Any) -> CogMeta:
        name, bases, attrs = args
        attrs["__cog_name__"] = kwargs.pop("name", name)

        description = kwargs.pop("description", None)
        if description is None:
            description = inspect.cleandoc(attrs.get("__doc__", ""))
        attrs["__cog_description__"] = description

        return super().__new__(cls, name, bases, attrs, **kwargs)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args)

    @classmethod
    def qualified_name(cls) -> str:
        return cls.__cog_name__


class Cog(metaclass=CogMeta):
    """The base class that all cogs must inherit from.

    A cog is a collection of commands, listeners, and optional state to
    help group commands together. More information on them can be found on
    the :ref:`cogs` page.

    When inheriting from this class, the options shown in :class:`CogMeta`
    are equally valid here.
    """

    __cog_name__: ClassVar[str]
    __cog_application_commands__: List[BaseApplicationCommand]
    __cog_listeners__: List[Tuple[str, str]]

    def __new__(cls, *args: Any, **kwargs: Any):
        new_cls = super(Cog, cls).__new__(cls)
        new_cls._read_application_commands()
        new_cls._read_listeners()
        return new_cls

    def _read_application_commands(self) -> None:
        """Iterates through the application (sub)commands contained within the Cog, runs their from_callback
        methods, then adds them to the internal list of application commands for this cog.

        After adding all of the application commands into the internal list,
        """
        self.__cog_application_commands__ = []
        for base in reversed(self.__class__.__mro__):
            for _, value in base.__dict__.items():
                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__

                # TODO: Make a better test for a BaseApplicationCommand
                if hasattr(value, "cmd_type"):
                    if value.cmd_type is ApplicationCommandType.chat_input:
                        value.parent_cog = self
                        value.from_callback(value.callback, call_children=False)
                        self.__cog_application_commands__.append(value)
                    elif (
                        value.cmd_type is ApplicationCommandOptionType.sub_command
                        or value.cmd_type is ApplicationCommandOptionType.sub_command_group
                    ):
                        # As subcommands are part of a parent command and
                        #  not usable on their own, we don't add them to the command list, but do set the self_argument and
                        #  run them from the callback.
                        value.parent_cog = self
                        value.from_callback(value.callback, call_children=False)
                    else:
                        value.parent_cog = self
                        value.from_callback(value.callback)
                        self.__cog_application_commands__.append(value)

    def _read_listeners(self) -> None:
        """Iterates through all coroutine functions contained within the Cog and adds their listener name
        and function name into the internal list of listener names.
        """
        self.__cog_listeners__ = []
        listeners = {}

        for base in reversed(self.__class__.__mro__):
            for elem, value in base.__dict__.items():
                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__

                if asyncio.iscoroutinefunction(value):
                    listeners[elem] = value

        for listener in listeners.values():
            for listener_name in listener.__cog_listener_names__:
                self.__cog_listeners__.append((listener_name, listener.__name__))

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Returns the cog's specified name, not the class name."""
        return self.__cog_name__

    @property
    def description(self) -> str:
        """:class:`str`: Returns the cog's description, typically the cleaned docstring."""
        return self.__cog_description__

    @description.setter
    def description(self, description: str) -> None:
        self.__cog_description__ = description

    @property
    def application_commands(self) -> List[BaseApplicationCommand]:
        """Provides the list of application commands in this cog. Subcommands are not included."""
        return self.__cog_application_commands__

    @property
    def listeners(self) -> List[Tuple[str, Callable[..., Any]]]:
        """Provides the list of listeners in this cog with the name and callback in a tuple."""
        return [(name, getattr(self, method_name)) for name, method_name in self.__cog_listeners__]

    def get_listeners(self) -> List[Tuple[str, Callable[..., Any]]]:
        """Returns a :class:`list` of (name, function) listener pairs that are defined in this cog.
        Returns
        --------
        List[Tuple[:class:`str`, :ref:`coroutine <coroutine>`]]
            The listeners defined in this cog.
        """
        return [(name, getattr(self, method_name)) for name, method_name in self.__cog_listeners__]

    @classmethod
    def listener(cls, name: str = MISSING):
        """A decorator that marks a function as a listener.

        Parameters
        ------------
        name: :class:`str`
            The name of the event being listened to. If not provided, it
            defaults to the function's name.

        Raises
        --------
        TypeError
            The function is not a coroutine function or a string was not passed as
            the name.
        """

        if name is not MISSING and not isinstance(name, str):
            raise TypeError(
                f"Cog.listener expected str but received {name.__class__.__name__!r} instead."
            )

        def decorator(func: FuncT) -> FuncT:
            actual = func

            if isinstance(actual, staticmethod):
                actual = actual.__func__

            if not asyncio.iscoroutinefunction(actual):
                raise TypeError("Listener function must be a coroutine function.")

            actual.__cog_listener__ = True
            to_assign = name or actual.__name__
            try:
                actual.__cog_listener_names__.append(to_assign)
            except AttributeError:
                actual.__cog_listener_names__ = [to_assign]

            return func

        return decorator

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
