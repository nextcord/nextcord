"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
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
import collections
import collections.abc
import copy
import importlib.util
import inspect
import os
import sys
import traceback
import types
import warnings
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

import nextcord

from . import errors
from .cog import Cog
from .context import Context
from .core import GroupMixin
from .help import DefaultHelpCommand, HelpCommand
from .view import StringView

if TYPE_CHECKING:
    import importlib.machinery

    import aiohttp

    from nextcord.activity import BaseActivity
    from nextcord.enums import Status
    from nextcord.flags import MemberCacheFlags
    from nextcord.mentions import AllowedMentions
    from nextcord.message import Message
    from nextcord.types.checks import ApplicationCheck, ApplicationHook

    from ._types import Check, CoroFunc

__all__ = (
    "when_mentioned",
    "when_mentioned_or",
    "Bot",
    "AutoShardedBot",
    "MissingMessageContentIntentWarning",
)

MISSING: Any = nextcord.utils.MISSING

T = TypeVar("T")
CFT = TypeVar("CFT", bound="CoroFunc")
CXT = TypeVar("CXT", bound="Context")


def when_mentioned(bot: Union[Bot, AutoShardedBot], msg: Message) -> List[str]:
    """A callable that implements a command prefix equivalent to being mentioned.

    These are meant to be passed into the :attr:`.Bot.command_prefix` attribute.
    """
    # bot.user will never be None when this is called
    return [f"<@{bot.user.id}> ", f"<@!{bot.user.id}> "]  # type: ignore


def when_mentioned_or(*prefixes: str) -> Callable[[Union[Bot, AutoShardedBot], Message], List[str]]:
    """A callable that implements when mentioned or other prefixes provided.

    These are meant to be passed into the :attr:`.Bot.command_prefix` attribute.

    Example
    --------

    .. code-block:: python3

        bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'))


    .. note::

        This callable returns another callable, so if this is done inside a custom
        callable, you must call the returned callable, for example:

        .. code-block:: python3

            async def get_prefix(bot, message):
                extras = await prefixes_for(message.guild) # returns a list
                return commands.when_mentioned_or(*extras)(bot, message)


    See Also
    ----------
    :func:`.when_mentioned`
    """

    def inner(bot, msg):
        r = list(prefixes)
        r = when_mentioned(bot, msg) + r
        return r

    return inner


def _is_submodule(parent: str, child: str) -> bool:
    return parent == child or child.startswith(parent + ".")


class MissingMessageContentIntentWarning(UserWarning):
    """Warning category raised when instantiating a :class:`~nextcord.ext.commands.Bot` with a
    :attr:`~nextcord.ext.commands.Bot.command_prefix` but without the :attr:`~nextcord.Intents.message_content`
    intent enabled.

    This warning is not raised when the :attr:`~nextcord.ext.commands.Bot.command_prefix`
    is set to an empty iterable or :func:`when_mentioned <nextcord.ext.commands.when_mentioned>`.

    This warning can be silenced using :func:`warnings.simplefilter`.

    .. code-block:: python3

        import warnings
        from nextcord.ext import commands

        warnings.simplefilter("ignore", commands.MissingMessageContentIntentWarning)
    """

    pass


_NonCallablePrefix = Union[str, Sequence[str]]


