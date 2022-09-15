from nextcord import Interaction, SlashOption
from nextcord.ext import commands

TESTING_GUILD_ID = 123456789  # Replace with your testing guild id

bot = commands.Bot()

list_of_dog_breeds = [
    "German Shepard",
    "Poodle",
    "Pug",
    "Shiba Inu",
]


@bot.slash_command(guild_ids=[TESTING_GUILD_ID])
async def your_favorite_dog(
    interaction: Interaction,
    dog: str = SlashOption(
        name="dog",
        description="Choose the best dog from this autocompleted list!",
    ),
):
    # sends the autocompleted result
    await interaction.response.send_message(f"Your favorite dog is {dog}!")


@your_favorite_dog.on_autocomplete("dog")
async def favorite_dog(interaction: Interaction, dog: str):
    if not dog:
        # send the full autocomplete list
        await interaction.response.send_autocomplete(list_of_dog_breeds)
        return
    # send a list of nearest matches from the list of dog breeds
    get_near_dog = [breed for breed in list_of_dog_breeds if breed.lower().startswith(dog.lower())]
    await interaction.response.send_autocomplete(get_near_dog)


bot.run("token")
