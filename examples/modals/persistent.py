import nextcord
from nextcord.ext import commands

TESTING_GUILD_ID = 123456798  # Replace with your testing guild id

class Feedback(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            title="Feedback",
            custom_id="feedback",
            timeout=None,
        )
        self.discovered = nextcord.ui.TextInput(
            label="How did you discover the bot?",
            required=False,
            style=nextcord.TextInputStyle.paragraph,
            custom_id="discovered",
        )
        self.rating = nextcord.ui.TextInput(
            label="How would you rate the bot?",
            placeholder="I would give the bot a ten out of ten...",
            custom_id="rating",
        )
        self.improve = nextcord.ui.TextInput(
            label="How could the bot improve?",
            style=nextcord.TextInputStyle.paragraph,
            required=False,
            custom_id="improve",
        )
        self.add_item(self.discovered)
        self.add_item(self.rating)
        self.add_item(self.improve)
    
    async def callback(self, interaction: nextcord.Interaction):
        await interaction.send(
            f"{interaction.user.mention} feedback :\n"
            f"Rating: {self.rating.value}\n"
            f"Where they discovered the bot: {self.discovered.value}\n"
            f"How could the bot improve: {self.improve.value}\n"
        )

bot = commands.Bot()

feedback_modal = None

@bot.event
async def on_ready():
    global feedback_modal
    feedback_modal = Feedback()
    bot.add_modal(feedback_modal)

@bot.slash_command(
    name="feedback",
    description="Send your feedback to the bot developer!",
    guild_ids=[TESTING_GUILD_ID],
)
async def feedback(interaction: nextcord.Interaction):
    await interaction.response.send_modal(feedback_modal)

bot.run("token")