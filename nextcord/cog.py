# SPDX-License-Identifier: MIT
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Type, TypeVar

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

            class MyCog(nextcord.Cog, name="My Cog"):
                pass

    Attributes
    ----------
    name: :class:`str`
        The cog name. By default, it is the name of the class with no modification.
    description: :class:`str`
        The cog description. By default, it is the cleaned docstring of the class.
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

    A cog is a collection of commands and optional state to
    help group commands together. More information on them can be found on
    the :ref:`cogs` page.

    When inheriting from this class, the options shown in :class:`nextcord.CogMeta`
    are equally valid here.
    """

    __cog_name__: str
    __cog_application_commands__: List[BaseApplicationCommand]

    def __new__(cls, *args: Any, **kwargs: Any):
        new_cls = super(Cog, cls).__new__(cls)
        new_cls._read_application_commands()
        return new_cls

    def _read_application_commands(self) -> None:
        """Iterates through the application (sub)commands contained within the Cog, runs their from_callback
        methods, then adds them to the internal list of application commands for this cog.

        After adding all of the application commands into the internal list,
        """
        # circular imports
        from .application_command import (
            BaseApplicationCommand,
            SlashApplicationCommand,
            SlashApplicationSubcommand,
        )

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
        """List[:class:`BaseApplicationCommand`]: Provides the list of application commands in this cog. Subcommands are not included."""
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
        ----------
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
        ----------
        interaction: :class:`.Interaction`
            The invocation interaction.
        """
        pass
