import nextcord
from nextcord import Interaction

client = nextcord.Client()


@client.slash_command(guild_ids=[...])  # Making the command and limiting the guilds
async def main(
    interaction: Interaction,
):  # passing through interaction and indentifing the sub-command group name
    await interaction.response.send_message("This will never get called if this has subcommands.")
    # a function never called


@main.subcommand()  # Identifying The Sub-Command
async def sub1(
    interaction: Interaction,
):  # Making The Sub Command Name And Passing Through Interaction
    await interaction.response.send_message("This is subcommand 1!")
    # Sending A Response


@main.subcommand(description="Aha! Another subcommand")  # Identifying The Sub-Command And Adding A Descripton
async def subcommand_two(interaction: Interaction):  # Passing in interaction

    await interaction.response.send_message("This is subcommand 2!")
    # Responding With The Args/Fields


client.run("TOKEN")
