import typing

import nextcord
from nextcord.ext import commands

intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", description="Nothing to see here!", intents=intents)


# the `hidden` keyword argument hides it from the help command.
@bot.group(hidden=True)
async def secret(ctx):
    """What is this "secret" you speak of?"""
    if ctx.invoked_subcommand is None:
        await ctx.send("Shh!", delete_after=5)


def create_overwrites(ctx, *objects):
    """This is just a helper function that creates the overwrites for the
    voice/text channels.

    A `nextcord.PermissionOverwrite` allows you to determine the permissions
    of an object, whether it be a `nextcord.Role` or a `nextcord.Member`.

    In this case, the `view_channel` permission is being used to hide the channel
    from being viewed by whoever does not meet the criteria, thus creating a
    secret channel.
    """

    # a dict comprehension is being utilised here to set the same permission overwrites
    # for each `nextcord.Role` or `nextcord.Member`.
    overwrites = {obj: nextcord.PermissionOverwrite(view_channel=True) for obj in objects}

    # prevents the default role (@everyone) from viewing the channel
    # if it isn't already allowed to view the channel.
    overwrites.setdefault(ctx.guild.default_role, nextcord.PermissionOverwrite(view_channel=False))

    # makes sure the client is always allowed to view the channel.
    overwrites[ctx.guild.me] = nextcord.PermissionOverwrite(view_channel=True)

    return overwrites


# since these commands rely on guild related features,
# it is best to lock it to be guild-only.
@secret.command()
@commands.guild_only()
async def text(ctx, name: str, *objects: typing.Union[nextcord.Role, nextcord.Member]):
    """This makes a text channel with a specified name
    that is only visible to roles or members that are specified.
    """

    overwrites = create_overwrites(ctx, *objects)

    await ctx.guild.create_text_channel(
        name,
        overwrites=overwrites,
        topic="Top secret text channel. Any leakage of this channel may result in serious trouble.",
        reason="Very secret business.",
    )


@secret.command()
@commands.guild_only()
async def voice(ctx, name: str, *objects: typing.Union[nextcord.Role, nextcord.Member]):
    """This does the same thing as the `text` subcommand
    but instead creates a voice channel.
    """

    overwrites = create_overwrites(ctx, *objects)

    await ctx.guild.create_voice_channel(
        name, overwrites=overwrites, reason="Very secret business."
    )


@secret.command()
@commands.guild_only()
async def emoji(ctx, emoji: nextcord.PartialEmoji, *roles: nextcord.Role):
    """This clones a specified emoji that only specified roles
    are allowed to use.
    """

    # fetch the emoji asset and read it as bytes.
    emoji_bytes = await emoji.read()

    # the key parameter here is `roles`, which controls
    # what roles are able to use the emoji.
    await ctx.guild.create_custom_emoji(
        name=emoji.name, image=emoji_bytes, roles=roles, reason="Very secret business."
    )


bot.run("token")
