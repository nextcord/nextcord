import nextcord
from nextcord.ext import application_checks, commands


# Define a simple View that persists between bot restarts
# In order for a view to persist between restarts it needs to meet the following conditions:
# 1) The timeout of the View has to be set to None
# 2) Every item in the View has to have a custom_id set
# It is recommended that the custom_id be sufficiently unique to
# prevent conflicts with other buttons the bot sends.
# For this example the custom_id is prefixed with the name of the bot.
# Note that custom_ids can only be up to 100 characters long.
class PersistentView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(
        label="Green", style=nextcord.ButtonStyle.green, custom_id="persistent_view:green"
    )
    async def green(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("This is green.", ephemeral=True)

    @nextcord.ui.button(
        label="Red", style=nextcord.ButtonStyle.red, custom_id="persistent_view:red"
    )
    async def red(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("This is red.", ephemeral=True)

    @nextcord.ui.button(
        label="Grey", style=nextcord.ButtonStyle.grey, custom_id="persistent_view:grey"
    )
    async def grey(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("This is grey.", ephemeral=True)


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persistent_views_added = False

    async def on_ready(self):
        if not self.persistent_views_added:
            # Register the persistent view for listening here.
            # Note that this does not send the view to any message.
            # To do that, you need to send a message with the View as shown below.
            # If you have the message_id you can also pass it as a keyword argument, but for this example
            # we don't have one.
            self.add_view(PersistentView())
            self.persistent_views_added = True

        print(f"Logged in as {self.user} (ID: {self.user.id})")


bot = Bot()


@bot.slash_command()
@application_checks.is_owner()
async def prepare(interaction):
    """Starts a persistent view."""
    # In order for a persistent view to be listened to, it needs to be sent to an actual message.
    # Call this method once just to store it somewhere.
    # In a more complicated program you might fetch the message_id from a database for use later.
    # However this is outside of the scope of this simple example.
    await interaction.send("What's your favourite colour?", view=PersistentView())


bot.run("token")
