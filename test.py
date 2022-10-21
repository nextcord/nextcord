import nextcord
from nextcord.ext import commands

bot = commands.Bot(
    command_prefix=commands.when_mentioned, case_insensitive=True, intents=nextcord.Intents.all()
)


class TestView(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @nextcord.ui.user_select(
        placeholder="Select a user", custom_id="user_select", min_values=1, max_values=5
    )
    async def user_select(self, select, interaction):
        users = await select.values.fetch(interaction.guild)
        mentions = [user.mention for user in users]
        await interaction.send(
            f'You selected {", ".join(mentions)}', allowed_mentions=nextcord.AllowedMentions.none()
        )

    @nextcord.ui.role_select(
        placeholder="Select a role", custom_id="role_select", min_values=1, max_values=5
    )
    async def role_select(self, select, interaction):
        roles = await select.values.fetch(interaction.guild)
        mentions = [role.mention for role in roles]
        await interaction.send(
            f'You selected {", ".join(mentions)}', allowed_mentions=nextcord.AllowedMentions.none()
        )

    @nextcord.ui.mentionable_select(
        placeholder="Select a mentionable",
        custom_id="mentionable_select",
        min_values=1,
        max_values=5,
    )
    async def mentionable_select(self, select, interaction):
        mentionables = await select.values.fetch(interaction.guild)
        mentions = [mentionable.mention for mentionable in mentionables]
        await interaction.send(
            f'You selected {", ".join(mentions)}', allowed_mentions=nextcord.AllowedMentions.none()
        )

    @nextcord.ui.channel_select(
        placeholder="Select a channel", custom_id="channel_select", min_values=1, max_values=5
    )
    async def channel_select(self, select, interaction):
        channels = await select.values.fetch(interaction.guild)
        mentions = [channel.mention for channel in channels]
        await interaction.send(
            f'You selected {", ".join(mentions)}', allowed_mentions=nextcord.AllowedMentions.none()
        )

    @nextcord.ui.channel_select(
        placeholder="Select a text channel",
        custom_id="text_channel_select",
        min_values=1,
        max_values=5,
        channel_types=[nextcord.ChannelType.text],
    )
    async def text_channel_select(self, select, interaction):
        channels = await select.values.fetch(interaction.guild)
        mentions = [channel.mention for channel in channels]
        await interaction.send(
            f'You selected {", ".join(mentions)}', allowed_mentions=nextcord.AllowedMentions.none()
        )


@bot.command()
async def test(ctx):
    await ctx.send("Hello", view=TestView(bot))


bot.run("ODgxMTU1MzM2Njg0MzM5MjQw.YSot2w.0bP2gDueBy5MLk5FYNJxMviY9e4")
