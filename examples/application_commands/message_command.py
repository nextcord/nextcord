from nextcord import Interaction
from nextcord.ext import commands

bot = commands.Bot(command_prefix="$") # won't let you do $my_slash_command


@bot.message_command(guild_ids=[...])  # limits guild's with this command
async def my_message_command(
    interaction: Interaction, message
):  # takes in message and uses Interaction.
    await interaction.response.send_message(f"Message: {message}")  # sends the message.


bot.run("TOKEN")
