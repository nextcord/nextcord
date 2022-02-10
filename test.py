import nextcord
from nextcord.ui.modal import Modal
from nextcord.ui.text_input import TextInput

bot = nextcord.Client()

@bot.event
async def on_ready():
    global modal_test
    print("ready")
    modal_test = ModalTest()
    bot.add_modal(modal_test)

class ModalTest(Modal):
    def __init__(self):
        super().__init__(
            "Test",
            timeout=None,
            custom_id="test",
            test=TextInput(
                label="Test",
                custom_id="test_message"
            )
        )
    
    async def callback(self, interaction: nextcord.Interaction):
        await interaction.send(f"Your name : {self.test.value}")

@bot.slash_command(
    name="test",
    description="A command made for tests",
    guild_ids=[941014823574061087]
)
async def test(inter: nextcord.Interaction):
    await inter.response.send_modal(
        modal_test
    )

bot.run("OTQxMDE1MjIyNDE0NjM5MTI1.YgPyuA.-6Lq5fQNyIVA7cDvcIb2OITWUOg")