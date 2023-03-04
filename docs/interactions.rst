:orphan:

.. currentmodule:: nextcord

.. _interactions:

Application Commands
====================

Simple Slash Command Example
----------------------------

The following example is a simple ping command using slash commands:

.. code-block:: python3

    @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
    async def ping(interaction: nextcord.Interaction):
        """Simple command that responds with Pong!"""
        await interaction.response.send_message("Pong!")

The way it works is by using the :meth:`~nextcord.ext.commands.Bot.slash_command` decorator to add a slash command for the bot to register with Discord.

``guild_ids`` is used to limit the guilds that the slash command is available to. This is useful for testing as global slash commands can take up to an hour to register.

The names of slash commands and their command options must only contain lowercase letters, numbers, hyphens, and underscores and be between 1 and 32 characters long.

Slash Command Options
---------------------

Slash options are used to allow the user to specify additional information for the command.

Below is an example that takes a single argument, ``arg``, and repeats it back to the user:

.. code-block:: python3

    @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
    async def echo(interaction: nextcord.Interaction, arg: str):
        """Repeats your message that you send as an argument

        Parameters
        ----------
        interaction: Interaction
            The interaction object
        arg: str
            The message to repeat. This is a required argument.
        """
        await interaction.response.send_message(f"You said: {arg}")

The option can be type-hinted with :class:`int`, :class:`float`, or :class:`bool` to change the type of the argument.

You can also set ``required=False`` in a :class:`~nextcord.SlashOption` or set a default value to make the argument optional.

.. code-block:: python3

    from typing import Optional

    @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
    async def echo_number(
        interaction: nextcord.Interaction,
        number: Optional[int] = SlashOption(required=False)
    ):
        """Repeats your number that you send as an argument

        Parameters
        ----------
        interaction: Interaction
            The interaction object
        arg: Optional[int]
            The number to repeat. This is an optional argument.
        """
        if number is None:
            await interaction.response.send_message("You didn't specify a number!")
        else:
            await interaction.response.send_message(f"You said: {number}")

Choices
~~~~~~~

You can also use choices to make fields that only accept certain values.

The choices can be specified using ``choices`` in a :class:`~nextcord.SlashOption` which can be a list of choices or a mapping of choices to their values.

.. code-block:: python3

    @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
    async def choose_a_number(
        interaction: nextcord.Interaction,
        number: int = SlashOption(
            name="picker",
            choices={"one": 1, "two": 2, "three": 3},
        ),
    ):
        """Repeats your number that you choose from a list

        Parameters
        ----------
        interaction: Interaction
            The interaction object
        number: int
            The chosen number.
        """
        await interaction.response.send_message(f"You chose {number}!")

You can also specify a type annotation such as :class:`nextcord.Member`, :class:`nextcord.abc.GuildChannel`, or :class:`nextcord.Role`
to make the command display a list of those types of objects.

.. code-block:: python3

    @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
    async def hi(interaction: nextcord.Interaction, user: nextcord.Member):
        """Say hi to a user

        Parameters
        ----------
        interaction: Interaction
            The interaction object
        user: nextcord.Member
            The user to say hi to.
        """
        await interaction.response.send_message(
            f"{interaction.user} just said hi to {user.mention}"
        )


Subcommands
-----------

To make a subcommand, you must first make a base slash command that will not be called and then make the subcommands on it.

Subcommands of a base command can also have subcommands, but the subcommands of a subcommand cannot. See the diagram below for an illustration.

.. code-block::

    command
    ├── subcommand-group
    │   └── subcommand
    └── subcommand

As shown in the demonstration below you make a main slash command and build subcommands using the :meth:`~nextcord.ApplicationCommand.subcommand` decorator on it.

