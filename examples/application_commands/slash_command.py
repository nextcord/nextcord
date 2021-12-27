from nextcord.ext import commands

bot = commands.Bot(command_prefix="$")  # won't let you do $my_slash_command


@bot.slash_command(guild_ids=[...]) # limits guilds with this command.
async def ping(interaction):  # Passing Through interaction And The Name.
    await interaction.response.send_message("Pong!")  
    # Send The Response, Please Don't Use CTX.


bot.run("TOKEN")
