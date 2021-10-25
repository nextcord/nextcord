"""**STANDALONE**: An experiment that allows the use of classes and
functions as a way to represent a group of commands.

Example:
```py
@bot.group(cls=ClassGroup)
class A(Config, invoke_without_command=True): # A group command
    _CONFIG = Config(invoke_without_command=True, description='no')

    async def __call__(ctx):
        await ctx.send('test')
    
    async def fmt(ctx): # A command
        await ctx.send('toot')
    
    class B: # A group command
        #_CONFIG = Config(description='yes')

        async def __call__(ctx):
            await ctx.send('no')

        async def oops(ctx): # A command
            await ctx.send('yert')
```

```
!A -> 'test'
!A fmt -> 'toot'
!A B -> 'no'
!A B oops -> 'no', 'yert'
```
"""

import inspect

from nextcord.ext import commands


class ClassGroup(commands.Group):
    def __init__(self, cls, *, name=None, parent=None):
        kwargs = {"name": name or cls.__name__, "parent": parent}
        func = cls.__call__

        try:
            cls._CONFIG
        except AttributeError:
            pass
        else:
            kwargs.update(cls._CONFIG.to_dict())

        super().__init__(func, **kwargs)

        for f in dir(cls):
            if f.startswith("_"):
                continue

            attr = getattr(cls, f)

            if inspect.isclass(attr):
                self.add_command(ClassGroup(attr, parent=self))
            elif inspect.iscoroutinefunction(attr):
                self.add_command(commands.Command(attr))


class Config:
    def __init__(
        self,
        *,
        invoke_without_command: bool = False,
        case_insensitive: bool = False,
        help: str = "",
        brief: str = "",
        usage: str = "",
        aliases: list = [],
        checks: list = [],
        description: str = "",
        hidden: bool = False,
    ):
        self.invoke_without_command = invoke_without_command
        self.case_insensitive = case_insensitive
        self.help = help
        self.brief = brief
        self.usage = usage
        self.aliases = aliases
        self.checks = checks
        self.description = description
        self.hidden = hidden

    def to_dict(self):
        d = {}
        for attr in dir(self):
            if not attr.startswith("_"):
                d[attr] = getattr(self, attr)

        return d
