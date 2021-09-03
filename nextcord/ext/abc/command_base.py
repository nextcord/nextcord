import datetime
from typing_extensions import Concatenate, ParamSpec
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union
from ._types import CogT, CommandT, ContextT, Coro, Check, Hook, HookT, Error, ErrorT
from .context_base import ContextBase
from nextcord.ext.interactions import CooldownMapping, BucketType, MaxConcurrency, Cog
from nextcord.ext.converters import Greedy
from nextcord.ext.errors import CommandError, CommandInvokeError, CommandOnCooldown, CheckFailure, DisabledCommand
import functools
import nextcord
import asyncio
import inspect


T = TypeVar('T')
P = ParamSpec('P')

class CommandBase(Generic[CogT, P, T]):
    __original_kwargs__: Dict[str, Any]

    def __new__(cls: Type[CommandT], *args: Any, **kwargs: Any) -> CommandT:
        # if you're wondering why this is done, it's because we need to ensure
        # we have a complete original copy of **kwargs even for classes that
        # mess with it by popping before delegating to the subclass __init__.
        # In order to do this, we need to control the instance creation and
        # inject the original kwargs through __new__ rather than doing it
        # inside __init__.
        self = super().__new__(cls)

        # we do a shallow copy because it's probably the most common use case.
        # this could potentially break if someone modifies a list or something
        # while it's in movement, but for now this is the cheapest and
        # fastest way to do what we want.
        self.__original_kwargs__ = kwargs.copy()
        return self

    # mypy doesn't support ParamSpec in generics
    def __init__(self, func: Union[ # type: ignore
        Callable[Concatenate[CogT, ContextT, P], Coro[T]],
        Callable[Concatenate[ContextT, P], Coro[T]],
    ], **kwargs: Any):
        self.set_fields(func, **kwargs)

    def set_fields(self, func: Union[ # type: ignore
        Callable[Concatenate[CogT, ContextT, P], Coro[T]],
        Callable[Concatenate[ContextT, P], Coro[T]],
    ], **kwargs: Any):
        """Does the heavy lifting for init. Classes which extend this one should set all their fields by overriding this function and calling super().set_fields(func, **kwargs). This function is called by update as well by __init__, which is why it's not in __init__.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')

        self.name = kwargs.get('name') or func.__name__
        if not isinstance(self.name, str):
            raise TypeError('Name of a command must be a string.')

        self.callback = func
        self.enabled: bool = kwargs.get('enabled', True)

        self.extras: Dict[str, Any] = kwargs.get('extras', {})

        help_doc = kwargs.get('help')
        if help_doc is not None:
            help_doc = inspect.cleandoc(help_doc)
        else:
            help_doc = inspect.getdoc(func)
            if isinstance(help_doc, bytes):
                help_doc = help_doc.decode('utf-8')

        self.help: Optional[str] = help_doc
        self.brief: Optional[str] = kwargs.get('brief')
        self.usage: Optional[str] = kwargs.get('usage')
        self.description: str = inspect.cleandoc(kwargs.get('description', ''))
        self.hidden: bool = kwargs.get('hidden', False)

        try:
            checks = func.__commands_checks__
            checks.reverse()
        except AttributeError:
            checks = kwargs.get('checks', [])

        self.checks: List[Check] = checks

        try:
            cooldown = func.__commands_cooldown__
        except AttributeError:
            cooldown = kwargs.get('cooldown')

        if cooldown is None:
            buckets = CooldownMapping(cooldown, BucketType.default)
        elif isinstance(cooldown, CooldownMapping):
            buckets = cooldown
        else:
            raise TypeError("Cooldown must be a an instance of CooldownMapping or None.")
        self._buckets: CooldownMapping = buckets

        try:
            max_concurrency = func.__commands_max_concurrency__
        except AttributeError:
            max_concurrency = kwargs.get('max_concurrency')

        self._max_concurrency: Optional[MaxConcurrency] = max_concurrency

        self.cog: Optional[CogT] = None

        self._before_invoke: Optional[Hook] = None
        try:
            before_invoke = func.__before_invoke__
        except AttributeError:
            pass
        else:
            self.before_invoke(before_invoke)

        self._after_invoke: Optional[Hook] = None
        try:
            after_invoke = func.__after_invoke__
        except AttributeError:
            pass
        else:
            self.after_invoke(after_invoke)

    @property
    def callback(self) -> Union[ # type: ignore
        Callable[Concatenate[CogT, ContextBase, P], Coro[T]],
        Callable[Concatenate[ContextBase, P], Coro[T]],
    ]:
        return self._callback

    @callback.setter
    def callback(self, function: Union[ # type: ignore
        Callable[Concatenate[CogT, ContextBase, P], Coro[T]],
        Callable[Concatenate[ContextBase, P], Coro[T]],
    ]) -> None:
        self._callback = function
        unwrap = unwrap_function(function)
        self.module = unwrap.__module__

        try:
            globalns = unwrap.__globals__ # type: ignore
        except AttributeError:
            globalns = {}

        self.params = get_signature_parameters(function, globalns)

    def add_check(self, func: Check) -> None:
        """Adds a check to the command.

        This is the non-decorator interface to :func:`.check`.

        .. versionadded:: 1.3

        Parameters
        -----------
        func
            The function that will be used as a check.
        """

        self.checks.append(func)

    def remove_check(self, func: Check) -> None:
        """Removes a check from the command.

        This function is idempotent and will not raise an exception
        if the function is not in the command's checks.

        .. versionadded:: 1.3

        Parameters
        -----------
        func
            The function to remove from the checks.
        """

        try:
            self.checks.remove(func)
        except ValueError:
            pass

    def update(self, **kwargs: Any) -> None:
        """Updates :class:`CommandBase` instance with updated attribute.

        This works similarly to the :func:`.command` decorator in terms
        of parameters in that they are passed to the :class:`Command` or
        subclass constructors, sans the name and callback.
        """
        self.set_fields(self.callback, **dict(self.__original_kwargs__, **kwargs))

    async def __call__(self, context: ContextBase, *args: P.args, **kwargs: P.kwargs) -> T: # type: ignore
        """|coro|

        Calls the internal callback that the command holds.

        .. note::

            This bypasses all mechanisms -- including checks, converters,
            invoke hooks, cooldowns, etc. You must take care to pass
            the proper arguments and types to this function.

        .. versionadded:: 1.3
        """
        if self.cog is not None:
            return await self.callback(self.cog, context, *args, **kwargs)
        else:
            return await self.callback(context, *args, **kwargs)

    def _ensure_assignment_on_copy(self, other: CommandT) -> CommandT:
        other._before_invoke = self._before_invoke
        other._after_invoke = self._after_invoke
        if self.checks != other.checks:
            other.checks = self.checks.copy()
        if self._buckets.valid and not other._buckets.valid:
            other._buckets = self._buckets.copy()
        if self._max_concurrency != other._max_concurrency:
            # _max_concurrency won't be None at this point
            other._max_concurrency = self._max_concurrency.copy()  # type: ignore

        try:
            other.on_error = self.on_error
        except AttributeError:
            pass
        return other

    def copy(self: CommandT) -> CommandT:
        """Creates a copy of this command.

        Returns
        --------
        :class:`Command`
            A new instance of this command.
        """
        ret = self.__class__(self.callback, **self.__original_kwargs__)
        return self._ensure_assignment_on_copy(ret)

    def _update_copy(self: CommandT, kwargs: Dict[str, Any]) -> CommandT:
        if kwargs:
            kw = kwargs.copy()
            kw.update(self.__original_kwargs__)
            copy = self.__class__(self.callback, **kw)
            return self._ensure_assignment_on_copy(copy)
        else:
            return self.copy()

    async def dispatch_error(self, ctx: ContextBase, error: Exception) -> None:
        ctx.command_failed = True
        cog = self.cog
        try:
            coro = self.on_error
        except AttributeError:
            pass
        else:
            injected = wrap_callback(coro)
            if cog is not None:
                await injected(cog, ctx, error)
            else:
                await injected(ctx, error)

        try:
            if cog is not None:
                local = Cog._get_overridden_method(cog.cog_command_error)
                if local is not None:
                    wrapped = wrap_callback(local)
                    await wrapped(ctx, error)
        finally:
            ctx.bot.dispatch('command_error', ctx, error)

    def before_invoke(self, coro: HookT) -> HookT:
        """A decorator that registers a coroutine as a pre-invoke hook.

        A pre-invoke hook is called directly before the command is
        called. This makes it a useful function to set up database
        connections or any type of set up required.

        This pre-invoke hook takes a sole parameter, a :class:`.Context`.

        See :meth:`.Bot.before_invoke` for more info.

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

    def after_invoke(self, coro: HookT) -> HookT:
        """A decorator that registers a coroutine as a post-invoke hook.

        A post-invoke hook is called directly after the command is
        called. This makes it a useful function to clean-up database
        connections or any type of clean up required.

        This post-invoke hook takes a sole parameter, a :class:`.Context`.

        See :meth:`.Bot.after_invoke` for more info.

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

    @property
    def clean_params(self) -> Dict[str, inspect.Parameter]:
        """Dict[:class:`str`, :class:`inspect.Parameter`]:
        Retrieves the parameter dictionary without the context or self parameters.

        Useful for inspecting signature.
        """
        result = self.params.copy()
        if self.cog is not None:
            # first parameter is self
            try:
                del result[next(iter(result))]
            except StopIteration:
                raise ValueError("missing 'self' parameter") from None

        try:
            # first/second parameter is context
            del result[next(iter(result))]
        except StopIteration:
            raise ValueError("missing 'context' parameter") from None

        return result

    async def call_before_hooks(self, ctx: ContextBase) -> None:
        # now that we're done preparing we can call the pre-command hooks
        # first, call the command local hook:
        cog = self.cog
        if self._before_invoke is not None:
            # should be cog if @commands.before_invoke is used
            instance = getattr(self._before_invoke, '__self__', cog)
            # __self__ only exists for methods, not functions
            # however, if @command.before_invoke is used, it will be a function
            if instance:
                await self._before_invoke(instance, ctx)  # type: ignore
            else:
                await self._before_invoke(ctx)  # type: ignore

        # call the cog local hook if applicable:
        if cog is not None:
            hook = Cog._get_overridden_method(cog.cog_before_invoke)
            if hook is not None:
                await hook(ctx)

        # call the bot global hook if necessary
        hook = ctx.bot._before_invoke
        if hook is not None:
            await hook(ctx)

    async def call_after_hooks(self, ctx: ContextBase) -> None:
        cog = self.cog
        if self._after_invoke is not None:
            instance = getattr(self._after_invoke, '__self__', cog)
            if instance:
                await self._after_invoke(instance, ctx)  # type: ignore
            else:
                await self._after_invoke(ctx)  # type: ignore

        # call the cog local hook if applicable:
        if cog is not None:
            hook = Cog._get_overridden_method(cog.cog_after_invoke)
            if hook is not None:
                await hook(ctx)

        hook = ctx.bot._after_invoke
        if hook is not None:
            await hook(ctx)

    def __str__(self) -> str:
        return self.name

    async def _prepare_cooldowns(self, ctx: ContextBase) -> None:
        if self._buckets.valid:
            dt = ctx.invoked_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            bucket = self._buckets.get_bucket(ctx, current)
            if bucket is not None:
                retry_after = bucket.update_rate_limit(current)
                if retry_after:
                    raise CommandOnCooldown(bucket, retry_after, self._buckets.type)

    async def prepare(self, ctx: ContextBase) -> None:
        ctx.command = self

        if not await self.can_run(ctx):
            raise CheckFailure(f'The check functions for command {str(self)} failed.')

        if self._max_concurrency is not None:
            await self._max_concurrency.acquire(ctx)

        try:
            await self._prepare_cooldowns(ctx)
            await self.call_before_hooks(ctx)
        except:
            if self._max_concurrency is not None:
                await self._max_concurrency.release(ctx)
            raise

    def is_on_cooldown(self, ctx: ContextBase) -> bool:
        """Checks whether the command is currently on cooldown.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to use when checking the commands cooldown status.

        Returns
        --------
        :class:`bool`
            A boolean indicating if the command is on cooldown.
        """
        if not self._buckets.valid:
            return False

        bucket = self._buckets.get_bucket(ctx)
        dt = ctx.invoked_at
        current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
        return bucket.get_tokens(current) == 0

    def reset_cooldown(self, ctx: ContextBase) -> None:
        """Resets the cooldown on this command.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to reset the cooldown under.
        """
        if self._buckets.valid:
            bucket = self._buckets.get_bucket(ctx)
            bucket.reset()

    def get_cooldown_retry_after(self, ctx: ContextBase) -> float:
        """Retrieves the amount of seconds before this command can be tried again.

        .. versionadded:: 1.4

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to retrieve the cooldown from.

        Returns
        --------
        :class:`float`
            The amount of time left on this command's cooldown in seconds.
            If this is ``0.0`` then the command isn't on cooldown.
        """
        if self._buckets.valid:
            bucket = self._buckets.get_bucket(ctx)
            dt = ctx.invoked_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            return bucket.get_retry_after(current)

        return 0.0

    async def invoke(self, ctx: ContextBase) -> None:
        await self.prepare(ctx)

        # terminate the invoked_subcommand chain.
        # since we're in a regular command (and not a group) then
        # the invoked subcommand is None.
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = hooked_wrapped_callback(self, ctx, self.callback)
        await injected(*ctx.args, **ctx.kwargs)

    async def reinvoke(self, ctx: ContextBase, *, call_hooks: bool = False) -> None:
        ctx.command = self

        if call_hooks:
            await self.call_before_hooks(ctx)

        ctx.invoked_subcommand = None
        try:
            await self.callback(*ctx.args, **ctx.kwargs)  # type: ignore
        except:
            ctx.command_failed = True
            raise
        finally:
            if call_hooks:
                await self.call_after_hooks(ctx)

    def error(self, coro: ErrorT) -> ErrorT:
        """A decorator that registers a coroutine as a local error handler.

        A local error handler is an :func:`.on_command_error` event limited to
        a single command. However, the :func:`.on_command_error` is still
        invoked afterwards as the catch-all.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the local error handler.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler must be a coroutine.')

        self.on_error: Error = coro
        return coro

    def has_error_handler(self) -> bool:
        """:class:`bool`: Checks whether the command has an error handler registered.

        .. versionadded:: 1.7
        """
        return hasattr(self, 'on_error')

    @property
    def cog_name(self) -> Optional[str]:
        """Optional[:class:`str`]: The name of the cog this command belongs to, if any."""
        return type(self.cog).__cog_name__ if self.cog is not None else None

    @property
    def short_doc(self) -> str:
        """:class:`str`: Gets the "short" documentation of a command.

        By default, this is the :attr:`.brief` attribute.
        If that lookup leads to an empty string then the first line of the
        :attr:`.help` attribute is used instead.
        """
        if self.brief is not None:
            return self.brief
        if self.help is not None:
            return self.help.split('\n', 1)[0]
        return ''

    async def can_run(self, ctx: ContextBase) -> bool:
        """|coro|

        Checks if the command can be executed by checking all the predicates
        inside the :attr:`~Command.checks` attribute. This also checks whether the
        command is disabled.

        .. versionchanged:: 1.3
            Checks whether the command is disabled or not

        Parameters
        -----------
        ctx: :class:`.Context`
            The ctx of the command currently being invoked.

        Raises
        -------
        :class:`CommandError`
            Any command error that was raised during a check call will be propagated
            by this function.

        Returns
        --------
        :class:`bool`
            A boolean indicating if the command can be invoked.
        """

        if not self.enabled:
            raise DisabledCommand(f'{self.name} command is disabled')

        original = ctx.command
        ctx.command = self

        try:
            if not await ctx.bot.can_run(ctx):
                raise CheckFailure(
                    f'The global check functions for command {self.qualified_name} failed.')

            cog = self.cog
            if cog is not None:
                local_check = Cog._get_overridden_method(cog.cog_check)
                if local_check is not None:
                    ret = await nextcord.utils.maybe_coroutine(local_check, ctx)
                    if not ret:
                        return False

            predicates = self.checks
            if not predicates:
                # since we have no checks, then we just return True.
                return True

            return await nextcord.utils.async_all(predicate(ctx) for predicate in predicates) # type: ignore
        finally:
            ctx.command = original


