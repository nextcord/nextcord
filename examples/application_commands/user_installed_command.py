from nextcord import IntegrationType, Interaction, InteractionContextType
from nextcord.ext import commands

bot = commands.Bot()


@bot.slash_command(
    description="An example slash command demonstrating user installed apps",
    # These parameters can be used on any application command type
    integration_types=[
        IntegrationType.user_install,  # Command will be available when the app is installed on a user.
        IntegrationType.guild_install,  # Command will be available when the app is added to a server.
    ],
    contexts=[
        InteractionContextType.guild,  # Command can be used within servers.
        InteractionContextType.bot_dm,  # Command can be used within DMs with the app's bot user.
        InteractionContextType.private_channel,  # Command can be used within Group DMs and DMs other than the app's bot user.
    ],
)
async def example_slash_command(interaction: Interaction):
    if interaction.context == InteractionContextType.guild:
        place = "within a server"
    elif interaction.context == InteractionContextType.bot_dm:
        place = "within DMs with the app's bot user"
    elif interaction.context == InteractionContextType.private_channel:
        place = "within a Group DM or DM other than the app's bot user"
    else:
        place = "somewhere nextcord doesn't support yet"

    await interaction.response.send_message(f"This command was run {place}.")


bot.run("token")
