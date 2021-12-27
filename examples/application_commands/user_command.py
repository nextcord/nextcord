import nextcord
from nextcord.interactions import Interaction

client = nextcord.Client()


@client.user_command(guild_ids=[...])  # limits guilds
async def my_user_command(interaction: Interaction, member):  # intakes member
    await interaction.response.send_message(f"Member: {member}")  
    # sends info about the member


client.run("TOKEN")
