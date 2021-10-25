"""An experiment that allows you to define commands in the bot subclass

Example:
```py
from nextcord.ext.alternatives import inline_bot_commands
from nextcord.ext import commands

class MyBot(commands.Bot):
    @commands.command()
    async def test(self, ctx):
        await ctx.send(f'{len(self.all_commands)} commands registered on {self.__class__.__name__}!')

    @commands.command()
    async def echo(self, ctx, *, words):
        await ctx.send(words)


bot = MyBot(command_prefix='?')
bot.run(token)
```
"""

from nextcord.ext import commands


class InlineMeta(type):
    def __new__(cls, *args, **kwargs):
        new_cls = super().__new__(cls, *args)
        cmds = {}
        for base in reversed(new_cls.__mro__):
            for elem, value in base.__dict__.items():
                if elem in cmds:
                    del cmds[elem]
                if isinstance(value, commands.Command):
                    cmds[elem] = value

        new_cls.__inline_commands__ = list(cmds.values())
        return new_cls

    @property
    def qualified_name(cls):
        # for the default help command, since the bot is acting as a cog
        return "No Category"


class BotBase(commands.bot.BotBase, metaclass=InlineMeta):
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)

        self.__inline_commands__ = tuple(c.copy() for c in cls.__inline_commands__)

        lookup = {cmd.qualified_name: cmd for cmd in self.__inline_commands__}

        # Update the Command instances dynamically as well
        for command in self.__inline_commands__:
            setattr(self, command.callback.__name__, command)
            command.cog = self
            parent = command.parent
            if parent is not None:
                # Get the latest parent reference
                parent = lookup[parent.qualified_name]

                # Update our parent's reference to our self
                parent.remove_command(command.name)
                parent.add_command(command)

        return self

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for command in self.__inline_commands__:
            self.add_command(command)


commands.bot.BotBase = BotBase
