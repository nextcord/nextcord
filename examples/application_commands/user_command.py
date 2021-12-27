from nextcord.ext import commands
from nextcord.interactions import Interaction

bot = commands.Bot(command_prefix="$")  # won't let you do $my_slash_command


@bot.user_command(guild_ids=[...])  # limits guilds
async def my_user_command(interaction: Interaction, member):  # intakes member
    await interaction.response.send_message(
        f"Member: {member}"
    )  # sends info about the member


bot.run("TOKEN")
