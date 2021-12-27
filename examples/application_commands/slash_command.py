from nextcord.ext import commands

bot = commands.Bot(command_prefix="$")

# This Example Can Be Found On The Docs Aswell.
@bot.slash_command(guild_ids=[...])
# Call The Function Define The Name If You Need It For Dynamic Help Commands And Which Guilds Get The Slash Command.
async def ping(interaction):  # Passing Through interaction And The Name.
    await interaction.response.send_message(
        "Pong!"
    )  # Send The Response, Please Don't Use CTX.


bot.run("TOKEN")
