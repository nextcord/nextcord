"""An experiment that allows you to set a command suffix on a Bot

Example:
```py
bot = commands.Bot(command_suffix='!', command_prefix='!')  # both the prefix and the suffix will work when invoking commands


@bot.command()
async def say(ctx, *, words):
    ret = 'You said \"{}\" with the {} `{}`!'

    if ctx.prefix is not None:
        ret = ret.format(words, 'prefix', ctx.prefix)
    else:
        ret = ret.format(words, 'suffix', ctx.prefix)

    await ctx.send(ret)


@bot.command()
async def ping(ctx):
    await ctx.send('Pong! {}ms'.format(ctx.bot.latency * 1000))


@bot.command()
async def hello(ctx):
    await ctx.send('Hello! I\'m a bot with command suffixes!')
```

'hello!' --> 'Hello! I'm a bot with command suffixes!'
'say! this is neat' --> 'You said "this is neat" with the suffix `!`'
'!say this is neat' --> 'You said "this is neat" with the prefix `!`'
'!say! this is neat' --> No reply
"""

import collections

import nextcord
from nextcord.ext import commands


def _suffix_used(suffix, content):
    space_index = content.find(" ")
    suffix_index = content.find(suffix)
    return suffix_index > 0 and (space_index == -1 or suffix_index < space_index)


class Context(commands.Context):
    def __init__(self, **attrs):
        super().__init__(**attrs)
        self.suffix = attrs.pop("suffix")

    @property
    def valid(self):
        return (self.suffix is not None or self.prefix is not None) and self.command is not None

    async def reinvoke(self, *, call_hooks=False, restart=True):
        if self.suffix is not None:
            # since the command was invoked with a suffix,
            # we need to make sure the view doesn't try to skip a nonexistent prefix
            original_prefix = self.prefix
            self.prefix = ""

        await super().reinvoke(call_hooks=call_hooks, restart=restart)

        try:
            self.prefix = original_prefix
        except NameError:
            pass


class BotBase(commands.bot.BotBase):
    def __init__(self, command_prefix=None, command_suffix=None, **options):
        if command_prefix is None and command_suffix is None:
            raise ValueError("Bot must have a prefix or suffix")

        super().__init__(command_prefix=command_prefix, **options)
        self.command_suffix = command_suffix

    async def get_prefix(self, message):
        if self.command_prefix is None:
            return None

        return await super().get_prefix(message)

    async def get_suffix(self, message):
        """|coro|
        Retrieves the prefix the bot is listening to
        with the message as a context.
        Parameters
        -----------
        message: :class:`nextcord.Message`
            The message context to get the prefix of.
        Returns
        --------
        Optional[Union[List[:class:`str`], :class:`str`]]
            A list of prefixes or a single prefix that the bot is
            listening for.
        """
        if self.command_suffix is None:
            return None

        suffix = ret = self.command_suffix
        if callable(suffix):
            ret = await nextcord.utils.maybe_coroutine(suffix, self, message)

        if not isinstance(ret, str):
            try:
                ret = list(ret)
            except TypeError:
                # It's possible that a generator raised this exception.  Don't
                # replace it with our own error if that's the case.
                if isinstance(ret, collections.abc.Iterable):
                    raise

                raise TypeError(
                    "command_suffix must be plain string, iterable of strings, or callable "
                    "returning either of these, not {}".format(ret.__class__.__name__)
                )

            if not ret:
                raise ValueError("Iterable command_prefix must contain at least one suffix")

        return ret

    async def get_context(self, message, *, cls=Context):
        """Defaults to check for prefix first."""
        view = commands.view.StringView(message.content)
        ctx = cls(prefix=None, suffix=None, view=view, bot=self, message=message)

        if self._skip_check(message.author.id, self.user.id):
            return ctx

        prefix = await self.get_prefix(message)
        suffix = await self.get_suffix(message)

        if prefix is not None:
            if isinstance(prefix, str):
                if view.skip_string(prefix):
                    invoked_prefix = prefix
            else:
                try:
                    if message.content.startswith(tuple(prefix)):
                        invoked_prefix = nextcord.utils.find(view.skip_string, prefix)
                except TypeError:
                    if not isinstance(prefix, list):
                        raise TypeError(
                            "get_prefix must return either a string or a list of string, "
                            "not {}".format(prefix.__class__.__name__)
                        )

                    for value in prefix:
                        if not isinstance(value, str):
                            raise TypeError(
                                "Iterable command_prefix or list returned from get_prefix must "
                                "contain only strings, not {}".format(value.__class__.__name__)
                            )

                    raise
        else:
            if isinstance(suffix, str):
                if _suffix_used(suffix, message.content):
                    invoked_suffix = suffix
                else:
                    return ctx
            else:
                try:
                    invoked_suffixes = [s for s in suffix if _suffix_used(s, message.content)]
                    if not invoked_suffixes:
                        return ctx

                    for suf in invoked_suffixes:
                        invoker = view.get_word()[: -len(suf)]
                        command = self.all_commands.get(invoker)
                        if command is not None:
                            view.undo()
                            invoked_suffix = suf
                            break
                    else:
                        return ctx

                except TypeError:
                    if not isinstance(suffix, list):
                        raise TypeError(
                            "get_suffix must return either a string or a list of string, "
                            "not {}".format(suffix.__class__.__name__)
                        )

                    for value in suffix:
                        if not isinstance(value, str):
                            raise TypeError(
                                "Iterable command_suffix or list returned from get_suffix must "
                                "contain only strings, not {}".format(value.__class__.__name__)
                            )

                    raise

        invoker = view.get_word()

        try:
            ctx.suffix = invoked_suffix
        except NameError:
            try:
                ctx.prefix = invoked_prefix
            except NameError:
                pass
        else:
            invoker = invoker[: -len(invoked_suffix)]

        ctx.invoked_with = invoker
        ctx.command = self.all_commands.get(invoker)
        return ctx


commands.bot.BotBase = BotBase
commands.Context = Context
