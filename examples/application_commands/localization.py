
from nextcord import Interaction, Locale, SlashOption
from nextcord.ext import commands


TESTING_GUILD_ID = 123456789  # Replace with your testing guild id
BOT_TOKEN = ""                # Replace with your bot token


bot = commands.Bot()


@bot.slash_command(
    name="hello",              # name of the command by default in English
    name_localizations={
        Locale.de : "hallo",   # localization for the name of the command in German (Deutsch)
        Locale.fr : "bonjour", # localization for the name of the command in French (Français)
        Locale.es_ES : "hola"  # localization for the name of the command in Spanish (Español)
    },
    description="Description of the command in English",      # description of the command by default in English
    description_localizations={
        Locale.de : "Beschreibung des Befehls auf Deutsch",   # localization for the description of the command in German (Deutsch)
        Locale.fr : "Description de la commande en français", # localization for the description of the command in French (Français)
        Locale.es_ES : "Descripción del comando en español"   # localization for the description of the command in Spanish (Español)
    },
    guild_ids=[TESTING_GUILD_ID]
)
async def hello_command(interaction: Interaction):

    # interaction.locale is the user's locale (language set by user in the discord app)

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
        Locale.en_US : "color",
        Locale.de : "farbe",
        Locale.fr : "couleur",
        Locale.es_ES: "color"
    },
    guild_ids=[TESTING_GUILD_ID]
)
async def choose_colour_command(
    interaction: Interaction,
    colour: str = SlashOption(
        name="colour",              # name for the argument "colour" by default in English
        name_localizations={
            Locale.en_US : "color", # localization for the name of the argument "colour" in US English
            Locale.de : "farbe",    # localization for the name of the argument "colour" in German (Deutsch)
            Locale.fr : "couleur",  # localization for the name of the argument "colour" in French (Français)
            Locale.es_ES: "color"   # localization for the name of the argument "colour" in Spanish (Español)
        },
        description="Choose the colour",         # description of the argument by default in English
        description_localizations={
            Locale.en_US : "Choose the color",   # localization of the description in US English
            Locale.de : "Wählen Sie die Farbe",  # localization of the description in German (Deutsch)
            Locale.fr : "Choisissez la couleur", # localization of the description in French (Français)
            Locale.es_ES : "Elige el color"      # localization of the description in Spanish (Español)
        },
        choices=["Red", "Green", "Blue"], # available colours by default in English
        choice_localizations={
            "Red" : {
                Locale.de : "Rot",        # localization for the red colour in German (Deutsch)
                Locale.fr : "Rouge",      # localization for the red colour in French (Français)
                Locale.es_ES: "Rojo"      # localization for the red colour in Spanish (Español)
            },
            "Green" : {
                Locale.de : "Grün",       # localization for the green colour in German (Deutsch)
                Locale.fr : "Vert",       # localization for the green colour in French (Français)
                Locale.es_ES: "Verde"     # localization for the green colour in Spanish (Español)
            },
            "Blue" : {
                Locale.de : "Blau",       # localization for the blue colour in German (Deutsch)
                Locale.fr : "Bleu",       # localization for the blue colour in French (Français)
                Locale.es_ES: "Azul"      # localization for the blue colour in Spanish (Español)
            }
        }
    )
):
    if interaction.locale == "en-US":
        await interaction.response.send_message(f"You chose **`{colour}`** color")
    elif interaction.locale == "de":
        await interaction.response.send_message(f"Sie haben **`{colour}`** Farbe gewählt")
    elif interaction.locale == "fr":
        await interaction.response.send_message(f"Vous avez choisi la couleur rouge **`{colour}`**")
    elif interaction.locale == "es-ES":
        await interaction.response.send_message(f"Elegiste el color **`{colour}`**")
    else:
        await interaction.response.send_message(f"You chose **`{colour}`** colour")


bot.run(BOT_TOKEN)