class BotBase(GroupMixin):
    def __init__(
        self,
        command_prefix: Union[
            _NonCallablePrefix,
            Callable[
                [Union[Bot, AutoShardedBot], Message],
                Union[Awaitable[_NonCallablePrefix], _NonCallablePrefix],
            ],
        ],
        help_command: Optional[HelpCommand],
        description: Optional[str],
        *,
        owner_id: Optional[int],
        owner_ids: Optional[Iterable[int]],
        strip_after_prefix: bool,
        case_insensitive: bool,
    ):
        super().__init__(
            case_insensitive=case_insensitive,
        )

        self.command_prefix = command_prefix if command_prefix is not MISSING else tuple()
        self.extra_events: Dict[str, List[CoroFunc]] = {}
        self.__cogs: Dict[str, Cog] = {}
        self.__extensions: Dict[str, types.ModuleType] = {}
        self._checks: List[Check] = []
        self._check_once = []
        self._before_invoke = None
        self._after_invoke = None
        self._help_command: Optional[HelpCommand] = None
        self.description = inspect.cleandoc(description) if description else ""
        self.owner_id = owner_id
        self.owner_ids = owner_ids or set()
        self.strip_after_prefix = strip_after_prefix

        if self.owner_id and self.owner_ids:
            raise TypeError("Both owner_id and owner_ids are set.")

        if self.owner_ids and not isinstance(self.owner_ids, collections.abc.Collection):
            raise TypeError(f"owner_ids must be a collection not {self.owner_ids.__class__!r}")

        # if command prefix is a callable, string, or non-empty iterable and message content intent
        # is disabled, warn the user that prefix commands might not work
        if (
            (
                callable(self.command_prefix)
                or isinstance(self.command_prefix, str)
                or len(self.command_prefix) > 0
            )
            and self.command_prefix is not when_mentioned
            and hasattr(self, "intents")
            and not self.intents.message_content  # type: ignore
        ):
            warnings.warn(
                "Message content intent is not enabled. "
                "Prefix commands may not work as expected unless you enable this. "
                "See https://docs.nextcord.dev/en/stable/intents.html#what-happened-to-my-prefix-commands "
                "for more information.",
                category=MissingMessageContentIntentWarning,
                stacklevel=0,
            )

        if help_command is MISSING:
            self.help_command = DefaultHelpCommand()
        else:
            self.help_command = help_command

    # internal helpers

    def dispatch(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        # super() will resolve to Client
        super().dispatch(event_name, *args, **kwargs)  # type: ignore
        ev = "on_" + event_name
        for event in self.extra_events.get(ev, []):
            self._schedule_event(event, ev, *args, **kwargs)  # type: ignore

    @nextcord.utils.copy_doc(nextcord.Client.close)
    async def close(self) -> None:
        for extension in tuple(self.__extensions):
            try:
                self.unload_extension(extension)
            except Exception:
                pass

        for cog in tuple(self.__cogs):
            try:
                self.remove_cog(cog)
            except Exception:
                pass

        await super().close()  # type: ignore

    async def on_command_error(self, context: Context, exception: errors.CommandError) -> None:
        """|coro|

        The default command error handler provided by the bot.

        By default this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.

        This only fires if you do not specify any listeners for command error.
        """
        if self.extra_events.get("on_command_error", None):
            return

        command = context.command
        if command and command.has_error_handler():
            return

        cog = context.cog
        if cog and cog.has_error_handler():
            return

        print(f"Ignoring exception in command {context.command}:", file=sys.stderr)
        traceback.print_exception(
            type(exception), exception, exception.__traceback__, file=sys.stderr
        )

    # global check registration

    def check(self, func: T) -> T:
        r"""A decorator that adds a global check to the bot.

        A global check is similar to a :func:`.check` that is applied
        on a per command basis except it is run before any command checks
        have been verified and applies to every command the bot has.

        .. note::

            This function can either be a regular function or a coroutine.

        Similar to a command :func:`.check`\, this takes a single parameter
        of type :class:`.Context` and can only raise exceptions inherited from
        :exc:`.CommandError`.

        Example
        ---------

        .. code-block:: python3

            @bot.check
            def check_commands(ctx):
                return ctx.command.qualified_name in allowed_commands

        """
        # T was used instead of Check to ensure the type matches on return
        self.add_check(func)  # type: ignore
        return func

    def add_check(self, func: Check, *, call_once: bool = False) -> None:
        """Adds a global check to the bot.

        This is the non-decorator interface to :meth:`.check`
        and :meth:`.check_once`.

        Parameters
        -----------
        func
            The function that was used as a global check.
        call_once: :class:`bool`
            If the function should only be called once per
            :meth:`.invoke` call.
        """

        if call_once:
            self._check_once.append(func)
        else:
            self._checks.append(func)

    def remove_check(self, func: Check, *, call_once: bool = False) -> None:
        """Removes a global check from the bot.

        This function is idempotent and will not raise an exception
        if the function is not in the global checks.

        Parameters
        -----------
        func
            The function to remove from the global checks.
        call_once: :class:`bool`
            If the function was added with ``call_once=True`` in
            the :meth:`.Bot.add_check` call or using :meth:`.check_once`.
        """
        l = self._check_once if call_once else self._checks

        try:
            l.remove(func)
        except ValueError:
            pass

    def check_once(self, func: CFT) -> CFT:
        r"""A decorator that adds a "call once" global check to the bot.

        Unlike regular global checks, this one is called only once
        per :meth:`.invoke` call.

        Regular global checks are called whenever a command is called
        or :meth:`.Command.can_run` is called. This type of check
        bypasses that and ensures that it's called only once, even inside
        the default help command.

        .. note::

            When using this function the :class:`.Context` sent to a group subcommand
            may only parse the parent command and not the subcommands due to it
            being invoked once per :meth:`.Bot.invoke` call.

        .. note::

            This function can either be a regular function or a coroutine.

        Similar to a command :func:`.check`\, this takes a single parameter
        of type :class:`.Context` and can only raise exceptions inherited from
        :exc:`.CommandError`.

        Example
        ---------

        .. code-block:: python3

            @bot.check_once
            def whitelist(ctx):
                return ctx.message.author.id in my_whitelist

        """
        self.add_check(func, call_once=True)
        return func

    async def can_run(self, ctx: Context, *, call_once: bool = False) -> bool:
        data = self._check_once if call_once else self._checks

        if len(data) == 0:
            return True

        # type-checker doesn't distinguish between functions and methods
        return await nextcord.utils.async_all(f(ctx) for f in data)  # type: ignore

    async def is_owner(self, user: nextcord.User) -> bool:
        """|coro|
        Checks if a :class:`~nextcord.User` or :class:`~nextcord.Member` is the owner of
        this bot.

        If an :attr:`owner_id` is not set, it is fetched automatically
        through the use of :meth:`~.Bot.application_info`.

        .. versionchanged:: 1.3
            The function also checks if the application is team-owned if
            :attr:`owner_ids` is not set.

        Parameters
        -----------
        user: :class:`.abc.User`
            The user to check for.

        Returns
        --------
        :class:`bool`
            Whether the user is the owner.
        """

        if self.owner_id:
            return user.id == self.owner_id
        elif self.owner_ids:
            return user.id in self.owner_ids
        else:

            app = await self.application_info()  # type: ignore
            if app.team:
                self.owner_ids = ids = {m.id for m in app.team.members}
                return user.id in ids
            else:
                self.owner_id = owner_id = app.owner.id
                return user.id == owner_id

    def before_invoke(self, coro: CFT) -> CFT:
        """A decorator that registers a coroutine as a pre-invoke hook.

        A pre-invoke hook is called directly before the command is
        called. This makes it a useful function to set up database
        connections or any type of set up required.

        This pre-invoke hook takes a sole parameter, a :class:`.Context`.

        .. note::

            The :meth:`~.Bot.before_invoke` and :meth:`~.Bot.after_invoke` hooks are
            only called if all checks and argument parsing procedures pass
            without error. If any check or argument parsing procedures fail
            then the hooks are not called.

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

        self._before_invoke = coro
        return coro

    def after_invoke(self, coro: CFT) -> CFT:
        r"""A decorator that registers a coroutine as a post-invoke hook.

        A post-invoke hook is called directly after the command is
        called. This makes it a useful function to clean-up database
        connections or any type of clean up required.

        This post-invoke hook takes a sole parameter, a :class:`.Context`.

        .. note::

            Similar to :meth:`~.Bot.before_invoke`\, this is not called unless
            checks and argument parsing procedures succeed. This hook is,
            however, **always** called regardless of the internal command
            callback raising an error (i.e. :exc:`.CommandInvokeError`\).
            This makes it ideal for clean-up scenarios.

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

        self._after_invoke = coro
        return coro

    # listener registration

    def add_listener(self, func: CoroFunc, name: str = MISSING) -> None:
        """The non decorator alternative to :meth:`.listen`.

        Parameters
        -----------
        func: :ref:`coroutine <coroutine>`
            The function to call.
        name: :class:`str`
            The name of the event to listen for. Defaults to ``func.__name__``.

        Example
        --------

        .. code-block:: python3

            async def on_ready(): pass
            async def my_message(message): pass

            bot.add_listener(on_ready)
            bot.add_listener(my_message, 'on_message')

        """
        name = func.__name__ if name is MISSING else name

        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Listeners must be coroutines")

        if name in self.extra_events:
            self.extra_events[name].append(func)
        else:
            self.extra_events[name] = [func]

    def remove_listener(self, func: CoroFunc, name: str = MISSING) -> None:
        """Removes a listener from the pool of listeners.

        Parameters
        -----------
        func
            The function that was used as a listener to remove.
        name: :class:`str`
            The name of the event we want to remove. Defaults to
            ``func.__name__``.
        """

        name = func.__name__ if name is MISSING else name

        if name in self.extra_events:
            try:
                self.extra_events[name].remove(func)
            except ValueError:
                pass

    def listen(self, name: str = MISSING) -> Callable[[CFT], CFT]:
        """A decorator that registers another function as an external
        event listener. Basically this allows you to listen to multiple
        events from different places e.g. such as :func:`.on_ready`

        The functions being listened to must be a :ref:`coroutine <coroutine>`.

        Example
        --------

        .. code-block:: python3

            @bot.listen()
            async def on_message(message):
                print('one')

            # in some other file...

            @bot.listen('on_message')
            async def my_message(message):
                print('two')

        Would print one and two in an unspecified order.

        Raises
        -------
        TypeError
            The function being listened to is not a coroutine.
        """

        def decorator(func: CFT) -> CFT:
            self.add_listener(func, name)
            return func

        return decorator

    # cogs

    def add_cog(self, cog: Cog, *, override: bool = False) -> None:
        """Adds a "cog" to the bot.

        A cog is a class that has its own event listeners and commands.

        .. versionchanged:: 2.0

            :exc:`.ClientException` is raised when a cog with the same name
            is already loaded.

        Parameters
        -----------
        cog: :class:`.Cog`
            The cog to register to the bot.
        override: :class:`bool`
            If a previously loaded cog with the same name should be ejected
            instead of raising an error.

            .. versionadded:: 2.0

        Raises
        -------
        TypeError
            The cog does not inherit from :class:`.Cog`.
        CommandError
            An error happened during loading.
        .ClientException
            A cog with the same name is already loaded.
        """

        if not isinstance(cog, Cog):
            raise TypeError("cogs must derive from Cog")

        cog_name = cog.__cog_name__
        existing = self.__cogs.get(cog_name)

        if existing is not None:
            if not override:
                raise nextcord.ClientException(f"Cog named {cog_name!r} already loaded")
            self.remove_cog(cog_name)

        cog = cog._inject(self)
        self.__cogs[cog_name] = cog
        # TODO: This blind call to nextcord.Client is dumb.
        super().add_cog(cog)  # type: ignore
        # Info: To add the ability to use BaseApplicationCommands in Cogs, the Client has to be aware of cogs. For
        # minimal editing, BotBase must call Client's add_cog function. While it all works out in the end because Bot
        # and AutoShardedBot both end up subclassing Client, this is BotBase and BotBase does not subclass Client, hence
        # this being a "blind call" to nextcord.Client
        # Whatever warning that your IDE is giving about the above line of code is correct. When Bot + BotBase
        # inevitably get reworked, make me happy and fix this.

    def get_cog(self, name: str) -> Optional[Cog]:
        """Gets the cog instance requested.

        If the cog is not found, ``None`` is returned instead.

        Parameters
        -----------
        name: :class:`str`
            The name of the cog you are requesting.
            This is equivalent to the name passed via keyword
            argument in class creation or the class name if unspecified.

        Returns
        --------
        Optional[:class:`Cog`]
            The cog that was requested. If not found, returns ``None``.
        """
        return self.__cogs.get(name)

    def remove_cog(self, name: str) -> Optional[Cog]:
        """Removes a cog from the bot and returns it.

        All registered commands and event listeners that the
        cog has registered will be removed as well.

        If no cog is found then this method has no effect.

        Parameters
        -----------
        name: :class:`str`
            The name of the cog to remove.

        Returns
        -------
        Optional[:class:`.Cog`]
             The cog that was removed. ``None`` if not found.
        """

        cog = self.__cogs.pop(name, None)
        if cog is None:
            return

        help_command = self._help_command
        if help_command and help_command.cog is cog:
            help_command.cog = None
        cog._eject(self)

        # TODO: This blind call to nextcord.Client is dumb.
        super().remove_cog(cog)  # type: ignore
        # See Bot.add_cog() for the reason why.

        return cog

    @property
    def cogs(self) -> Mapping[str, Cog]:
        """Mapping[:class:`str`, :class:`Cog`]: A read-only mapping of cog name to cog."""
        return types.MappingProxyType(self.__cogs)

    # extensions

    def _remove_module_references(self, name: str) -> None:
        # find all references to the module
        # remove the cogs registered from the module
        for cogname, cog in self.__cogs.copy().items():
            if _is_submodule(name, cog.__module__):
                self.remove_cog(cogname)

        # remove all the commands from the module
        for cmd in self.all_commands.copy().values():
            if cmd.module is not None and _is_submodule(name, cmd.module):
                if isinstance(cmd, GroupMixin):
                    cmd.recursively_remove_all_commands()
                self.remove_command(cmd.name)

        # remove all the listeners from the module
        for event_list in self.extra_events.copy().values():
            remove = []
            for index, event in enumerate(event_list):
                if event.__module__ is not None and _is_submodule(name, event.__module__):
                    remove.append(index)

            for index in reversed(remove):
                del event_list[index]

    def _call_module_finalizers(self, lib: types.ModuleType, key: str) -> None:
        try:
            func = getattr(lib, "teardown")
        except AttributeError:
            pass
        else:
            try:
                func(self)
            except Exception:
                pass
        finally:
            self.__extensions.pop(key, None)
            sys.modules.pop(key, None)
            name = lib.__name__
            for module in list(sys.modules.keys()):
                if _is_submodule(name, module):
                    del sys.modules[module]

    def _load_from_module_spec(
        self,
        spec: importlib.machinery.ModuleSpec,
        key: str,
        extras: Optional[Dict[str, Any]] = None,
    ) -> None:
        # precondition: key not in self.__extensions
        lib = importlib.util.module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)  # type: ignore
        except Exception as e:
            del sys.modules[key]
            raise errors.ExtensionFailed(key, e) from e

        try:
            setup = getattr(lib, "setup")
        except AttributeError:
            del sys.modules[key]
            raise errors.NoEntryPointError(key)

        params = inspect.signature(setup).parameters
        has_kwargs = len(params) > 1

        if extras is not None:
            if not has_kwargs:
                raise errors.InvalidSetupArguments(key)
            elif not isinstance(extras, dict):
                raise errors.ExtensionFailed(key, TypeError("Expected 'extras' to be a dictionary"))

        extras = extras or {}
        try:
            if asyncio.iscoroutinefunction(setup):
                try:
                    asyncio.create_task(setup(self, **extras))
                except RuntimeError:
                    raise RuntimeError(
                        f"""
                    Looks like you are attempting to load an asynchronous setup function incorrectly.
                    Please read our FAQ here:
                    https://docs.nextcord.dev/en/stable/faq.html#how-do-i-make-my-setup-function-a-coroutine-and-load-it
                    """
                    )
            else:
                setup(self, **extras)
        except Exception as e:
            del sys.modules[key]
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, key)
            raise errors.ExtensionFailed(key, e) from e
        else:
            self.__extensions[key] = lib

    def _resolve_name(self, name: str, package: Optional[str]) -> str:
        try:
            return importlib.util.resolve_name(name, package)
        except ImportError:
            raise errors.ExtensionNotFound(name)

    def load_extension(
        self, name: str, *, package: Optional[str] = None, extras: Optional[Dict[str, Any]] = None
    ) -> None:
        """Loads an extension.

        An extension is a python module that contains commands, cogs, or
        listeners.

        An extension must have a global function, ``setup`` defined as
        the entry point on what to do when the extension is loaded. This entry
        point must have a single argument, the ``bot``.

        Parameters
        ------------
        name: :class:`str`
            The extension name to load. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when loading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

            .. versionadded:: 1.7
        extras: Optional[:class:`dict`]
            A mapping of kwargs to values to be passed to your
            cog's ``__init__`` method as keyword arguments.

            Usage ::

                # main.py
                bot.load_extension("cogs.me_cog", extras={"keyword_arg": True})

                # cogs/me_cog.py
                class MeCog(commands.Cog):
                    def __init__(self, bot, keyword_arg):
                        self.bot = bot
                        self.keyword_arg = keyword_arg

                def setup(bot, **kwargs):
                    bot.add_cog(MeCog(bot, **kwargs))

                # Alternately
                def setup(bot, keyword_arg):
                    bot.add_cog(MeCog(bot, keyword_arg))

            .. versionadded:: 2.0.0

        Raises
        --------
        ExtensionNotFound
            The extension could not be imported.
            This is also raised if the name of the extension could not
            be resolved using the provided ``package`` parameter.
        ExtensionAlreadyLoaded
            The extension is already loaded.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension or its setup function had an execution error.
        InvalidSetupArguments
            ``load_extension`` was given ``extras`` but the ``setup``
            function did not take any additional arguments.
        """

        name = self._resolve_name(name, package)
        if name in self.__extensions:
            raise errors.ExtensionAlreadyLoaded(name)

        spec = importlib.util.find_spec(name)
        if spec is None:
            raise errors.ExtensionNotFound(name)

        self._load_from_module_spec(spec, name, extras=extras)

    def unload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        """Unloads an extension.

        When the extension is unloaded, all commands, listeners, and cogs are
        removed from the bot and the module is un-imported.

        The extension can provide an optional global function, ``teardown``,
        to do miscellaneous clean-up if necessary. This function takes a single
        parameter, the ``bot``, similar to ``setup`` from
        :meth:`~.Bot.load_extension`.

        Parameters
        ------------
        name: :class:`str`
            The extension name to unload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when unloading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

            .. versionadded:: 1.7

        Raises
        -------
        ExtensionNotFound
            The name of the extension could not
            be resolved using the provided ``package`` parameter.
        ExtensionNotLoaded
            The extension was not loaded.
        """

        name = self._resolve_name(name, package)
        lib = self.__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)

        self._remove_module_references(lib.__name__)
        self._call_module_finalizers(lib, name)

    def reload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        """Atomically reloads an extension.

        This replaces the extension with the same extension, only refreshed. This is
        equivalent to a :meth:`unload_extension` followed by a :meth:`load_extension`
        except done in an atomic way. That is, if an operation fails mid-reload then
        the bot will roll-back to the prior working state.

        Parameters
        ------------
        name: :class:`str`
            The extension name to reload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when reloading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

            .. versionadded:: 1.7

        Raises
        -------
        ExtensionNotLoaded
            The extension was not loaded.
        ExtensionNotFound
            The extension could not be imported.
            This is also raised if the name of the extension could not
            be resolved using the provided ``package`` parameter.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension setup function had an execution error.
        """

        name = self._resolve_name(name, package)
        lib = self.__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)

        # get the previous module states from sys modules
        modules = {
            name: module
            for name, module in sys.modules.items()
            if _is_submodule(lib.__name__, name)
        }

        try:
            # Unload and then load the module...
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, name)
            self.load_extension(name)
        except Exception:
            # if the load failed, the remnants should have been
            # cleaned from the load_extension function call
            # so let's load it from our old compiled library.
            lib.setup(self)
            self.__extensions[name] = lib

            # revert sys.modules back to normal and raise back to caller
            sys.modules.update(modules)
            raise

    def load_extensions(
        self,
        names: List[str],
        *,
        package: Optional[str] = None,
        packages: Optional[List[str]] = None,
        extras: Optional[List[Dict[str, Any]]] = None,
        stop_at_error: bool = False,
    ) -> List[str]:
        """Loads all extensions provided in a list.

        .. note::

            By default, any exceptions found while loading will not be raised but will be printed to console (standard error/`stderr`).

        .. versionadded:: 2.1

        Parameters
        ----------
        names: List[:class:`str`]
            The names of all of the extensions to load.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when loading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.
        packages: Optional[List[:class:`str`]]
            A list of package names to resolve relative imports with.
            This is required when loading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

            Usage::

                # main.py
                bot.load_extensions(
                    [
                        ".my_cog",
                        ".my_cog_two",
                    ],
                    packages=[
                        "cogs.coolcog",
                        "cogs.coolcogtwo",
                    ],
                )

                # cogs/coolcog/my_cog.py
                class MyCog(commands.Cog):
                    def __init__(self, bot):
                        self.bot = bot

                    # ...

                def setup(bot):
                    bot.add_cog(MyCog(bot))

                # cogs/coolcogtwo/my_cog_two.py
                class MyCogTwo(commands.Cog):
                    def __init__(self, bot):
                        self.bot = bot

                    # ...

                def setup(bot):
                    bot.add_cog(MyCogTwo(bot))

        extras: Optional[List[Dict[:class:`str`, Any]]]
            A list of extra arguments to pass to the extension's setup function.

            Usage::

                # main.py
                bot.load_extensions(
                    [
                        ".my_cog",
                        ".my_cog_two",
                    ],
                    package="cogs",
                    extras=[{"my_attribute": 11}, {"my_other_attribute": 12}],
                )

                # cogs/my_cog.py
                class MyCog(commands.Cog):
                    def __init__(self, bot, my_attribute):
                        self.bot = bot
                        self.my_attribute = my_attribute

                    # ...

                def setup(bot, **kwargs):
                    bot.add_cog(MyCog(bot, **kwargs))

                # cogs/my_cog_two.py
                class MyCogTwo(commands.Cog):
                    def __init__(self, bot, my_other_attribute):
                        self.bot = bot
                        self.my_other_attribute = my_other_attribute

                    # ...

                def setup(bot, my_other_attribute):
                    bot.add_cog(MyCogTwo(bot, my_other_attribute))

        stop_at_error: :class:`bool`
            Whether or not an exception should be raised if we encounter one. Set to ``False`` by
            default.

        Returns
        -------
        List[:class:`str`]
            A list that contains the names of all of the extensions
            that loaded successfully.

        Raises
        ------
        ValueError
            The length of ``packages`` or the length of ``extras` is not equal to the length of ``names``.
        InvalidArgument
            You passed in both ``package`` and ``packages``.
        ExtensionNotFound
            An extension could not be imported.
        ExtensionAlreadyLoaded
            An extension is already loaded.
        NoEntryPointError
            An extension does not have a setup function.
        ExtensionFailed
            An extension or its setup function had an execution error.
        """
        if package and packages:
            raise errors.BadArgument("Cannot provide both package and packages.")
        if packages and len(packages) != len(names):
            raise ValueError("The length of packages must match the length of extensions.")
        if extras and len(extras) != len(names):
            raise ValueError("The length of extra parameters must match the length of extensions.")

        packages_itr: Optional[Iterator] = iter(packages) if packages else None
        extras_itr: Optional[Iterator] = iter(extras) if extras else None

        loaded_extensions: List[str] = []

        for extension in names:
            if packages_itr:
                package = next(packages_itr)
            cur_extra: Optional[Dict[str, Any]] = next(extras_itr) if extras_itr else None

            try:
                self.load_extension(extension, package=package, extras=cur_extra)
            except Exception as e:
                if stop_at_error:
                    raise e
                else:
                    # we print the exception instead of raising it because we want to continue loading extensions
                    traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
            else:
                loaded_extensions.append(extension)

        return loaded_extensions

    def load_extensions_from_module(
        self, source_module: str, *, ignore: Optional[List[str]] = None, stop_at_error: bool = False
    ) -> List[str]:
        """Loads all extensions found in a module.

        Once an extension found in a module has been loaded and did not throw
        any exceptions, it will be added to a list of extension names that
        will be returned.

        .. note::

            By default, any exceptions found while loading will not be raised but will be printed to console (standard error/`stderr`).

        .. versionadded:: 2.1

        Parameters
        ----------
        source_module: :class:`str`
            The name of the source module to look for submodules.
        ignore: Optional[List[:class:`str`]]
            File names of extensions to ignore.
        stop_at_error: :class:`bool`
            Whether or not an exception should be raised if we encounter one. Set to ``False`` by
            default.

        Returns
        -------
        List[:class:`str`]
            A list that contains the names of all of the extensions
            that loaded successfully.

        Raises
        ------
        ValueError
            The module at ``source_module`` is not found, or the module at ``source_module``
            has no submodules.
        ExtensionNotFound
            An extension could not be imported.
        ExtensionAlreadyLoaded
            An extension is already loaded.
        NoEntryPointError
            An extension does not have a setup function.
        ExtensionFailed
            An extension or its setup function had an execution error.
        """
        name = self._resolve_name(source_module, None)
        spec = importlib.util.find_spec(name)
        if spec is None:
            raise ValueError(f"Module {name} not found")

        submodule_paths = spec.submodule_search_locations
        if submodule_paths is None:
            raise ValueError(f"Module {name} has no submodules")

        extensions: List[str] = []

        for submodule_path in submodule_paths:
            submodules = [
                (f"{name}.{submodule[:-3]}" if submodule.endswith(".py") else f"{name}.{submodule}")
                for submodule in os.listdir(submodule_path)
                if not submodule.startswith("_")
            ]
            if ignore is not None:
                submodules = [s for s in submodules if s not in ignore]

            extensions.extend(self.load_extensions(submodules, stop_at_error=stop_at_error))

        return extensions

    @property
    def extensions(self) -> Mapping[str, types.ModuleType]:
        """Mapping[:class:`str`, :class:`py:types.ModuleType`]: A read-only mapping of extension name to extension."""
        return types.MappingProxyType(self.__extensions)

    # help command stuff

    @property
    def help_command(self) -> Optional[HelpCommand]:
        return self._help_command

    @help_command.setter
    def help_command(self, value: Optional[HelpCommand]) -> None:
        if value is not None:
            if not isinstance(value, HelpCommand):
                raise TypeError("help_command must be a subclass of HelpCommand")
            if self._help_command is not None:
                self._help_command._remove_from_bot(self)
            self._help_command = value
            value._add_to_bot(self)
        elif self._help_command is not None:
            self._help_command._remove_from_bot(self)
            self._help_command = None
        else:
            self._help_command = None

    # command processing

    async def get_prefix(self, message: Message) -> Union[List[str], str]:
        """|coro|

        Retrieves the prefix the bot is listening to
        with the message as a context.

        Parameters
        -----------
        message: :class:`nextcord.Message`
            The message context to get the prefix of.

        Returns
        --------
        Union[List[:class:`str`], :class:`str`]
            A list of prefixes or a single prefix that the bot is
            listening for.
        """
        prefix = self.command_prefix
        if callable(prefix):
            ret = await nextcord.utils.maybe_coroutine(prefix, self, message)  # type: ignore
            # the callable wants an (AutoSharded)Bot but this is BotBase
        else:
            ret = prefix

        if not isinstance(ret, str):
            try:
                ret = list(ret)
            except TypeError:
                # It's possible that a generator raised this exception.  Don't
                # replace it with our own error if that's the case.
                if isinstance(ret, collections.abc.Iterable):
                    raise

                raise TypeError(
                    "command_prefix must be plain string, iterable of strings, or callable "
                    f"returning either of these, not {ret.__class__.__name__}"
                )

        return ret

    async def get_context(self, message: Message, *, cls: Type[CXT] = Context) -> CXT:
        r"""|coro|

        Returns the invocation context from the message.

        This is a more low-level counter-part for :meth:`.process_commands`
        to allow users more fine grained control over the processing.

        The returned context is not guaranteed to be a valid invocation
        context, :attr:`.Context.valid` must be checked to make sure it is.
        If the context is not valid then it is not a valid candidate to be
        invoked under :meth:`~.Bot.invoke`.

        Parameters
        -----------
        message: :class:`nextcord.Message`
            The message to get the invocation context from.
        cls
            The factory class that will be used to create the context.
            By default, this is :class:`.Context`. Should a custom
            class be provided, it must be similar enough to :class:`.Context`\'s
            interface.

        Returns
        --------
        :class:`.Context`
            The invocation context. The type of this can change via the
            ``cls`` parameter.
        """

        view = StringView(message.content)
        ctx: CXT = cls(prefix=None, view=view, bot=self, message=message)  # type: ignore
        # pyright/lance has no idea how typevars work for some reason

        if message.author.id == self.user.id:  # type: ignore
            return ctx

        prefix = await self.get_prefix(message)
        invoked_prefix = prefix

        if isinstance(prefix, str):
            if not view.skip_string(prefix):
                return ctx
        else:
            try:
                # if the context class' __init__ consumes something from the view this
                # will be wrong.  That seems unreasonable though.
                if message.content.startswith(tuple(prefix)):
                    invoked_prefix = nextcord.utils.find(view.skip_string, prefix)
                else:
                    return ctx

            except TypeError:
                if not isinstance(prefix, list):
                    raise TypeError(
                        "get_prefix must return either a string or a list of string, "
                        f"not {prefix.__class__.__name__}"
                    )

                # It's possible a bad command_prefix got us here.
                for value in prefix:
                    if not isinstance(value, str):
                        raise TypeError(
                            "Iterable command_prefix or list returned from get_prefix must "
                            f"contain only strings, not {value.__class__.__name__}"
                        )

                # Getting here shouldn't happen
                raise

        if self.strip_after_prefix:
            view.skip_ws()

        invoker = view.get_word()
        ctx.invoked_with = invoker
        # type-checker fails to narrow invoked_prefix type.
        ctx.prefix = invoked_prefix  # type: ignore
        ctx.command = self.all_commands.get(invoker)
        return ctx

    async def invoke(self, ctx: Context) -> None:
        """|coro|

        Invokes the command given under the invocation context and
        handles all the internal event dispatch mechanisms.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to invoke.
        """
        if ctx.command is not None:
            self.dispatch("command", copy.copy(ctx))
            try:
                if await self.can_run(ctx, call_once=True):
                    await ctx.command.invoke(ctx)
                else:
                    raise errors.CheckFailure("The global check once functions failed.")
            except errors.CommandError as exc:
                await ctx.command.dispatch_error(ctx, exc)
            else:
                self.dispatch("command_completion", ctx)
        elif ctx.invoked_with:
            exc = errors.CommandNotFound(ctx.invoked_with)
            self.dispatch("command_error", ctx, exc)

    async def process_commands(self, message: Message) -> None:
        """|coro|

        This function processes the commands that have been registered
        to the bot and other groups. Without this coroutine, none of the
        commands will be triggered.

        By default, this coroutine is called inside the :func:`.on_message`
        event. If you choose to override the :func:`.on_message` event, then
        you should invoke this coroutine as well.

        This is built using other low level tools, and is equivalent to a
        call to :meth:`~.Bot.get_context` followed by a call to :meth:`~.Bot.invoke`.

        This also checks if the message's author is a bot and doesn't
        call :meth:`~.Bot.get_context` or :meth:`~.Bot.invoke` if so.

        Parameters
        -----------
        message: :class:`nextcord.Message`
            The message to process commands for.
        """
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def on_message(self, message):
        await self.process_commands(message)

    def add_application_command_check(self, func: ApplicationCheck) -> None:
        """Adds a global application check to the bot.

        This is the non-decorator interface to :meth:`.check`
        and :meth:`.check_once`.

        Parameters
        -----------
        func: Callable[[:class:`Interaction`], MaybeCoro[bool]]]
            The function that was used as a global application check.
        """

        self._connection._application_command_checks.append(func)  # type: ignore

    def remove_application_command_check(self, func: ApplicationCheck) -> None:
        """Removes a global check from the bot.

        This function is idempotent and will not raise an exception
        if the function is not in the global checks.

        Parameters
        -----------
        func: Callable[[:class:`Interaction`], MaybeCoro[bool]]]
            The function to remove from the global application checks.
        """

        try:
            self._connection._application_command_checks.remove(func)  # type: ignore
        except ValueError:
            pass

    def application_command_check(self, func: Callable) -> ApplicationCheck:
        r"""A decorator that adds a global application check to the bot.

        A global check is similar to a :func:`.check` that is applied
        on a per command basis except it is run before any command checks
        have been verified and applies to every command the bot has.

        .. note::

            This function can either be a regular function or a coroutine.

        Similar to a command :func:`.check`\, this takes a single parameter
        of type :class:`.Interaction` and can only raise exceptions inherited from
        :exc:`.ApplicationError`.

        Example
        ---------

        .. code-block:: python3

            @client.check
            def check_commands(interaction: Interaction) -> bool:
                return interaction.application_command.qualified_name in allowed_commands

        """
        return self.add_application_command_check(func)  # type: ignore

    def application_command_before_invoke(self, coro: ApplicationHook) -> ApplicationHook:
        """A decorator that registers a coroutine as a pre-invoke hook.

        A pre-invoke hook is called directly before the command is
        called. This makes it a useful function to set up database
        connections or any type of set up required.

        This pre-invoke hook takes a sole parameter, a :class:`.Interaction`.

        .. note::

            The :meth:`.application_command_before_invoke` and :meth:`.application_command_after_invoke`
            hooks are only called if all checks pass without error. If any check fails, then the hooks
            are not called.

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

        self._connection._application_command_before_invoke = coro  # type: ignore
        return coro

    def application_command_after_invoke(self, coro: ApplicationHook) -> ApplicationHook:
        r"""A decorator that registers a coroutine as a post-invoke hook.

        A post-invoke hook is called directly after the command is
        called. This makes it a useful function to clean-up database
        connections or any type of clean up required. There may only be
        one global post-invoke hook.

        This post-invoke hook takes a sole parameter, a :class:`.Interaction`.

        .. note::

            Similar to :meth:`~.Client.application_command_before_invoke`\, this is not called unless
            checks succeed. This hook is, however, **always** called regardless of the internal command
            callback raising an error (i.e. :exc:`.ApplicationInvokeError`\).
            This makes it ideal for clean-up scenarios.

        Parameters
        -----------
        coro: :ref:`coroutine`
            The coroutine to register as the post-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError("The post-invoke hook must be a coroutine.")

        self._connection._application_command_after_invoke = coro  # type: ignore
        return coro


