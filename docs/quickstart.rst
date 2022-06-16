:orphan:

.. _quickstart:

.. currentmodule:: nextcord

Quickstart
==========

This page gives a brief introduction to the library. It assumes you have the library installed,
if you don't check the :ref:`installing` portion.

A Minimal Bot
-------------

Let's make a bot that responds to a slash command and walk you through it.

It looks something like this:

.. code-block:: python3

    import nextcord
    from nextcord.ext import commands

    TESTING_GUILD_ID = 123456789  # Replace with your guild ID

    bot = commands.Bot()

    @bot.event
    async def on_ready():
        print(f'We have logged in as {bot.user}')

    @bot.slash_command(description="My first slash command", guild_ids=[TESTING_GUILD_ID])
    async def hello(interaction: nextcord.Interaction):
        await interaction.send("Hello!")

    bot.run('your token here')

Let's name this file ``example_bot.py``. Make sure not to name it ``nextcord`` as that'll conflict
with the library.

A lot is going on here, so let's walk you through it step by step.

1. The first line just imports the library, if this raises a :exc:`ModuleNotFoundError` or :exc:`ImportError`
   then head on over to :ref:`installing` section to properly install.
2. The second line imports the :doc:`Bot commands framework <./ext/commands/index>` which allows us to use the
   :class:`~nextcord.ext.commands.Bot` class to create our bot.
3. After that, we will declare a constant called ``TESTING_GUILD_ID`` which will be used to identify the guild
   we want to use. This will allow us to test the command immediately in our server. Without this, we would have
   to wait up to an hour for the global command to register.
4. Next, we create an instance of a :class:`~nextcord.ext.commands.Bot`. This bot is our connection to Discord.
5. We then use the :meth:`bot.event <nextcord.ext.commands.Bot.event>` decorator to register an event. This library has many
   :ref:`events <discord-api-events>`. Since this library is asynchronous, we do things in a "callback" style manner.

   A callback is essentially a function that is called when something happens. In our case,
   the :func:`on_ready` event is called when the bot has finished logging in and setting things up.
6. Next, we use the :meth:`bot.slash_command <nextcord.ext.commands.Bot.slash_command>` decorator to register a slash command.
   This decorator can take arguments for configuring the slash commands such as the description and guild IDs where you want
   the command to be registered. The callback of the slash command takes in an :class:`~nextcord.Interaction` object as a
   parameter which can be used to respond to the user. In the callback, we use the method :meth:`Interaction.send` to reply.
7. Finally, we run the bot with our login token. If you need help getting your token or creating a bot,
   look in the :ref:`discord-intro` section.


Now that we've made a bot, we have to *run* the bot. Luckily, this is simple since this is just a
Python script, we can run it directly.

On Windows:

.. code-block:: shell

    $ py -3 example_bot.py

On other systems:

.. code-block:: shell

    $ python3 example_bot.py

Now you can try playing around with your basic bot.

You can find more examples in the `examples directory <https://github.com/nextcord/nextcord/blob/master/examples/>`_ on GitHub.
