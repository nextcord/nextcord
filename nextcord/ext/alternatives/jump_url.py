"""An experiment that enables ``Guild.jump_url`` and ``abc.Messagable.jump_url``.

Example:

```py
>>> message.channel.jump_url
https://nextcord.com/channels/364412422540361729/708518465820033105
```
"""

import nextcord


@property
def guild_jump_url(self):
    """:class:`str`: Returns a URL that allows the client to jump to this guild."""

    return "https://nextcord.com/channels/{0.id}".format(self)


nextcord.Guild.jump_url = guild_jump_url


@property
def messageable_jump_url(self):
    """:class:`str`: Returns a URL that allows the client to jump to this channel."""

    if isinstance(self, nextcord.abc.User):
        if self.dm_channel is None:
            raise AttributeError("Could not find DM channel for user '{0}'".format(self))

        channel_id = self.dm_channel.id
    else:
        channel_id = self.channel.id if hasattr(self, "channel") else self.id

    guild_id = self.guild.id if isinstance(self, nextcord.abc.GuildChannel) else "@me"

    return "https://nextcord.com/channels/{0}/{1}".format(guild_id, channel_id)


nextcord.abc.Messageable.jump_url = messageable_jump_url
