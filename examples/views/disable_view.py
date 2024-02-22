import nextcord
from nextcord import Interaction
from nextcord.ext import commands

bot = commands.Bot()


class MyView(nextcord.ui.View):
    message: nextcord.Message

    def __init__(self):
        # Set a timeout of 30 seconds, after which `on_timeout` will be called
        super().__init__(timeout=30.0)

    async def on_timeout(self):
        # Once the view times out, we disable the first button and remove the second button
        self.disable_button.disabled = True
        self.remove_item(self.remove_button)

        # make sure to update the message with the new buttons
        await self.message.edit(view=self)

    @nextcord.ui.button(label="Disable the view", style=nextcord.ButtonStyle.grey)
    async def disable_button(self, button: nextcord.ui.Button, interaction: Interaction):
        # We disable every single component in this view
        for child in self.children:
            if isinstance(child, nextcord.ui.Button):
                child.disabled = True
        # make sure to update the message with the new buttons
        await interaction.response.edit_message(view=self)

        # Prevents on_timeout from being triggered after the buttons are disabled
        self.stop()

    @nextcord.ui.button(label="Remove the view", style=nextcord.ButtonStyle.red)
    async def remove_button(self, button: nextcord.ui.Button, interaction: Interaction):
        # view=None removes the view
        await interaction.response.edit_message(view=None)

        # Prevents on_timeout from being triggered after the view is removed
        self.stop()


@bot.slash_command()
async def my_view(interaction: Interaction):
    # Create our view
    view = MyView()

    # Send a message with the view
    message = await interaction.send("These buttons will be disabled or removed!", view=view)

    # Assign the message to the view, so that we can use it in on_timeout to edit it
    view.message = message


bot.run("token")
