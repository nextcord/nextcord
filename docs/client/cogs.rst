.. currentmodule:: nextcord

.. _client_cogs:

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
