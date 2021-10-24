:orphan:

.. currentmodule:: nextcord

.. _interactions:

Interaction Commands
=====================

As discord have added interaction commands a feature with alot of possiblity's and idea's we at nextcord have decided to add them to our fleet of features,

This doc will explain the innerworkings and how to use interaction commmands.

We suggest you learn how to make regular commands before looking through here.

How To Make A Simple Interaction Command
-----------------------------------------

This right here is a simple ping pong Command made with Nextcords slash feature.

.. code-block:: python3

    @bot.slash_command(name="ping", guild_ids=[GUILD_ID])
    async def ping(interaction):
        await interaction.response.send_message("Pong!")
        
The way it works is that you use the slash_command fuction to interact with the DiscordAPI "name" is the name of your slash command, And guild_ids is used to limit the guilds that the slash command is available also useful for testing as slash commands can take up to an hour to register

How To Use Sub-Commands
------------------------

The way sub-commands work is that you will make a normal slash command that will never be called then make the sub-commands and have them do the work of real slash commands, There is no difference to slash commands and sub-commands, The Only thing you will need to change is functions. 

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
        
Fields And Requirements
------------------------
Fields are mean't to facilitate an easier way to fill info, Letting people doing a slash commands know what to fill in

Nextcord's implementation of slash commands has fields and is very simple, In the example below is a field

.. code-block:: python3
     
     @bot.slash_command(name="help", guild_ids="GUILD_ID")
     async def help(interaction: Interaction,
                    settings: str = SlashOption(name=settings, description="Your Current Help Settings")
                    music: str = SlashOption(name=music, description="Your Music Settings")):
         await interaction.response.send_message(f"") 


How To Make Slash Commands In Cogs
-----------------------------------
Show below is an example of a simple command running in a cog, It is very basic doesn't have alot of features, Some features planned is autocomplete and proper error handling to slash commands, So that mean's that slash cogs are gonna need to get a massive upgrade and will change alot, Since this is a very simple slash command cog it won't change just the more advanced features.

.. code-block:: python3
      
      class ExampleCog(commands.Cog):
    def __init__(self):
        self.count = 0

    @commands.command(name="cogexample")
    async def example_cog_command(self, context: commands.Context):
        await context.send("Hi there i am a normal command!")
        print(f"COGEXAMPLE: {context.guild.members}")

    @slash_command(name="cogexample", guild_ids=[GUILD_ID])
    async def slash_example_cog_command(self, interaction):
        await interaction.response.send_message("Hello i am a slash command in a cog!")

    @slash_command(name="dump", guild_ids=[GUILD_ID])
    async def do_member(self, interaction: Interaction, member: nextcord.Member):
        await interaction.response.send_message(f"Member found: {member}")

    @user_command(name="dump", guild_ids=[GUILD_ID])
    async def userdump(self, interaction, member):
        await interaction.response.send_message(f"Member: {member}, Data Dump: {interaction.data}")

    @message_command(name="dump", guild_ids=[GUILD_ID])
    async def messagedump(self, interaction, message: Message):
        await interaction.response.send_message(f"Data Dump: {interaction.data}")

  bot.add_cog(ExampleCog())
  bot.run(TOKEN)

The example shown above responds to a user when they do a slash command, It is very identical to a normal slash command and to normal commands in general.

How To Use Advanced Cog Features
---------------------------------
Classes Etc **Coming Soon**


Role And User Permissions
--------------------------

Autocomplete
-------------
