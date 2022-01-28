import nextcord

client = nextcord.Client()


@client.slash_command(guild_ids=[...])  # limits guilds with this command.
async def ping(
    interaction: nextcord.Interaction,
):
    await interaction.response.send_message("Pong!")


client.run("TOKEN")
