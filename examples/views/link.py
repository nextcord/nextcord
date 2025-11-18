from urllib.parse import quote_plus

import nextcord
from nextcord.ext import commands


# Define a simple View that gives us a google link button.
# We take in `query` as the query that the command author requests for
class Google(nextcord.ui.View):
    def __init__(self, query: str):
        super().__init__()
        # We need to quote the query string to make a valid URL. Discord will raise an error if it isn't valid.
        query = quote_plus(query)
        url = f"https://www.google.com/search?q={query}"

        # Link buttons cannot be made with the decorator
        # Therefore we have to manually create one.
        # We add the quoted URL to the button, and add the button to the view.
        self.add_item(nextcord.ui.Button(label="Click Here", url=url))


bot = commands.Bot()


@bot.slash_command()
async def google(interaction, query: str):
    """Returns a google link for a query"""
    await interaction.send(f"Google Result for: `{query}`", view=Google(query))


bot.run("token")
