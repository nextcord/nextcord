import nextcord
from nextcord import SlashOption
from nextcord.interactions import Interaction

client = nextcord.Client()


@client.slash_command(guild_ids=[...])  # Limits the guildes
async def choose_a_number(
    interaction: Interaction,
    number: str = SlashOption(
        name="picker",
        description="The number you want",
        choices={"1": 1, "2": 2, "3": 3},
    ),
):
    await interaction.response.send_message(f"You chose {number}!")


@client.slash_command(guild_ids=[...])  # limits the guilds with this command
async def hi(
    interaction: Interaction,
    member: nextcord.Member = SlashOption(name="user", description="the user to say hi to"),
):
    await interaction.response.send_message(f"{interaction.user} just said hi to {member.mention}")


client.run("TOKEN")
