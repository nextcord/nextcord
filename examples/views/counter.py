import nextcord

from nextcord.ext import commands


# Define a simple View that gives us a counter button
class Counter(nextcord.ui.View):

    # Define the actual button
    # When pressed, this increments the number displayed until it hits 5.
    # When it hits 5, the counter button is disabled and it turns green.
    # note: The name of the function does not matter to the library
    @nextcord.ui.button(label='0', style=nextcord.ButtonStyle.red)
    async def count(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        number = int(button.label) if button.label else 0
        if number >= 4:
            button.style = nextcord.ButtonStyle.green
            button.disabled = True
        button.label = str(number + 1)

        # Make sure to update the message with our updated selves
        await interaction.response.edit_message(view=self)


bot = commands.Bot(command_prefix='$')


@bot.command()
async def counter(ctx):
    """Starts a counter for pressing."""
    await ctx.send('Press!', view=Counter())


bot.run('token')
