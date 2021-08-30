
from typing_extensions import Concatenate
import nextcord
from typing import Callable, Type, Union

MISSING: Any = nextcord.utils.MISSING


def slash(
    name: str = MISSING,
    cls: Type[CommandT] = MISSING,
    **attrs: Any
) -> Callable[
        [
            Union[
                Callable[Concatenate[ContextT, P], Coro[Any]],
                Callable[Concatenate[CogT, ContextT, P], Coro[T]],
            ]
        ], Union[Command[CogT, P, T], CommandT]]:
    """A decorator that transforms a function into a :class:`.Command`
    or if called with :func:`.group`, :class:`.Group`.

    By default the ``help`` attribute is received automatically from the
    docstring of the function and is cleaned up with the use of
    ``inspect.cleandoc``. If the docstring is ``bytes``, then it is decoded
    into :class:`str` using utf-8 encoding.

    All checks added using the :func:`.check` & co. decorators are added into
    the function. There is no way to supply your own checks through this
    decorator.

    Parameters
    -----------
    name: :class:`str`
        The name to create the command with. By default this uses the
        function name unchanged.
    cls
        The class to construct with. By default this is :class:`.Command`.
        You usually do not change this.
    attrs
        Keyword arguments to pass into the construction of the class denoted
        by ``cls``.

    Raises
    -------
    TypeError
        If the function is not a coroutine or is already a command.
    """
    if cls is MISSING:
        cls = Command  # type: ignore

    def decorator(func: Union[
        Callable[Concatenate[ContextT, P], Coro[Any]],
        Callable[Concatenate[CogT, ContextT, P], Coro[Any]],
    ]) -> CommandT:
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator
