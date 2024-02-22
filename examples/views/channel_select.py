from config import token

import nextcord
from nextcord.ext import commands


class Channels(nextcord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Choose your favourite channel...",
            min_values=1,
            max_values=5,
        )

    async def callback(self, interaction: nextcord.Interaction):
        channels = ", ".join([f"``{i.name}``" for i in self.values.channels])
        await interaction.response.send_message(f"Your favourite channels is {channels}")


class TextChannel(nextcord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Choose your favourite channel...",
            min_values=1,
            max_values=5,
            channel_types=[nextcord.ChannelType.text],
        )

    async def callback(self, interaction: nextcord.Interaction):
        channels = ", ".join([f"``{i.name}``" for i in self.values.channels])
        await interaction.response.send_message(f"Your favourite channels is {channels}")


class ChannelsView(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Channels())


class TextChannelsView(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TextChannel())


bot = commands.Bot()


@bot.slash_command()
async def channel_select(interaction):
    """Sends a message with our dropdown containing colours"""

    view = ChannelsView()
    await interaction.send("Pick your favourite channels:", view=view)


@bot.slash_command()
async def text_channel_select(interaction):
    """Sends a message with our dropdown containing colours"""

    view = TextChannelsView()
    await interaction.send("Pick your favourite channels:", view=view)


bot.run(token)
