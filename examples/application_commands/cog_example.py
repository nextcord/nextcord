from nextcord import Interaction, message_command, slash_command, user_command, Message, Member
from nextcord.ext import commands


class ApplicationCommandCog(commands.Cog):  # Subclassing commands.Cog as you always do.
    def __init__(self, bot: commands.Bot):  # takes in bot for the setup later
        self.bot = bot  # making it global to this class.

    @slash_command(guild_ids=[...])  # isn't really any different to normal commands.
    async def my_slash_command(self, interaction: Interaction):
        await interaction.response.send_message("This is a slash command in a cog!")

    @user_command(guild_ids=[...])  # Again very simular to normal commands.
    async def my_user_command(
        self, interaction: Interaction, member: Member
    ):  # passing in member as it is intaked
        await interaction.response.send_message(f"Hello, {member}!")

    @message_command(guild_ids=[...])  # limits guilds
    async def my_message_command(
        self, interaction: Interaction, message: Message
    ):  # passing in message as it is intaked
        await interaction.response.send_message(f"{message}")


def setup(bot):
    bot.add_cog(ApplicationCommandCog(bot))  # adds the cog to your bot.