class Bot(BotBase, nextcord.Client):
    """Represents a discord bot.

    This class is a subclass of :class:`nextcord.Client` and as a result
    anything that you can do with a :class:`nextcord.Client` you can do with
    this bot.

    This class also subclasses :class:`.GroupMixin` to provide the functionality
    to manage commands.

    Attributes
    -----------
    command_prefix
        The command prefix is what the message content must contain initially
        to have a command invoked. This prefix could either be a string to
        indicate what the prefix should be, or a callable that takes in the bot
        as its first parameter and :class:`nextcord.Message` as its second
        parameter and returns the prefix. This is to facilitate "dynamic"
        command prefixes. This callable can be either a regular function or
        a coroutine.

        An empty string as the prefix always matches, enabling prefix-less
        command invocation. While this may be useful in DMs it should be avoided
        in servers, as it's likely to cause performance issues and unintended
        command invocations.

        The command prefix could also be an iterable of strings indicating that
        multiple checks for the prefix should be used and the first one to
        match will be the invocation prefix. You can get this prefix via
        :attr:`.Context.prefix`.

        .. note::

            When passing multiple prefixes be careful to not pass a prefix
            that matches a longer prefix occurring later in the sequence.  For
            example, if the command prefix is ``('!', '!?')``  the ``'!?'``
            prefix will never be matched to any message as the previous one
            matches messages starting with ``!?``. This is especially important
            when passing an empty string, it should always be last as no prefix
            after it will be matched.
    case_insensitive: :class:`bool`
        Whether the commands should be case insensitive. Defaults to ``False``. This
        attribute does not carry over to groups. You must set it to every group if
        you require group commands to be case insensitive as well.
    description: :class:`str`
        The content prefixed into the default help message.
    help_command: Optional[:class:`.HelpCommand`]
        The help command implementation to use. This can be dynamically
        set at runtime. To remove the help command pass ``None``. For more
        information on implementing a help command, see :ref:`ext_commands_help_command`.
    owner_id: Optional[:class:`int`]
        The user ID that owns the bot. If this is not set and is then queried via
        :meth:`.is_owner` then it is fetched automatically using
        :meth:`~.Bot.application_info`.
    owner_ids: Optional[Collection[:class:`int`]]
        The user IDs that owns the bot. This is similar to :attr:`owner_id`.
        If this is not set and the application is team based, then it is
        fetched automatically using :meth:`~.Bot.application_info`.
        For performance reasons it is recommended to use a :class:`set`
        for the collection. You cannot set both ``owner_id`` and ``owner_ids``.

        .. versionadded:: 1.3
    strip_after_prefix: :class:`bool`
        Whether to strip whitespace characters after encountering the command
        prefix. This allows for ``!   hello`` and ``!hello`` to both work if
        the ``command_prefix`` is set to ``!``. Defaults to ``False``.

        .. versionadded:: 1.7
    """

    def __init__(
        self,
        command_prefix: Union[
            _NonCallablePrefix,
            Callable[
                [Union[Bot, AutoShardedBot], Message],
                Union[Awaitable[_NonCallablePrefix], _NonCallablePrefix],
            ],
        ] = tuple(),
        help_command: Optional[HelpCommand] = MISSING,
        description: Optional[str] = None,
        *,
        max_messages: Optional[int] = 1000,
        connector: Optional[aiohttp.BaseConnector] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        shard_id: Optional[int] = None,
        shard_count: Optional[int] = None,
        application_id: Optional[int] = None,
        intents: nextcord.Intents = nextcord.Intents.default(),
        member_cache_flags: MemberCacheFlags = MISSING,
        chunk_guilds_at_startup: bool = MISSING,
        status: Optional[Status] = None,
        activity: Optional[BaseActivity] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        heartbeat_timeout: float = 60.0,
        guild_ready_timeout: float = 2.0,
        assume_unsync_clock: bool = True,
        enable_debug_events: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        lazy_load_commands: bool = True,
        rollout_associate_known: bool = True,
        rollout_delete_unknown: bool = True,
        rollout_register_new: bool = True,
        rollout_update_known: bool = True,
        rollout_all_guilds: bool = False,
        owner_id: Optional[int] = None,
        owner_ids: Optional[Iterable[int]] = None,
        strip_after_prefix: bool = False,
        case_insensitive: bool = False,
    ):
        nextcord.Client.__init__(
            self,
            max_messages=max_messages,
            connector=connector,
            proxy=proxy,
            proxy_auth=proxy_auth,
            shard_id=shard_id,
            shard_count=shard_count,
            application_id=application_id,
            intents=intents,
            member_cache_flags=member_cache_flags,
            chunk_guilds_at_startup=chunk_guilds_at_startup,
            status=status,
            activity=activity,
            allowed_mentions=allowed_mentions,
            heartbeat_timeout=heartbeat_timeout,
            guild_ready_timeout=guild_ready_timeout,
            assume_unsync_clock=assume_unsync_clock,
            enable_debug_events=enable_debug_events,
            loop=loop,
            lazy_load_commands=lazy_load_commands,
            rollout_associate_known=rollout_associate_known,
            rollout_delete_unknown=rollout_delete_unknown,
            rollout_register_new=rollout_register_new,
            rollout_update_known=rollout_update_known,
            rollout_all_guilds=rollout_all_guilds,
        )

        BotBase.__init__(
            self,
            command_prefix=command_prefix,
            help_command=help_command,
            description=description,
            owner_id=owner_id,
            owner_ids=owner_ids,
            strip_after_prefix=strip_after_prefix,
            case_insensitive=case_insensitive,
        )


