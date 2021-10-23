.. currentmodule:: nextcord

.. _ext_slash_temp_introduction:

A Introduction To Interaction Commands
=======================================

As discord have limited the access of message content, Nextcord have decided to add Slash Commands to there fleet of features, This page will teach you the basics of slash commands how they work how you can use them and more!

This right here is a simple ping Pong! Command made with Nextcords slash feature.

.. code-block:: python3

    @bot.slash_command(name="ping", guild_ids=[GUILD_ID])
    async def ping(interaction):
        await interaction.response.send_message("Pong!")
        
The way it works is that you use the slash_command fuction to interact with the DiscordAPI "name" is the name of your slash command, And guild_ids is used to limit the guilds that the slash command is available also useful for testing as slash commands can take up to an hour to register

Sub-Commands
-------------

The way sub-commands work is that you will make a normal slash command that will never be called then make the sub-commands and have them only do the work of real slash commands, There is no difference to slash commands and sub-cmmands, The Only thing you will need to change is functions. 

As shown in the demistration below you make a main slash command or a Dummy slash command and build sub-commands off it

.. code-block:: python3

    @bot.slash_command(guild_ids=[GUILD_ID])
    async def main(interaction):
        await interaction.response.send_message("This will never get called if this has subcommands.")


    @main.subcommand()
    async def sub1(interaction):
        await interaction.response.send_message("This is subcommand 1!")


    @main.subcommand(name="sub2", description="This is subcommand 2 tricked out!")
    async def subcommand_two(interaction: Interaction,
                            arg1: str = SlashOption(name="argument1", description="The first argument."),
                            arg2: str = SlashOption(description="The second argument!", default=None)):
        await interaction.response.send_message(f"This is subcommand 2 with arg1 {arg1} and arg2 {arg2}")
