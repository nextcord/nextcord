import nextcord
from nextcord.ext import commands

TESTING_GUILD_ID = 123456798  # Replace with your testing guild id


# Define a simple Modal that persists between bot restarts
# In order for a Modal to persist between restarts it needs to meet the following conditions:
# 1) The timeout of the Modal has to be set to None
# 2) The Modal has to have a custom_id set
# 3) Every item in the Modal has to have a custom_id set
# It is recommended that the custom_id be sufficiently unique to
# prevent conflicts with other modals the bot sends.
# For this example the custom_id is prefixed with the name of the bot.
# Note that custom_ids can only be up to 100 characters long.
class FeedbackModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            title="Feedback",
            custom_id="persistent_modal:feedback",
            timeout=None,
        )

        self.discovered = nextcord.ui.TextInput(
            label="How did you discover the bot?",
            placeholder="e.g. Discord server, friend, etc.",
            required=False,
            style=nextcord.TextInputStyle.paragraph,
            custom_id="persistent_modal:discovered",
        )
        self.add_item(self.discovered)

        self.rating = nextcord.ui.TextInput(
            label="How would you rate the bot out of 10?",
            placeholder="10",
            max_length=2,
            custom_id="persistent_modal:rating",
        )
        self.add_item(self.rating)

        self.improve = nextcord.ui.TextInput(
            label="How could the bot improve?",
            placeholder="e.g. add more features, improve the UI, etc.",
            style=nextcord.TextInputStyle.paragraph,
            required=False,
            custom_id="persistent_modal:improve",
        )
        self.add_item(self.improve)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.send(
            f"Feedback from {interaction.user.mention}:\n"
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
            # Note that this does not display the modal to the user.
            # To do that, you need to respond to an interaction as shown below.
            self.add_modal(FeedbackModal())
            self.persistent_modals_added = True

        print(f"Logged in as {self.user} (ID: {self.user.id})")


bot = Bot()


@bot.slash_command(
    name="feedback",
    description="Send your feedback to the bot developer!",
    guild_ids=[TESTING_GUILD_ID],
)
async def feedback(interaction: nextcord.Interaction):
    await interaction.response.send_modal(FeedbackModal())


bot.run("token")
