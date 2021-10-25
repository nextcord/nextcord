import inspect
import copy
import typing

from nextcord.ext.commands import GroupMixin, Command, Group

from .model import ConverterDict

__all__ = (
    'ConvertersCommand',
    'ConvertersGroupMixin',
    'ConvertersGroup',
    'command',
    'group',
)

class ConvertersCommand(Command):
    converters: ConverterDict

    async def _actual_conversion(self, ctx, converter, argument, param):
        converter = self.converters.get(converter, converter)
        return await super()._actual_conversion(ctx, converter, argument, param)

T = ConvertersCommand

class ConvertersGroupMixin(GroupMixin):
    converters = ConverterDict()

    # redefine GroupMixin#command and GroupMixin#group to work with redefined decorators
    def command(self, *args, **kwargs) -> typing.Callable[..., T]:
        def decorator(func: typing.Callable[..., typing.Any]) -> T:
            kwargs.setdefault('parent', self)
            result = command(*args, **kwargs)(func)
            result.converters = copy.copy(self.converters)
            self.add_command(result)
            return result
        
        return decorator
    
    def group(self, *args, **kwargs) -> typing.Callable[..., T]:
        def decorator(func: typing.Callable[..., typing.Any]) -> T:
            kwargs.setdefault('parent', self)
            result = group(*args, **kwargs)(func)
            result.converters.update(copy.copy(self.converters))
            self.add_command(result)
            return result

        return decorator


class ConvertersGroup(ConvertersGroupMixin, ConvertersCommand):
    ...

def command(name: typing.Optional[str] = None, cls: typing.Optional[typing.Type[T]] = None, **attrs: typing.Any) -> typing.Callable[..., T]:
    if cls is None:
        cls = ConvertersCommand

    def decorator(func: typing.Callable[..., typing.Any]) -> T:
        if isinstance(func, ConvertersCommand):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator

def group(name: typing.Optional[str] = None, **attrs: typing.Any) -> typing.Callable[..., typing.Union[ConvertersGroup, T]]:
    """A decorator that transforms a function into a :class:`.Group`.

    This is similar to the :func:`.command` decorator but the ``cls``
    parameter is set to :class:`Group` by default.

    .. versionchanged:: 1.1
        The ``cls`` parameter can now be passed.
    """

    attrs.setdefault('cls', ConvertersGroup)
    return command(name=name, **attrs)
