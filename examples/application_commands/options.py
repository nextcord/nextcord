from nextcord import SlashOption
from nextcord.ext import commands
from nextcord.interactions import Interaction

bot = commands.Bot(command_prefix="/")


@bot.slash_command(guild_ids=[...])  # Limits the guides
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


bot.run("TOKEN")
