.. currentmodule:: nextcord

.. _ext_slash_temp_cogs:

Slash Command Cogs
===================
Coming Soon As Slash Cogs Are Being Remade/Reworked

How To Make Slash Commands In Cogs
-----------------------------------
Show below is an example of a simple command running in a cog, It is very basic doesn't have alot of features, Some features planned is autocomplete and proper error handling to slash commands, So that mean's that slash cogs are gonna need to get a massive upgrade and will change alot, Since this is a very simple slash command cog it won't probably change just the more advanced features.
.. code-block:: python3
      class ExampleCog(commands.Cog):
      def __init__(self):
          self.count = 0

      @slash_command(name="cogexample", guild_ids=[755220989310140447])
      async def slash_example_cog_command(self, interaction):
          await interaction.response.send_message("Hi there from a cog!")

  bot.add_cog(ExampleCog())
  bot.run(TOKEN)

The example shown above responds to a user when they do a slash command, It is very identical to a normal slash command and to normal commands in general.

How To Use Advanced Cog Features
---------------------------------
Classes Etc
