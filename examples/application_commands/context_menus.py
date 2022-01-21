import nextcord
from nextcord.interactions import Interaction

client = nextcord.Client()


@client.user_command(guild_ids=[...])  # limits guilds
async def member_info(interaction: Interaction, member: nextcord.Member):  # takes a member
    await interaction.response.send_message(f"Member: {member}")  
    # sends info about the member

@client.message_command(guild_ids=[...])  # limits guilds
async def my_message_command(interaction: Interaction, message: nextcord.Message):  
    # takes in message and uses Interaction.
    await interaction.response.send_message(f"Message: {message}")  # sends the message.


client.run("TOKEN")