.. code-block:: python3

    @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
    async def main(interaction: nextcord.Interaction):
        """
        This is the main slash command that will be the prefix of all commands below.
        This will never get called since it has subcommands.
        """
        pass


    @main.subcommand(description="Subcommand 1")
    async def sub1(interaction: nextcord.Interaction):
        """
        This is a subcommand of the '/main' slash command.
        It will appear in the menu as '/main sub1'.
        """
        await interaction.response.send_message("This is subcommand 1!")


    @main.subcommand(description="Subcommand 2")
    async def sub2(interaction: nextcord.Interaction):
        """
        This is another subcommand of the '/main' slash command.
        It will appear in the menu as '/main sub2'.
        """
        await interaction.response.send_message("This is subcommand 2!")


    @main.subcommand()
    async def main_group(interaction: nextcord.Interaction):
        """
        This is a subcommand group of the '/main' slash command.
        All subcommands of this group will be prefixed with '/main main_group'.
        This will never get called since it has subcommands.
        """
        pass


    @main_group.subcommand(description="Subcommand group subcommand 1")
    async def subsub1(interaction: nextcord.Interaction):
        """
        This is a subcommand of the '/main main_group' subcommand group.
        It will appear in the menu as '/main main_group subsub1'.
        """
        await interaction.response.send_message("This is a subcommand group's subcommand!")


    @main_group.subcommand(description="Subcommand group subcommand 2")
    async def subsub2(interaction: nextcord.Interaction):
        """
        This is another subcommand of the '/main main_group' subcommand group.
        It will appear in the menu as '/main main_group subsub2'.
        """
        await interaction.response.send_message("This is subcommand group subcommand 2!")


Context Menu Commands
---------------------

Context menu commands display commands in the Apps section of the right-click menu of a user or message.

User Commands
~~~~~~~~~~~~~

Here is an example of a command that will say hi to a user that was right-clicked on.

.. code-block:: python3

    @bot.user_command(guild_ids=[TESTING_GUILD_ID])
    async def hello(interaction: nextcord.Interaction, member: nextcord.Member):
        """Says hi to a user that was right-clicked on"""
        await interaction.response.send_message(f"Hello {member}!")

Message Commands
~~~~~~~~~~~~~~~~

Here is an example of a message command which sends the content of the right-clicked message as an ephemeral response to the user who invoked it.

.. code-block:: python3

    @bot.message_command(guild_ids=[TESTING_GUILD_ID])
    async def say(interaction: nextcord.Interaction, message: nextcord.Message):
        """Sends the content of the right-clicked message as an ephemeral response"""
        await interaction.response.send_message(message.content, ephemeral=True)


Deferred Response
-----------------

Discord expects you to respond in 3 seconds, you can extend that by deferring and then sending followup in the next 15 minutes.

Responding to the interaction with :meth:`~nextcord.InteractionResponse.defer` will show the "bot is thinking" message to the user
until the followup response is sent.

Note: by default the message will be public, but you can make it visible only to the user by setting the ``ephemeral`` parameter to ``True``.

.. code-block:: python3

    @bot.slash_command(guild_ids=[TESTING_GUILD_ID])
    async def hi(interaction: nextcord.Interaction):
        """Say hi to a user"""
        # defer the response, so we can take a long time to respond
        await interaction.response.defer()
        # do something that takes a long time
        await asyncio.sleep(5)
        # followup must be used after defer since a response is already sent
        await interaction.followup.send(f"Hi {interaction.user}! Thanks for waiting!")


Application Commands in Cogs
----------------------------

Shown below is an example of a simple command running in a cog:

.. code-block:: python3

    class ExampleCog(commands.Cog):
        def __init__(self):
            self.count = 0

        @nextcord.slash_command(guild_ids=[TESTING_GUILD_ID])
        async def slash_command_cog(self, interaction: nextcord.Interaction):
            """This is a slash command in a cog"""
            await interaction.response.send_message("Hello I am a slash command in a cog!")

Context menu commands can also be made in cogs using the :meth:`nextcord.user_command` or :meth:`nextcord.message_command` decorators.


Default Guild IDs
-----------------

If you would like for all of your application commands to have the same guild ids unless explicitly stated, then you can set the ``default_guild_ids`` keyword argument in :class:`~nextcord.Client`, :class:`~nextcord.ext.commands.Bot`, or :class:`~nextcord.ext.commands.AutoShardedBot`!

Here's an example of this:

.. code-block:: python3

    bot = commands.Bot(..., default_guild_ids=[TESTING_GUILD_ID])

    @bot.slash_command()
    async def bye(interaction: nextcord.Interaction):
        await interaction.response.send_message(f"Goodbye {bot.default_guild_ids}!")

    @bot.slash_command(guild_ids=None)
    async def bye_global(interaction: nextcord.Interaction):
        await interaction.response.send_message("Goodbye everyone!")
