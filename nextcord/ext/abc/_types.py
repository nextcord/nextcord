"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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


from typing import Any, Callable, Coroutine, TYPE_CHECKING, TypeVar, Union


if TYPE_CHECKING:
    from nextcord.ext.interactions.cog import Cog
    from nextcord.ext.errors import CommandError
    from .context_base import ContextBase
    from .command_base import CommandBase

T = TypeVar('T')

Coro = Coroutine[Any, Any, T]
MaybeCoro = Union[T, Coro[T]]
CoroFunc = Callable[..., Coro[Any]]

Check = Union[Callable[["Cog", "ContextBase[Any]"], MaybeCoro[bool]],
              Callable[["ContextBase[Any]"], MaybeCoro[bool]]]
Hook = Union[Callable[["Cog", "ContextBase[Any]"], Coro[Any]],
             Callable[["ContextBase[Any]"], Coro[Any]]]
Error = Union[Callable[["Cog", "ContextBase[Any]", "CommandError"],
                       Coro[Any]], Callable[["ContextBase[Any]", "CommandError"], Coro[Any]]]

CogT = TypeVar('CogT', bound='Cog')
CommandT = TypeVar('CommandT', bound='CommandBase')
ContextT = TypeVar('ContextT', bound='ContextBase')
CoroFuncT = TypeVar('CoroFuncT', bound='CoroFunc')
HookT = TypeVar('HookT', bound='Hook')
ErrorT = TypeVar('ErrorT', bound='Error')
