from nextcord import Interaction
from nextcord.ext import commands

TESTING_GUILD_ID = 123456789  # Replace with your testing guild id

bot = commands.Bot()


@bot.slash_command(guild_ids=[TESTING_GUILD_ID], description="main command")
async def main(interaction: Interaction):
    """
    This is the main slash command that will be the prefix of all commands below.
    This will never get called since it has subcommands.
    """
    pass


@main.subcommand(description="Subcommand 1")
async def sub1(interaction: Interaction):
    """
    This is a subcommand of the '/main' slash command.
    It will appear in the menu as '/main sub1'.
    """
    await interaction.response.send_message("This is subcommand 1!")


@main.subcommand(description="Subcommand 2")
async def sub2(interaction: Interaction):
    """
    This is another subcommand of the '/main' slash command.
    It will appear in the menu as '/main sub2'.
    """
    await interaction.response.send_message("This is subcommand 2!")


@main.subcommand(description="main_group subcommand group")
async def main_group(interaction: Interaction):
    """
    This is a subcommand group of the '/main' slash command.
    All subcommands of this group will be prefixed with '/main main_group'.
    This will never get called since it has subcommands.
    """
    pass


@main_group.subcommand(description="Subcommand group subcommand 1")
async def subsub1(interaction: Interaction):
    """
    This is a subcommand of the '/main main_group' subcommand group.
    It will appear in the menu as '/main main_group subsub1'.
    """
    await interaction.response.send_message("This is a subcommand group's subcommand!")


@main_group.subcommand(description="Subcommand group subcommand 2")
async def subsub2(interaction: Interaction):
    """
    This is another subcommand of the '/main main_group' subcommand group.
    It will appear in the menu as '/main main_group subsub2'.
    """
    await interaction.response.send_message("This is subcommand group subcommand 2!")


bot.run("token")
