from nextcord import Interaction, SlashOption
from nextcord.ext import commands

bot = commands.Bot(command_prefix="$")  # won't let you do $my_slash_command


@bot.slash_command(guild_ids=[...])  # Making the command and limiting the guilds
async def main(
    interaction,
):  # passing through interaction and indentifing the sub-command group name
    await interaction.response.send_message(
        "This will never get called if this has subcommands."
    )  # a function never called


@main.subcommand()  # Identifying The Sub-Command
async def sub1(
    interaction,
):  # Making The Sub Command Name And Passing Through Interaction
    await interaction.response.send_message(
        "This is subcommand 1!"
    )  # Sending A Response


@main.subcommand(
    description="Aha! Another subcommand"
)  # Identifying The Sub-Command And Adding A Descripton
async def subcommand_two(interaction: Interaction):  # Passing in interaction

    await interaction.response.send_message(
        "This is subcommand 2!"
    )  # Responding With The Args/Fields


bot.run("TOKEN")
