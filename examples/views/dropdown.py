import nextcord
from nextcord.ext import commands


# Defines a custom Select containing colour options
# that the user can choose. The callback function
# of this class is called when the user changes their choice
class Dropdown(nextcord.ui.Select):
    def __init__(self):

        # Set the options that will be presented inside the dropdown
        options = [
            nextcord.SelectOption(
                label="Red", description="Your favourite colour is red", emoji="🟥"
            ),
            nextcord.SelectOption(
                label="Green", description="Your favourite colour is green", emoji="🟩"
            ),
            nextcord.SelectOption(
                label="Blue", description="Your favourite colour is blue", emoji="🟦"
            ),
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Choose your favourite colour...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: nextcord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        await interaction.response.send_message(f"Your favourite colour is {self.values[0]}")


class DropdownView(nextcord.ui.View):
    def __init__(self):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Dropdown())


bot = commands.Bot()


@bot.slash_command()
async def colour(interaction):
    """Sends a message with our dropdown containing colours"""

    # Create the view containing our dropdown
    view = DropdownView()

    # Sending a message containing our view
    await interaction.send("Pick your favourite colour:", view=view)


bot.run("token")
