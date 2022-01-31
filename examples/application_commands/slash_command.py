import nextcord
from nextcord import Interaction, SlashOption

TESTING_GUILD_ID = 123456789  # Replace with your testing guild id

client = nextcord.Client()

# command will be global if guild_ids is not specified
@client.slash_command(guild_ids=[TESTING_GUILD_ID])
async def ping(interaction: Interaction):
    await interaction.response.send_message("Pong!")


@client.slash_command(guild_ids=[TESTING_GUILD_ID])
async def echo(interaction: Interaction, arg: str):
    await interaction.response.send_message(arg)


@client.slash_command(guild_ids=[TESTING_GUILD_ID])
async def enter_a_number(interaction: Interaction, number: int = SlashOption(required=False)):
    if not number:
        await interaction.response.send_message("You need to specify a number!", ephemeral=True)
    else:
        await interaction.response.send_message(f"You chose {number}!")


client.run("token")
