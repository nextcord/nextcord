:orphan:

.. currentmodule:: nextcord

.. _client_index:
   
Interaction Commands
======================

Since Discord has added interaction commands a feature with many possibilities, we at Nextcord have decided to add them to our fleet of features.

This doc will explain the innerworkings and how to use interaction commmands.

We suggest you learn how to make regular commands before looking through here, we suggest looking at the :doc:`quickstart`

How To Make A Simple Interaction Command
------------------------------------------

This right here is a simple ping pong command made with Nextcords slash feature.

.. code-block:: python3

    @bot.slash_command(name="ping")
    async def ping(interaction):
        await interaction.response.send_message("Pong!")
        
The way it works is that you use the :meth:`~Client.slash_command` function to interact with the Discord API. The ``name`` parameter is the name of your slash command.

``guild_ids`` is used to limit the guilds that the slash command is available to. This is also useful for testing, as global slash commands can take up to an hour to register.

Example:

.. code-block:: python3
      
    @bot.slash_command(guild_ids=[id1, id2])

How To Use Sub-Commands
-------------------------

The way sub-commands work is that you make a normal slash command that will never be called, and then make the sub-commands and have them do the work of real slash commands. There is no difference with slash commands and sub-commands. The only thing you will need to change is functions.

As shown in the demonstration below you make a main slash command or a dummy slash command and build sub-commands off it.

.. code-block:: python3

    @bot.slash_command()
    async def main(interaction):
        await interaction.response.send_message("This will never get called if this has subcommands.")


    @main.subcommand()
    async def sub1(interaction):
        await interaction.response.send_message("This is subcommand 1!")


    @main.subcommand(name="sub2", description="Sub2s Description")
    async def subcommand_two(
                            interaction: Interaction,
                            arg1: str = SlashOption(name="argument1", description="The first argument."),
                            arg2: str = SlashOption(description="The second argument!", default=None)
                              ):
        await interaction.response.send_message(f"This is subcommand 2 with arg1 {arg1} and arg2 {arg2}")
        
Fields And Requirements
------------------------
Fields are meant to facilitate an easier way to fill info, letting people using your slash command get a different response for each answer.

Nextcord's implementation of slash commands has fields and is very simple. in the example below is a field.

.. code-block:: python3
     
     @bot.slash_command(name="help")
     async def help(
         interaction: Interaction,
         setting: str = SlashOption(name="settings", description="Configure Your Settings")
     ):
         if setting == "music":
             await interaction.response.send_message(f"MOOSIC")
         elif setting == "moderation":
             await interaction.response.send_message(f"Mods party? POOG")
         else:
             await interaction.response.send_message("Odd, I don't know that setting")


How To Make Slash Commands In Cogs
-----------------------------------
Show below is an example of a simple command running in a cog.

.. code-block:: python3
      
    class ExampleCog(commands.Cog):
        def __init__(self):
            self.count = 0

        @slash_command(name="cogexample")
        async def slash_example_cog_command(self, interaction):
            await interaction.response.send_message("Hello i am a slash command in a cog!")


bot.add_cog(ExampleCog())

The example shown above responds to a user when they do a slash command. It is identical to a normal slash command and to normal commands in general.

How To Make Application Commands
------------------------------------
Application commands display commands on a menu of a message/user.

User Commands
~~~~~~~~~~~~~~
What you see below is a example of a simple user command.
It is a user dump command that dumps user data.

.. code-block:: python3

    @bot.user_command(name="dump")
    async def userdump(interaction, member):
        await interaction.response.send_message(f"Member: {member}, Data Dump: {interaction.data}")

Message Commands
~~~~~~~~~~~~~~~~~
What you see below is a example of a simple message command, 
It's a message dump command that dumps message data.

.. code-block:: python3

    @bot.message_command(name="dump")
    async def messagedump(interaction, message: Message):
        await interaction.response.send_message(f"Data Dump: {interaction.data}")
        
