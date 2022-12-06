import nextcord
from nextcord.ext import commands

TESTING_GUILD_ID = 123456789  # Replace with your testing guild id


class ApplicationCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @nextcord.slash_command(guild_ids=[TESTING_GUILD_ID], description="Test command")
    async def my_slash_command(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.send_message("This is a slash command in a cog!")

    @nextcord.user_command(guild_ids=[TESTING_GUILD_ID])
    async def my_user_command(
        self, interaction: nextcord.Interaction, member: nextcord.Member
    ) -> None:
        await interaction.response.send_message(f"Hello, {member}!")

    @nextcord.message_command(guild_ids=[TESTING_GUILD_ID])
    async def my_message_command(
        self, interaction: nextcord.Interaction, message: nextcord.Message
    ) -> None:
        await interaction.response.send_message(f"{message}")


def setup(bot) -> None:
    bot.add_cog(ApplicationCommandCog(bot))
