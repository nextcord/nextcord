"""An experiment that allows you to handle all exceptions of
group commands in the error handler of the root parent.

Example:
```py
@bot.group()
async def profile(ctx):
    pass

@profile.error
async def profile_error(ctx, error):
    if isinstance(error.original, Exception):
        await ctx.send("You have not created your profile yet. Use ;profile create command now to create your profile.")

@profile.command()
async def name(ctx):
    raise Exception

@profile.command()
async def color(ctx):
    raise Exception
```
"""

from nextcord.ext import commands


async def dispatch_error(self, ctx, error):
    ctx.command_failed = True
    cog = self.cog

    try:
        coro = self.on_error
    except AttributeError:
        pass
    else:
        injected = commands.core.wrap_callback(coro)

        if cog is not None:
            await injected(cog, ctx, error)
        else:
            await injected(ctx, error)

    try:
        coro = self.root_parent.on_error
    except AttributeError:
        pass
    else:
        injected = commands.core.wrap_callback(coro)

        if cog is not None:
            await injected(cog, ctx, error)
        else:
            await injected(ctx, error)

    try:
        if cog is not None:
            local = commands.Cog._get_overridden_method(cog.cog_command_error)
            if local is not None:
                wrapped = commands.core.wrap_callback(local)
                await wrapped(ctx, error)
    finally:
        ctx.bot.dispatch("command_error", ctx, error)


commands.Command.dispatch_error = dispatch_error
