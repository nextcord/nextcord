import nextcord
from nextcord.ext import commands

TESTING_GUILD_ID = 123456798  # Replace with your testing guild id


class Pet(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "Your pet",
            timeout=5 * 60,  # 5 minutes
        )

        self.name = nextcord.ui.TextInput(
            label="Your pet's name",
            min_length=2,
            max_length=50,
        )
        self.add_item(self.name)

        self.description = nextcord.ui.TextInput(
            label="Description",
            style=nextcord.TextInputStyle.paragraph,
            placeholder="Information that can help us recognise your pet",
            required=False,
            max_length=1800,
        )
        self.add_item(self.description)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        response = f"{interaction.user.mention}'s favourite pet's name is {self.name.value}."
        if self.description.value != "":
            response += (
                f"\nTheir pet can be recognized by this information:\n{self.description.value}"
            )
        await interaction.send(response)


bot = commands.Bot()


@bot.slash_command(
    name="pet",
    description="Describe your favourite pet",
    guild_ids=[TESTING_GUILD_ID],
)
async def send(interaction: nextcord.Interaction):
    modal = Pet()
    await interaction.response.send_modal(modal)


bot.run("token")
