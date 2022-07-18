.. currentmodule:: nextcord

.. _ext_commands_cogs:

Cogs
======

:class:`~.commands.Cog` is like :class:`~.Cog` except it adds support for :class:`~.commands.Command`
and more special methods.

It should be noted that cogs are typically used alongside with :ref:`ext_commands_extensions`.

Quick Example
---------------

This example cog defines a ``Greetings`` category for your commands, with a single :ref:`command <ext_commands_commands>` named ``hello`` as well as a listener to listen to an :ref:`Event <discord-api-events>`.

.. code-block:: python3

    class Greetings(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
            self._last_member = None

        @commands.Cog.listener()
        async def on_member_join(self, member):
            channel = member.guild.system_channel
            if channel is not None:
                await channel.send(f'Welcome {member.mention}.')

        @commands.command()
        async def hello(self, ctx, *, member: nextcord.Member = None):
            """Says hello"""
            member = member or ctx.author
            if self._last_member is None or self._last_member.id != member.id:
                await ctx.send(f'Hello {member.name}~')
            else:
                await ctx.send(f'Hello {member.name}... This feels familiar.')
            self._last_member = member

.. _ext_commands_cogs_special_methods:

Special Methods
-----------------

As cogs get more complicated and have more commands, there comes a point where we want to customise the behaviour of the entire cog or bot.

They are as follows:

- :meth:`.Cog.cog_unload`
- :meth:`.Cog.cog_check`
- :meth:`.Cog.cog_command_error`
- :meth:`.Cog.cog_before_invoke`
- :meth:`.Cog.cog_after_invoke`
- :meth:`.Cog.bot_check`
- :meth:`.Cog.bot_check_once`

You can visit the reference to get more detail and see additional special methods in :ref:`cog`.

Inspection
------------

Since cogs ultimately are classes, we have some tools to help us inspect certain properties of the cog.


To get a :class:`list` of commands, we can use :meth:`.Cog.get_commands`. ::

    >>> cog = bot.get_cog('Greetings')
    >>> commands = cog.get_commands()
    >>> print([c.name for c in commands])

If we want to get the subcommands as well, we can use the :meth:`.Cog.walk_commands` generator. ::

    >>> print([c.qualified_name for c in cog.walk_commands()])
