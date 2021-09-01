import collections
from nextcord.utils import MISSING
import nextcord
import types
import inspect
import sys
import traceback
import asyncio
import importlib.util
from typing import Any, Callable, Dict, List, Mapping, Optional, TypeVar
from nextcord.client import Client
from .cog import Cog
from nextcord.ext.abc import ContextBase
from nextcord.ext.abc._types import CoroFunc, Check, CoroFuncT
from . import errors

CheckType = TypeVar("CheckType", bound="Check")

class Bot(Client):
    def __init__(self, description=None, **options):
        super().__init__(**options)
        self.extra_events: Dict[str, List[CoroFunc]] = {}
        self.__cogs: Dict[str, Cog] = {}
        self.__extensions: Dict[str, types.ModuleType] = {}
        self._checks: List[Check] = []
        self._check_once = []
        self._before_invoke = None
        self._after_invoke = None
        self.description = inspect.cleandoc(description) if description else ''
        self.owner_id = options.get('owner_id')
        self.owner_ids = options.get('owner_ids', set())

        if self.owner_id and self.owner_ids:
            raise TypeError('Both owner_id and owner_ids are set.')

        if self.owner_ids and not isinstance(self.owner_ids, collections.abc.Collection):
            raise TypeError(
                f'owner_ids must be a collection not {self.owner_ids.__class__!r}')

    # internal helpers

    def dispatch(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        super().dispatch(event_name, *args, **kwargs)  # type: ignore
        ev = 'on_' + event_name
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

        await super().close()

    async def on_command_error(self, context: ContextBase, exception: errors.CommandError) -> None:
        """|coro|

        The default command error handler provided by the bot.

        By default this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.

        This only fires if you do not specify any listeners for command error.
        """
        if self.extra_events.get('on_command_error', None):
            return

        command = context.command
        if command and command.has_error_handler():
            return

        cog = context.cog
        if cog and cog.has_error_handler():
            return

        print(f'Ignoring exception in command {context.command}:', file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    # global check registration

    def check(self, func: CheckType) -> CheckType:
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
        self.add_check(func)
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
        checks = self._check_once if call_once else self._checks

        try:
            checks.remove(func)
        except ValueError:
            pass

    def check_once(self, func: CoroFuncT) -> CoroFuncT:
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

    async def can_run(self, ctx: ContextBase, *, call_once: bool = False) -> bool:
        checks = self._check_once if call_once else self._checks

        if not checks:
            return True

        # type-checker doesn't distinguish between functions and methods
        # type: ignore
        return await nextcord.utils.async_all(f(ctx) for f in checks)

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

            app = await self.application_info()
            if app.team:
                self.owner_ids = ids = {m.id for m in app.team.members}
                return user.id in ids
            else:
                self.owner_id = owner_id = app.owner.id
                return user.id == owner_id

    def before_invoke(self, coro: CoroFuncT) -> CoroFuncT:
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
            raise TypeError('The pre-invoke hook must be a coroutine.')

        self._before_invoke = coro
        return coro

    def after_invoke(self, coro: CoroFuncT) -> CoroFuncT:
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
            raise TypeError('The post-invoke hook must be a coroutine.')

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
            raise TypeError('Listeners must be coroutines')

        if name not in self.extra_events:
            self.extra_events[name] = []
        self.extra_events[name].append(func)

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

    def listen(self, name: str = MISSING) -> Callable[[CoroFuncT], CoroFuncT]:
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

        def decorator(func: CoroFuncT) -> CoroFuncT:
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

        if not (isinstance(cog, Cog)):
            raise TypeError('cogs must derive from Cog')

        cog_name = cog.__cog_name__
        existing = self.__cogs.get(cog_name)

        if existing is not None:
            if not override:
                raise nextcord.ClientException(f'Cog named {cog_name!r} already loaded')
            self.remove_cog(cog_name)

        cog = cog._inject(self)
        self.__cogs[cog_name] = cog

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
            return None

        cog._eject(self)

        return cog

    @property
    def cogs(self) -> Mapping[str, Cog]:
        """Mapping[:class:`str`, :class:`Cog`]: A read-only mapping of cog name to cog."""
        return types.MappingProxyType(self.__cogs)

    # extensions

    def _is_submodule(self, parent: str, child: str) -> bool:
        return parent == child or child.startswith(parent + ".")

    def _remove_registered_cogs(self, name: str) -> None:
        # remove the cogs registered from the module
        for cogname, cog in self.__cogs.copy().items():
            if self._is_submodule(name, cog.__module__):
                self.remove_cog(cogname)

    def _remove_listeners(self, name: str) -> None:
        # remove all the listeners from the module
        for event_list in self.extra_events.copy().values():
            remove = []
            for index, event in enumerate(event_list):
                if event.__module__ is not None and self._is_submodule(name, event.__module__):
                    remove.append(index)

            for index in reversed(remove):
                del event_list[index]

    def _remove_module_references(self, name: str) -> None:
        # find all references to the module
        self._remove_registered_cogs(name)
        self._remove_listeners(name)


    def _call_module_finalizers(self, lib: types.ModuleType, key: str) -> None:
        try:
            func = getattr(lib, 'teardown')
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
                if self._is_submodule(name, module):
                    del sys.modules[module]

    def _load_from_module_spec(self, spec: importlib.machinery.ModuleSpec, key: str) -> None:
        # precondition: key not in self.__extensions
        lib = importlib.util.module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)  # type: ignore
        except Exception as e:
            del sys.modules[key]
            raise errors.ExtensionFailed(key, e) from e

        try:
            setup = getattr(lib, 'setup')
        except AttributeError:
            del sys.modules[key]
            raise errors.NoEntryPointError(key)

        try:
            setup(self)
        except Exception as e:
            del sys.modules[key]
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, key)
            raise errors.ExtensionFailed(key, e) from e
        else:
            self.__extensions[key] = lib

    def _resolve_name(self, name: str, package: Optional[str]) -> str:
        try:
            # type checker thinks resolve_name can't take optional for package
            return importlib.util.resolve_name(name, package) # type: ignore
        except ImportError:
            raise errors.ExtensionNotFound(name)

    def load_extension(self, name: str, *, package: Optional[str] = None) -> None:
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
        """

        name = self._resolve_name(name, package)
        if name in self.__extensions:
            raise errors.ExtensionAlreadyLoaded(name)

        spec = importlib.util.find_spec(name)
        if spec is None:
            raise errors.ExtensionNotFound(name)

        self._load_from_module_spec(spec, name)

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
            if self._is_submodule(lib.__name__, name)
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
            lib.setup(self)  # type: ignore
            self.__extensions[name] = lib

            # revert sys.modules back to normal and raise back to caller
            sys.modules.update(modules)
            raise

    @property
    def extensions(self) -> Mapping[str, types.ModuleType]:
        """Mapping[:class:`str`, :class:`py:types.ModuleType`]: A read-only mapping of extension name to extension."""
        return types.MappingProxyType(self.__extensions)


class AutoShardedBot(nextcord.AutoShardedClient, Bot):
    """This is similar to :class:`.Bot` except that it is inherited from
    :class:`nextcord.AutoShardedClient` instead.
    """
    pass