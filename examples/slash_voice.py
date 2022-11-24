# This is here to show how to use voice with slash commands

import asyncio

import nextcord
import youtube_dl
from nextcord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""


ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    "source_address": "0.0.0.0",
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(nextcord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(nextcord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voiceClient = None
        self.paused = False

    @nextcord.slash_command(description="Joins a voice channel")
    async def join(self, interaction: nextcord.Interaction, *, channel: nextcord.VoiceChannel):
        """Joins a voice channel"""

        try:
            self.voiceClient = await channel.connect()
        except nextcord.errors.ApplicationInvokeError:
            await self.voiceClient.disconnect()
            self.voiceClient = await channel.connect()
        await interaction.send(f"Joined {channel.name}")

    @nextcord.slash_command(description="Plays a file from the local filesystem")
    async def play(self, interaction: nextcord.Interaction, *, query):
        """Plays a file from the local filesystem"""

        if self.voiceClient is None:
            if interaction.user.voice:
                await self.join(interaction, channel=interaction.user.voice.channel)
            else:
                await interaction.send("You are not connected to a voice channel.")
                raise commands.CommandError(
                    "Author not connected to a voice channel.")
        source = nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(query))
        self.voiceClient.play(source, after=lambda e: print(
            f"Player error: {e}") if e else None)

        await interaction.send(f"Now playing: {query}")

    @nextcord.slash_command(description="Plays from a URL (almost anything youtube_dl supports)")
    async def yt(self, interaction: nextcord.Interaction, *, url):
        """Plays from a URL (almost anything youtube_dl supports)"""

        if self.voiceClient is None:
            if interaction.user.voice:
                await self.join(interaction, channel=interaction.user.voice.channel)
            else:
                await interaction.send("You are not connected to a voice channel.")
                raise commands.CommandError(
                    "Author not connected to a voice channel.")
        async with interaction.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            self.voiceClient.play(
                player, after=lambda e: print(
                    f"Player error: {e}") if e else None
            )

        await interaction.send(f"Now playing: {player.title}")

    @nextcord.slash_command(description="Streams from a URL (same as yt, but doesn't predownload)")
    async def stream(self, interaction: nextcord.Interaction, *, url):
        """Streams from a URL (same as yt, but doesn't predownload)"""

        if self.voiceClient is None:
            if interaction.user.voice:
                await self.join(interaction, channel=interaction.user.voice.channel)
            else:
                await interaction.send("You are not connected to a voice channel.")
                raise commands.CommandError(
                    "Author not connected to a voice channel.")
        elif self.voiceClient.is_playing():
            self.voiceClient.stop()
        async with interaction.channel.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            self.voiceClient.play(
                player, after=lambda e: print(
                    f"Player error: {e}") if e else None
            )

        await interaction.send(f"Now playing: {player.title}")

    @nextcord.slash_command(description="Changes the player's volume")
    async def volume(self, interaction: nextcord.Interaction, volume: int):
        """Changes the player's volume"""

        if self.voiceClient is None:
            return await interaction.send("Not connected to a voice channel.")

        self.voiceClient.source.volume = volume / 100
        await interaction.send(f"Changed volume to {volume}%")

    @nextcord.slash_command(description="Pauses music playback")
    async def pause(self, interaction: nextcord.Interaction):
        """Pauses music playback"""

        if self.voiceClient.is_playing():
            self.paused = True
            self.voiceClient.pause()
            await interaction.send("Paused.")
        else:
            await interaction.send("There isn't any music to pause.")

    @nextcord.slash_command(description="Resumes playing on voice")
    async def resume(self, interaction: nextcord.Interaction):
        """Resumes music playback"""

        async with interaction.channel.typing():
            pass
        if self.paused:
            self.voiceClient.resume()
            await interaction.send("Resumed.")
            self.paused = False
        else:
            await interaction.send("There isn't any music to resume.")

    @nextcord.slash_command(description="Stops and disconnects the bot from voice")
    async def stop(self, interaction: nextcord.Interaction):
        """Stops and disconnects the bot from voice"""

        await self.voiceClient.disconnect()
        await interaction.send("Disconnected.")


intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents)


bot.add_cog(Music(bot))
bot.run("token")
