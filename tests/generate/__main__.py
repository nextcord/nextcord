# SPDX-License-Identifier: MIT

from nextcord.ext import commands
from tests import utils

from .base import GenerateBase
from .components import GenerateComponents

assert utils.EnvVar.bot_token is not None
bot = commands.Bot(default_guild_ids=[utils.EnvVar.test_guild] if utils.EnvVar.test_guild else None)


@bot.event
async def on_ready():
    print("Bot ready.")


base = GenerateBase()
components = GenerateComponents()
bot.add_cog(base)
bot.add_cog(components)


bot.run(utils.EnvVar.bot_token)
