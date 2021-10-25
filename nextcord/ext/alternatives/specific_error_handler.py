"""An experiment that allows handlers to handle specific errors.

This overrides the default behaviour of ``Command.error``.
(Change ``@Command.error`` to ``@Command.error()``).

Example:
```py
@bot.command()
async def throw_error(ctx):
    raise Exception

@command.error(CommandInvokeError)
async def handle(ctx, error):
    if isinstance(error.original, Exception):
        await ctx.send('oh no')
```
"""

import asyncio

from nextcord.ext import commands


async def on_error(*args):  # cog?, ctx, error
    error, ctx = args[-1], args[-2]
    cls = error.__class__

    for exc, callback in ctx.command._handled_errors.items():
        if exc in cls.__mro__:  # walk mro to check if the handler can handle it
            await callback(*args)


def error(self, *exceptions):
    def decorator(func):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("The error must be a coroutine.")

        if not exceptions:
            self.on_error = func
            return

        try:
            self._handled_errors
        except AttributeError:
            self._handled_errors = {}
        finally:
            for exc in exceptions:
                self._handled_errors[exc] = func

        try:
            self.on_error
        except AttributeError as e:
            self.on_error = on_error

        return func

    return decorator


commands.Command.error = error

_old_ensure_assignment_on_copy = commands.Command._ensure_assignment_on_copy


def _ensure_assignment_on_copy(self, other):
    other = _old_ensure_assignment_on_copy(self, other)

    try:
        other._handled_errors = self._handled_errors
    except AttributeError:
        pass

    return other


commands.Command._ensure_assignment_on_copy = _ensure_assignment_on_copy
