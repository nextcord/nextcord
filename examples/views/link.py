import nextcord

from nextcord.ext import commands
from urllib.parse import quote_plus

# Define a simple View that gives us a google link button.
# We take in `query` as the query that the command author requests for
class Google(nextcord.ui.View):
    def __init__(self, query: str):
        super().__init__()
        # we need to quote the query string to make a valid url. Discord will raise an error if it isn't valid.
        query = quote_plus(query)
        url = f'https://www.google.com/search?q={query}'

        # Link buttons cannot be made with the decorator
        # Therefore we have to manually create one.
        # We add the quoted url to the button, and add the button to the view.
        self.add_item(nextcord.ui.Button(label='Click Here', url=url))


bot = commands.Bot(command_prefix='$')


@bot.command()
async def google(ctx, *, query: str):
    """Returns a google link for a query"""
    await ctx.send(f'Google Result for: `{query}`', view=Google(query))


bot.run('token')
