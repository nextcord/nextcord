from nextcord.ext import commands
from nextcord import Interaction

bot = commands.Bot(command_prefix="/")


@bot.message_command(guild_ids=[...])  # limits guild's with this command
async def my_message_command(
    interaction: Interaction, message
):  # takes in message and uses Interaction.
    await interaction.response.send_message(f"Message: {message}")  # sends the message.


bot.run("TOKEN")