class AutoShardedBot(BotBase, nextcord.AutoShardedClient):
    """This is similar to :class:`.Bot` except that it is inherited from
    :class:`nextcord.AutoShardedClient` instead.
    """

    def __init__(
        self,
        command_prefix: Union[
            _NonCallablePrefix,
            Callable[
                [Union[Bot, AutoShardedBot], Message],
                Union[Awaitable[_NonCallablePrefix], _NonCallablePrefix],
            ],
        ] = tuple(),
        help_command: Optional[HelpCommand] = MISSING,
        description: Optional[str] = None,
        *,
        max_messages: Optional[int] = 1000,
        connector: Optional[aiohttp.BaseConnector] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        shard_id: Optional[int] = None,
        shard_count: Optional[int] = None,
        shard_ids: Optional[list[int]] = None,
        application_id: Optional[int] = None,
        intents: nextcord.Intents = nextcord.Intents.default(),
        member_cache_flags: MemberCacheFlags = MISSING,
        chunk_guilds_at_startup: bool = MISSING,
        status: Optional[Status] = None,
        activity: Optional[BaseActivity] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        heartbeat_timeout: float = 60.0,
        guild_ready_timeout: float = 2.0,
        assume_unsync_clock: bool = True,
        enable_debug_events: bool = False,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        lazy_load_commands: bool = True,
        rollout_associate_known: bool = True,
        rollout_delete_unknown: bool = True,
        rollout_register_new: bool = True,
        rollout_update_known: bool = True,
        rollout_all_guilds: bool = False,
        owner_id: Optional[int] = None,
        owner_ids: Optional[Iterable[int]] = None,
        strip_after_prefix: bool = False,
        case_insensitive: bool = False,
    ):
        nextcord.AutoShardedClient.__init__(
            self,
            max_messages=max_messages,
            connector=connector,
            proxy=proxy,
            proxy_auth=proxy_auth,
            shard_id=shard_id,
            shard_count=shard_count,
            shard_ids=shard_ids,
            application_id=application_id,
            intents=intents,
            member_cache_flags=member_cache_flags,
            chunk_guilds_at_startup=chunk_guilds_at_startup,
            status=status,
            activity=activity,
            allowed_mentions=allowed_mentions,
            heartbeat_timeout=heartbeat_timeout,
            guild_ready_timeout=guild_ready_timeout,
            assume_unsync_clock=assume_unsync_clock,
            enable_debug_events=enable_debug_events,
            loop=loop,
            lazy_load_commands=lazy_load_commands,
            rollout_associate_known=rollout_associate_known,
            rollout_delete_unknown=rollout_delete_unknown,
            rollout_register_new=rollout_register_new,
            rollout_update_known=rollout_update_known,
            rollout_all_guilds=rollout_all_guilds,
        )

        BotBase.__init__(
            self,
            command_prefix=command_prefix,
            help_command=help_command,
            description=description,
            owner_id=owner_id,
            owner_ids=owner_ids,
            strip_after_prefix=strip_after_prefix,
            case_insensitive=case_insensitive,
        )
