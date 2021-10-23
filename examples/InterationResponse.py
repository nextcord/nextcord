import nextcord
from nextcord.ext import commands

bot = commands.Bot()

#This Example Can Be Found On The Docs Aswell.
@bot.slash_command(name="ping", guild_ids=[GUILD_ID]) # Call The Function Define The Name If You Need It For Dynamic Help Commands And Which Guilds Get The Slash Command.
async def ping(interaction): # Passing Through interaction And The Name.
    await interaction.response.send_message("Pong!") # Send The Response, Please Don't Use CTX.
