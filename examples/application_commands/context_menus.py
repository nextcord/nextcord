import nextcord
from nextcord import Interaction
from nextcord.ext import commands

TESTING_GUILD_ID = 123456789  # Replace with your testing guild id

bot = commands.Bot()


@bot.user_command(guild_ids=[TESTING_GUILD_ID])
async def member_info(interaction: Interaction, member: nextcord.Member):
    await interaction.send(f"this is user {member}")


@bot.message_command(guild_ids=[TESTING_GUILD_ID])
async def my_message_command(interaction: Interaction, message: nextcord.Message):
    await interaction.send(f"the id of this message: {message.id}")


bot.run("token")
