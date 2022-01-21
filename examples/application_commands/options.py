import nextcord
from nextcord import SlashOption
from nextcord.interactions import Interaction

client = nextcord.Client()


@client.slash_command(guild_ids=[...])  # Limits the guildes
async def my_select_command(
    interaction: Interaction, help: str = SlashOption(name="option", description="The option you want", choices={"fun", "music", "mod"})
):
    if help == "fun":
        interaction.response.send_message("Fun!")
    elif help == "music":
        interaction.response.send_message(
            "Music.."
        )
    elif help == "mod":
        interaction.response.send_message(
            "Moderation is now moved to somewhere else..."
        )
    else:
        interaction.response.send_message("Could not find that help option!")
        
@client.slash_command(guild_ids=[...]) # limits the guilds with this command
async def hi(interaction: Interaction, member: nextcord.Member = SlashOption(name="user", description="the user to say hi to")):
    await interaction.response.send_message(f"{interaction.user} just said hi to {member.mention}")

client.run("TOKEN")
