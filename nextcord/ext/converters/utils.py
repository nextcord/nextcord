from nextcord import Client


def get_from_guilds(bot: Client, getter, argument):
    result = None
    for guild in bot.guilds:
        result = getattr(guild, getter)(argument)
        if result:
            return result
    return result