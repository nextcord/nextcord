# Your bot token should not be made public with your code. Otherwise anyone can sign in as your bot and mess with its servers.
# You should load the token as an environment variable, then access it like this:

import os
from nextcord.ext import commands

# There are other ways to load environment variables but this is one
from dotenv import load_dotenv # https://pypi.org/project/python-dotenv/

# load_dotenv reads from a file called .env in the same directory as the python files which should roughly look like BOT_TOKEN="1234567890"
load_dotenv()

bot = commands.Bot(command_prefix="$")

# run the bot using the token in .env
bot.run(os.getenv('BOT_TOKEN'))
