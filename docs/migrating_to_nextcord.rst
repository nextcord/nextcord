.. currentmodule:: nextcord

.. _migrating_nextcord:

Migrating to nextcord
======================

Due to the `original discord.py repository <https://github.com/Rapptz/discord.py>`_ becoming read-only, we decided
that it would be necessary to fork it and keep on developing further. We also wanted to change the name and voted on
nextcord in order to properly register it at pypi.

Porting from discord.py
-------------------------

In order to port a bot using discord.py to nextcord.py, follow these steps:

1. Install nextcord: 

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U nextcord

    # Windows
    py -3 -m pip install -U nextcord

2. Update the following import statements:

* ``import discord`` -> ``import nextcord as discord``
* ``from discord.ext`` -> ``from nextcord.ext``

Code Example
--------------

.. code:: py

    #Previously: import discord
    from nextcord import discord

    #Previously: from discord.ext import commands
    from nextcord.ext import commands

    bot = commands.Bot(command_prefix='$')

    @bot.command()
    async def ping(ctx):
        embed=discord.Embed(
            title="Pong!",
            colour=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    bot.run('[Bot Token]')