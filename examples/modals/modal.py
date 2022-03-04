import nextcord
from nextcord.ext import commands

TESTING_GUILD_ID = 123456798  # Replace with your testing guild id

class Pet(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "Your pet",
            timeout=5*60, # 5 minutes
        )
        self.name = nextcord.ui.TextInput(
            label="Your pet's name",
            max_length=50,
        )
        self.description = nextcord.ui.TextInput(
            label="Description",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="Information that can help us recognise your pet",
            required=False,
            max_length=1800,
        )
        self.add_item(self.name)
        self.add_item(self.description)
    
    async def callback(self, inter: nextcord.Interaction) -> None:
        response = f"{inter.user.mention} favourite pet's name is {self.name.value}."
        if self.description.value != "":
            response += f"\nTheir pet can be recognized by this information:\n{self.description.value}"
        await inter.send(response)

bot = commands.Bot()

@bot.slash_command(
    name="pet",
    description="Describe your favourite pet",
    guild_ids=[TESTING_GUILD_ID],
)
async def send(inter: nextcord.Interaction):
    modal = Pet()
    await inter.response.send_modal(modal)

bot.run("token")