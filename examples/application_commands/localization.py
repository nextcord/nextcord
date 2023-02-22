from nextcord import Interaction, Locale, SlashOption
from nextcord.ext import commands

TESTING_GUILD_ID = 123456789  # Replace with your testing guild id


bot = commands.Bot()


@bot.slash_command(
    name="hello",
    name_localizations={
        Locale.de: "hallo",
        Locale.fr: "bonjour",
        Locale.es_ES: "hola",
    },
    description="Description of the command in English",
    description_localizations={
        Locale.de: "Beschreibung des Befehls auf Deutsch",
        Locale.fr: "Description de la commande en français",
        Locale.es_ES: "Descripción del comando en español",
    },
    guild_ids=[TESTING_GUILD_ID],
)
async def hello_command(interaction: Interaction):
    if interaction.locale == "de":
        await interaction.response.send_message("Hallo Welt!")
    elif interaction.locale == "fr":
        await interaction.response.send_message("Bonjour le monde!")
    elif interaction.locale == "es-ES":
        await interaction.response.send_message("¡Hola Mundo!")
    else:
        await interaction.response.send_message("Hello, world!")


@bot.slash_command(
    name="colour",
    name_localizations={
        Locale.en_US: "color",
        Locale.de: "farbe",
        Locale.fr: "couleur",
        Locale.es_ES: "color",
    },
    guild_ids=[TESTING_GUILD_ID],
)
async def choose_colour_command(
    interaction: Interaction,
    colour: str = SlashOption(
        name="colour",
        name_localizations={
            Locale.en_US: "color",
            Locale.de: "farbe",
            Locale.fr: "couleur",
            Locale.es_ES: "color",
        },
        description="Choose the colour",
        description_localizations={
            Locale.en_US: "Choose the color",
            Locale.de: "Wählen Sie die Farbe",
            Locale.fr: "Choisissez la couleur",
            Locale.es_ES: "Elige el color",
        },
        choices=["Red", "Green", "Blue"],
        choice_localizations={
            "Red": {
                Locale.de: "Rot",
                Locale.fr: "Rouge",
                Locale.es_ES: "Rojo",
            },
            "Green": {
                Locale.de: "Grün",
                Locale.fr: "Vert",
                Locale.es_ES: "Verde",
            },
            "Blue": {
                Locale.de: "Blau",
                Locale.fr: "Bleu",
                Locale.es_ES: "Azul",
            },
        },
    ),
):
    if interaction.locale == "en-US":
        await interaction.response.send_message(f"You chose **`{colour}`** color")
    elif interaction.locale == "de":
        await interaction.response.send_message(f"Du hast **`{colour}`** Farbe gewählt")
    elif interaction.locale == "fr":
        await interaction.response.send_message(f"Tu as choisi la couleur **`{colour}`**")
    elif interaction.locale == "es-ES":
        await interaction.response.send_message(f"Elegiste el color **`{colour}`**")
    else:
        await interaction.response.send_message(f"You chose **`{colour}`** colour")


bot.run("token")
