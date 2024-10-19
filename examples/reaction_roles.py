# This example requires the 'members' privileged intents
import nextcord
from nextcord.ext import commands


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.role_message_id = 0  # ID of the message that can be reacted to to add/remove a role.
        self.emoji_to_role = {
            nextcord.PartialEmoji(
                name="🔴"
            ): 0,  # ID of the role associated with unicode emoji '🔴'.
            nextcord.PartialEmoji(
                name="🟡"
            ): 0,  # ID of the role associated with unicode emoji '🟡'.
            nextcord.PartialEmoji(
                name="green", id=0
            ): 0,  # ID of the role associated with a partial emoji's ID.
        }

    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        """Gives a role based on a reaction emoji."""
        # Make sure that the message the user is reacting to is the one we care about.
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            # Check if we're still in the guild and it's cached.
            return

        try:
            role_id = self.emoji_to_role[payload.emoji]
        except KeyError:
            # If the emoji isn't the one we care about then exit as well.
            return

        role = guild.get_role(role_id)
        if role is None:
            # Make sure the role still exists and is valid.
            return

        try:
            # Finally, add the role.
            await payload.member.add_roles(role)
        except nextcord.HTTPException:
            # If we want to do something in case of errors we'd do it here.
            pass

    async def on_raw_reaction_remove(self, payload: nextcord.RawReactionActionEvent):
        """Removes a role based on a reaction emoji."""
        # Make sure that the message the user is reacting to is the one we care about.
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            # Check if we're still in the guild and it's cached.
            return

        try:
            role_id = self.emoji_to_role[payload.emoji]
        except KeyError:
            # If the emoji isn't the one we care about then exit as well.
            return

        role = guild.get_role(role_id)
        if role is None:
            # Make sure the role still exists and is valid.
            return

        # The payload for `on_raw_reaction_remove` does not provide `.member`
        # so we must get the member ourselves from the payload's `.user_id`.
        member = guild.get_member(payload.user_id)
        if member is None:
            # Make sure the member still exists and is valid.
            return

        try:
            # Finally, remove the role.
            await member.remove_roles(role)
        except nextcord.HTTPException:
            # If we want to do something in case of errors we'd do it here.
            pass


intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = Bot(command_prefix="$", intents=intents)
bot.run("token")
