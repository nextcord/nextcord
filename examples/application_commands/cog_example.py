import nextcord

TESTING_GUILD_ID = 123456789  # Replace with your testing guild id


class ApplicationCommandCog(nextcord.ClientCog):
    # Add a check for every application command in this ClientCog. Execute command if True, dont execute command if False.
    def cog_application_command_check(self, interaction: nextcord.Interaction):
        if interaction.user:
            return interaction.user.id == 123456789 # Example User ID, replace with your own for testing
        else:
            return False

    @nextcord.slash_command(guild_ids=[TESTING_GUILD_ID], description="Test command")
    async def my_slash_command(self, interaction: nextcord.Interaction):
        await interaction.response.send_message("This is a slash command in a cog!")

    @nextcord.user_command(guild_ids=[TESTING_GUILD_ID])
    async def my_user_command(self, interaction: nextcord.Interaction, member: nextcord.Member):
        await interaction.response.send_message(f"Hello, {member}!")

    @nextcord.message_command(guild_ids=[TESTING_GUILD_ID])
    async def my_message_command(self, interaction: nextcord.Interaction, message: nextcord.Message):
        await interaction.response.send_message(f"{message}")
