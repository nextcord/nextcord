import nextcord
from nextcord import Interaction

client = nextcord.Client()


@client.message_command(guild_ids=[...])  # limits guild's with this command
async def my_message_command(interaction: Interaction, message: nextcord.Message):  
    # takes in message and uses Interaction.
    await interaction.response.send_message(f"Message: {message}")  # sends the message.


client.run("TOKEN")
