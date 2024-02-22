from nextcord import Interaction, Embed, Color
from nextcord.ext import commands


webhook_id = 0
client = commands.Bot()
client.webhook = None


@client.event
async def on_ready():
    webhook = await client.fetch_webhook(webhook_id)
    client.webhook = webhook


@client.slash_command()
async def send_webhook(interaction: Interaction, title: str, description: str):
    if client.webhook is None:
        return
    await client.webhook.send(embed=Embed(title=title, description=description, color=Color.green()))
    await interaction.send("sent", ephemeral=True)


client.run("token")
