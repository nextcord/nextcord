from typing_extensions import Concatenate, ParamSpec
from typing import TYPE_CHECKING, Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union
from ._types import CogT, CommandT, ContextT, Coro, Check, Hook, HookT
from .context_base import ContextBase
from nextcord.ext.interactions import CooldownMapping, BucketType, MaxConcurrency, Cog
from nextcord.ext.converters import Greedy
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

        self.cooldown_after_parsing: bool = kwargs.get(
            'cooldown_after_parsing', False)
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

    async def dispatch_error(self, ctx: Context, error: Exception) -> None:
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

    async def transform(self, ctx: ContextBase, param: inspect.Parameter) -> Any:
        """TODO: Check what is necessary for base and what should only be done in logacy command"""
        required = param.default is param.empty
        converter = get_converter(param)
        consume_rest_is_special = param.kind == param.KEYWORD_ONLY and not self.rest_is_raw
        view = ctx.view
        view.skip_ws()

        # The greedy converter is simple -- it keeps going until it fails in which case,
        # it undos the view ready for the next parameter to use instead
        if isinstance(converter, Greedy):
            if param.kind in (param.POSITIONAL_OR_KEYWORD, param.POSITIONAL_ONLY):
                return await self._transform_greedy_pos(ctx, param, required, converter.converter)
            elif param.kind == param.VAR_POSITIONAL:
                return await self._transform_greedy_var_pos(ctx, param, converter.converter)
            else:
                # if we're here, then it's a KEYWORD_ONLY param type
                # since this is mostly useless, we'll helpfully transform Greedy[X]
                # into just X and do the parsing that way.
                converter = converter.converter

        if view.eof:
            if param.kind == param.VAR_POSITIONAL:
                raise RuntimeError()  # break the loop
            if required:
                if self._is_typing_optional(param.annotation):
                    return None
                if hasattr(converter, '__commands_is_flag__') and converter._can_be_constructible():
                    return await converter._construct_default(ctx)
                raise MissingRequiredArgument(param)
            return param.default

        previous = view.index
        if consume_rest_is_special:
            argument = view.read_rest().strip()
        else:
            try:
                argument = view.get_quoted_word()
            except ArgumentParsingError as exc:
                if self._is_typing_optional(param.annotation):
                    view.index = previous
                    return None
                else:
                    raise exc
        view.previous = previous

        # type-checker fails to narrow argument
        # type: ignore
        return await run_converters(ctx, converter, argument, param)




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