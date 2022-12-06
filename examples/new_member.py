# This example requires the 'members' privileged intent
import nextcord
from nextcord.ext import commands


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_member_join(self, member):
        guild = member.guild
        if guild.system_channel is not None:
            to_send = f"Welcome {member.mention} to {guild.name}!"
            await guild.system_channel.send(to_send)


intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = Bot(command_prefix="$", intents=intents)
bot.run("token")
