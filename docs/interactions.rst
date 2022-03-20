:orphan:

.. currentmodule:: nextcord

.. _interactions:

Slash Commands
==============

How To Make A Simple Slash Command
----------------------------------

The following example is a simple ping/pong command using Nextcord's slash commands:

.. code-block:: python3

    @bot.slash_command()
    async def ping(interaction):
        await interaction.response.send_message("Pong!")

The way it works is by using :meth:`~bot.slash_command` decorator to add a slash command for the bot to register with Discord.

``guild_ids`` is used to limit the guilds that the slash command is available to. This is useful for testing as global slash commands can take up to an hour to register.

Example:

.. code-block:: python3

    @bot.slash_command(guild_ids=[id1, id2])

How To Use Sub-Commands
-----------------------

The way sub-commands work is that you make a normal slash command that will never be called, and then make the sub-commands and have them do the work of real slash commands. There is no difference with slash commands and sub-commands. The only thing you will need to change is functions.

As shown in the demonstration below you make a main slash command or a dummy slash command and build sub-commands off it.

.. code-block:: python3

        @bot.slash_command(guild_ids=[...])  # Making the command and limiting the guilds
        async def my_main_command(interaction: Interaction):  
            ...


        @my_main_command.subcommand()  # Identifying The Sub-Command
        async def subcommand_one(
            interaction: Interaction
        ):  # Making The Sub Command Name And Passing Through Interaction
        await interaction.response.send_message(
            "This is subcommand 1!"
        )  # Sending A Response


        # Identifying The Sub-Command And Adding A Descripton
        @my_main_command.subcommand(description="Aha! Another subcommand")  
        async def subcommand_two(interaction: Interaction):  # Passing in interaction

        await interaction.response.send_message(
            "This is subcommand 2!"
        )  # Responding with a message

Fields And Requirements
-----------------------
Fields are meant to facilitate an easier way to fill info, letting people using your slash command get a different response for each answer.

Nextcord's implementation of slash commands has fields and is very simple. in the example below is a field.

.. code-block:: python3

    @bot.slash_command()
    async def choose_a_number(
        interaction: Interaction,
        number: str = SlashOption(name="settings", description="Configure Your Settings", choices={"1": 1, "2": 2,"3": 3})
    ):
        await interaction.response.send_message(f"You chose {number}")


How To Make Slash Commands In Cogs
----------------------------------
Shown below is an example of a simple command running in a cog:

.. code-block:: python3

    class ExampleCog(commands.Cog):
        def __init__(self):
            self.count = 0

        @nextcord.slash_command()
        async def slash_command_cog(self, interaction: Interaction):
            await interaction.response.send_message("Hello I am a slash command in a cog!")

The example shown above responds to a user when they do a slash command. Its function is the same as a slash command on the bot, adjusted to work in a class, only its decorator is different.

How To Make Context Menu Commands
---------------------------------
Context Menu commands display commands on the right-click menu of a message/user.

User Commands
~~~~~~~~~~~~~~
The following code simply prints out the name of the member it was performed on, but can be used for more complex actions too:

.. code-block:: python3

    @bot.user_command()
    async def hello(interaction: Interaction, member: Member):
        await interaction.response.send_message(f"Hello! {member}")

Message Commands
~~~~~~~~~~~~~~~~~
The following is a simple example of a message command which sends the content of the target message as an ephemeral response to the user who invoked it.

.. code-block:: python3

    @bot.message_command()
    async def say(interaction: Interaction, message: Message):
        await interaction.response.send_message(message.content, ephemeral=True)

