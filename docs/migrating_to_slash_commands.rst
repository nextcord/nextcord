:orphan:

.. _migrating_to_slash_commands:


Migrating To Slash Commands
=============================

Differences
-------------
One of the biggest difference's is the use of :class:`~nextcord.Interaction` instead of :class:`~nextcord.ext.commands.Context`

**NOTE:** It may take up to an hour for a slash command to register globally so we recommend you put guild_ids[] to limit the amount of guilds for testing 

Old Commands:

.. code-block:: python3
    
    @bot.command()
    async def example(ctx):
      await ctx.send("Hey!")
      
**This Way Is Deprecated For Slash Commands And CANT Be Used**

New Commands:

.. code-block:: python3
    
    @bot.slash_command()
    async def example(interaction):
      await interaction.response.send_message("Oye mate slash command here!")
      
**Note:** You have to respond to messages using response so discord counts it as responded to; And not say ``interaction failed`` to the user

For more info on interaction Look at the :doc:`api` Docs

Converting Normal Commands To Slash Commands
---------------------------------------------
* Step 1
    You're gonna want to replace ``command`` with ``slash_command``

* Step 2
    Replace :``ctx`` with ``interaction`` and replace any other next to ``ctx`` with ``interaction``
