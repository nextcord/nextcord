import nextcord
from nextcord import SlashOption
from nextcord.interactions import Interaction

client = nextcord.Client()


@client.slash_command(guild_ids=[...])  # Limits the guildes
async def my_select_command(
    interaction: Interaction, help: str = SlashOption(name="Say a help option!")
):
    if help == "fun":
        interaction.response.send_message("Fun!")
    elif help == "music":
        interaction.response.send_message(
            "Sorry lavalink support hasn't come to the line!"
        )
    elif help == "mod":
        interaction.response.send_message(
            "Moderation is now moved to somewhere else..."
        )
    else:
        interaction.response.send_message("Could not find that help option!")


client.run("TOKEN")
