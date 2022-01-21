import nextcord
from nextcord import Interaction, SlashOption

client = nextcord.Client()

list_of_dog_breeds = [  # the list of dog breeds
    "German Shepard",
    "Poodle",
    "Pug",
    "Shiba Inu",
]


@client.slash_command(guild_ids=[...])  # Limits guilds
async def your_favorite_dog(
    interaction: Interaction,
    dog: str = SlashOption(
        name="dog",  # the name
        description="Choose the best dog from this autocompleted list!",  # our description
    ),
):  # our slash option.
    await interaction.response.send_message(
        f"your favorite dog is {dog}!"
    )  # sends the autocompleted result


@your_favorite_dog.on_autocomplete("dog")
async def favorite_dog(interaction: Interaction, dog: str) -> None:
    if not dog:
        await interaction.response.send_autocomplete(list_of_dog_breeds)  # sending the list to discord.
        return

    results = [d for d in list_of_dog_breeds if d.lower().startswith(dog.lower())]
    await interaction.response.send_autocomplete(results)

client.run("TOKEN")
