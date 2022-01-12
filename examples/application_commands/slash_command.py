import nextcord
from nextcord.ext import commands

client = nextcord.Client()


@client.slash_command(guild_ids=[...]) # limits guilds with this command.
async def ping(interaction: nextcord.Interaction):  # Passing Through interaction And The Name.
    await interaction.response.send_message("Pong!")  
    # Send The Response, Please Don't Use CTX.


client.run("TOKEN")
