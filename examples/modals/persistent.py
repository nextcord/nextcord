import nextcord
from nextcord.ext import commands

TESTING_GUILD_ID = 123456798  # Replace with your testing guild id

class FeedbackModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            title="Feedback",
            custom_id="feedback", # required to make the modal persistent
            timeout=None,
        )
        
        self.discovered = nextcord.ui.TextInput(
            label="How did you discover the bot?",
            required=False,
            style=nextcord.TextInputStyle.paragraph,
            custom_id="discovered", # required to make the modal persistent
        )
        self.add_item(self.discovered)
        
        self.rating = nextcord.ui.TextInput(
            label="How would you rate the bot?",
            placeholder="I would give the bot a ten out of ten...",
            custom_id="rating", # required to make the modal persistent
        )
        self.add_item(self.rating)
        
        self.improve = nextcord.ui.TextInput(
            label="How could the bot improve?",
            style=nextcord.TextInputStyle.paragraph,
            required=False,
            custom_id="improve", # required to make the modal persistent
        )
        self.add_item(self.improve)
    
    async def callback(self, interaction: nextcord.Interaction):
        await interaction.send(
            f"{interaction.user.mention} feedback :\n"
            f"Rating: {self.rating.value}\n"
            f"Where they discovered the bot: {self.discovered.value}\n"
            f"How could the bot improve: {self.improve.value}\n"
        )

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persistent_modals_added = False

    async def on_ready(self):
        if not self.persistent_modals_added:
            # Register the persistent modal for listening here.
            self.add_modal(FeedbackModal())
            self.persistent_modals_added = True

        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

bot = Bot('!')

@bot.slash_command(
    name="feedback",
    description="Send your feedback to the bot developer!",
    guild_ids=[TESTING_GUILD_ID],
)
async def feedback(interaction: nextcord.Interaction):
    await interaction.response.send_modal(FeedbackModal())

bot.run("token")