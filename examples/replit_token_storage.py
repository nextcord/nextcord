import nextcord
from nextcord.ext import commands
import os

bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
  print('Bot online!')
 
@bot.command()
async def ping(ctx):
  await ctx.send('Ping!')

# In repl.it there is a secret variable witch you can store ur secrets
# You need to navigate to a lock icon on the left side of ur screen
# After that you schould see a field called "key" thats where you put the name of ur token for example "token" or "discord-bot-token"
# On the bottom of the key you schould see another field called "value" that is where you put ur bot token
# After that press the Add new secret button and ur done!
  
token = os.environ['token']
bot.run(token)
