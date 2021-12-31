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
import asyncio
import functools
from typing import (
    Any,
    Callable,
    Union,
    Coroutine,
    TypeVar,
    TYPE_CHECKING
)

from .application_command import ApplicationSubcommand, Interaction

if TYPE_CHECKING:
    from .application_command import ClientCog


__all__ = (
    "check"
)


T = TypeVar('T')

Coro = Coroutine[Any, Any, T]
MaybeCoro = Union[T, Coro[T]]
CoroFunc = Callable[..., Coro[Any]]
ApplicationCheck = Union[Callable[["ClientCog", Interaction], MaybeCoro[bool]], Callable[[Interaction], MaybeCoro[bool]]]

def check(predicate: ApplicationCheck) -> Callable[[T], T]:
    r"""A decorator that adds a check to the :class:`ApplicationSubcommand` or its
    subclasses. These checks could be accessed via :attr:`ApplicationSubcommand.checks`.
    These checks should be predicates that take in a single parameter taking
    a :class:`.Interaction`. If the check returns a ``False``\-like value then
    during invocation a :exc:`ApplicationCheckFailure` exception is raised and sent to
    the :func:`.on_command_error` event.
    If an exception should be thrown in the predicate then it should be a
    subclass of :exc:`.ApplicationCommandError`. Any exception not subclassed from it
    will be propagated while those subclassed will be sent to
    :func:`.on_application_command_error`.
    """

    def decorator(func: Union[ApplicationSubcommand, CoroFunc]) -> Union[ApplicationSubcommand, CoroFunc]:
        if isinstance(func, ApplicationSubcommand):
            func.checks.insert(0, predicate)
        else:
            if not hasattr(func, '__slash_command_checks__'):
                func.__slash_command_checks__ = []

            func.__slash_command_checks__.append(predicate)

        return func

    if asyncio.iscoroutinefunction(predicate):
        decorator.predicate = predicate
    else:
        @functools.wraps(predicate)
        async def wrapper(ctx):
            return predicate(ctx)
        decorator.predicate = wrapper

    return decorator