def unwrap_function(function: Callable[..., Any]) -> Callable[..., Any]:
    partial = functools.partial
    while True:
        if hasattr(function, '__wrapped__'):
            function = function.__wrapped__ # type: ignore
        elif isinstance(function, partial):
            function = function.func
        else:
            return function


def get_signature_parameters(function: Callable[..., Any], globalns: Dict[str, Any]) -> Dict[str, inspect.Parameter]:
    signature = inspect.signature(function)
    params = {}
    cache: Dict[str, Any] = {}
    eval_annotation = nextcord.utils.evaluate_annotation
    for name, parameter in signature.parameters.items():
        annotation = parameter.annotation
        if annotation is parameter.empty:
            params[name] = parameter
            continue
        if annotation is None:
            params[name] = parameter.replace(annotation=type(None))
            continue

        annotation = eval_annotation(annotation, globalns, globalns, cache)
        if annotation is Greedy:
            raise TypeError(
                'Unparameterized Greedy[...] is disallowed in signature.')

        params[name] = parameter.replace(annotation=annotation)

    return params


def wrap_callback(coro):
    @functools.wraps(coro)
    async def wrapped(*args, **kwargs):
        try:
            ret = await coro(*args, **kwargs)
        except CommandError:
            raise
        except asyncio.CancelledError:
            return
        except Exception as exc:
            raise CommandInvokeError(exc) from exc
        return ret
    return wrapped


def hooked_wrapped_callback(command, ctx, coro):
    @functools.wraps(coro)
    async def wrapped(*args, **kwargs):
        try:
            ret = await coro(*args, **kwargs)
        except CommandError:
            ctx.command_failed = True
            raise
        except asyncio.CancelledError:
            ctx.command_failed = True
            return
        except Exception as exc:
            ctx.command_failed = True
            raise CommandInvokeError(exc) from exc
        finally:
            if command._max_concurrency is not None:
                await command._max_concurrency.release(ctx)

            await command.call_after_hooks(ctx)
        return ret
    return wrapped