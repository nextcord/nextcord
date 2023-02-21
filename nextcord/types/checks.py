# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any, Callable, Coroutine, TypeVar, Union

if TYPE_CHECKING:
    from nextcord.cog import Cog

    from ..interactions import Interaction

    T = TypeVar("T")

    Coro = Coroutine[Any, Any, T]
    MaybeCoro = Union[T, Coro[T]]
    CoroFunc = Callable[..., Coro[Any]]
    ApplicationCheck = Union[
        Callable[[Cog, Interaction], MaybeCoro[bool]], Callable[[Interaction], MaybeCoro[bool]]
    ]
    ApplicationHook = Union[
        Callable[[Cog, Interaction], Coro[Any]], Callable[[Interaction], Coro[Any]]
    ]
    ApplicationErrorCallback = Union[
        Callable[[Cog, Interaction, Exception], Coro[Any]],
        Callable[[Interaction, Exception], Coro[Any]],
    ]
