:orphan:

.. currentmodule:: nextcord

.. _interactions:
   
Slash Commands
==============

Since Discord has added interaction commands a feature with many possibilities, we at Nextcord have decided to add them to our fleet of features.

This doc will explain the innerworkings and how to use interaction commmands.

We suggest you learn how to make regular commands before looking through here, we suggest looking at the :doc:`quickstart`

How To Make A Simple Slash Command
----------------------------------

This right here is a simple ping pong command made with Nextcord's slash feature.

.. code-block:: python3

    @client.slash_command()
    async def ping(interaction):
        await interaction.response.send_message("Pong!")
        
The way it works is that you use the :meth:`~Client.slash_command` function to interact with discord's application commands endpoint.

``guild_ids`` is used to limit the guilds that the slash command is available to. This is also useful for testing, as global slash commands can take up to an hour to register.

Example:

.. code-block:: python3
      
    @client.slash_command(guild_ids=[id1, id2])

How To Use Sub-Commands
-----------------------

The way sub-commands work is that you make a normal slash command that will never be called, and then make the sub-commands and have them do the work of real slash commands. There is no difference with slash commands and sub-commands. The only thing you will need to change is functions.

As shown in the demonstration below you make a main slash command or a dummy slash command and build sub-commands off it.

.. code-block:: python3

        @client.slash_command(guild_ids=[...])  # Making the command and limiting the guilds
        async def my_main_command(interaction):  
            await interaction.response.send_message(
            "This will never get called if this has subcommands."
                )  # a function never called


        @my_main_command.subcommand()  # Identifying The Sub-Command
        async def subcommand_one(interaction):  # Making The Sub Command Name And Passing Through Interaction
        await interaction.response.send_message(
            "This is subcommand 1!"
            )  # Sending A Response


        # Identifying The Sub-Command And Adding A Descripton
        @my_main_command.subcommand(description="Aha! Another subcommand")  
        async def subcommand_two(interaction: Interaction):  # Passing in interaction

        await interaction.response.send_message(
            "This is subcommand 2!"
            )       # Responding With The Args/Fields
        
Fields And Requirements
-----------------------
Fields are meant to facilitate an easier way to fill info, letting people using your slash command get a different response for each answer.

Nextcord's implementation of slash commands has fields and is very simple. in the example below is a field.

.. code-block:: python3
     
     @client.slash_command()
     async def help(
         interaction: Interaction,
         setting: str = SlashOption(name="settings", description="Configure Your Settings")
     ):
         if setting == "music":
             await interaction.response.send_message("Sorry we don't have PyNaCl installed currently")
         elif setting == "moderation":
             await interaction.response.send_message("Moderation?")
         else:
             await interaction.response.send_message("Odd, I don't know that setting")


How To Make Slash Commands In Cogs
----------------------------------
Show below is an example of a simple command running in a cog.

.. code-block:: python3

    class ExampleCog(commands.Cog):
        def __init__(self):
            self.count = 0

        @nextcord.slash_command()
        async def slash_example_cog_command(self, interaction):
            await interaction.response.send_message("Hello i am a slash command in a cog!")

The example shown above responds to a user when they do a slash command. It is identical to a normal slash command and to normal commands in general.

How To Make Context Menu Commands
---------------------------------
Context Menu commands display commands on a menu of a message/user.

User Commands
~~~~~~~~~~~~~~
What we show below just dumps the user's username but should be enough to get the point.

.. code-block:: python3

    @client.user_command()
    async def hello(interaction, member):
        await interaction.response.send_message(f"Hello! {member}")

Message Commands
~~~~~~~~~~~~~~~~~
Below is a simple example of message command that says the message given.

.. code-block:: python3

    @client.message_command()
    async def say(interaction, message: Message):
        await interaction.response.send_message(f"{message}")
        
