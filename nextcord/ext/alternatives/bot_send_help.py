"""An experiment that allows you to send help without requiring ``Context``,
or inside of ``on_message``.

Example:
```py
@bot.event
async def on_message(message):
    if message.content == message.guild.me.mention:
        await bot.send_help(message) # sends the entire help command.
```
"""

from nextcord.ext import commands


def send_help(self, message, *args, **kwargs):
    ctx = kwargs.get("cls", commands.Context)(prefix=self.user.mention, bot=self, message=message)
    return ctx.send_help(*args)


commands.bot.BotBase.send_help = send_help
