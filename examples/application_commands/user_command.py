import nextcord
from nextcord.interactions import Interaction

client = nextcord.Client()


@client.user_command(guild_ids=[...])  # limits guilds
async def member_info(interaction: Interaction, member: nextcord.Member):  # takes a member
    await interaction.response.send_message(f"Member: {member}")  
    # sends info about the member


client.run("TOKEN")
