import asyncio
from io import BytesIO
from traceback import format_exc
from typing import Dict, List, Optional, Union

import nextcord
from nextcord.ext import commands
from nextcord.voice_recording import (
    AUDIO_CHANNELS,
    AUDIO_HZ,
    AudioData,
    AudioFile,
    Formats,
    RecorderClient,
    Silence,
    get_ffmpeg_format,
)

bot = commands.Bot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# connect command
@bot.slash_command(
    description="Connect to your voice channel or a specified voice channel.",
    dm_permission=False,
    default_member_permissions=8,  # admins only
)
async def connect(
    interaction: nextcord.Interaction,
    channel: Optional[Union[nextcord.VoiceChannel, nextcord.StageChannel]] = None,
):
    assert interaction.guild
    assert isinstance(interaction.user, nextcord.Member)

    if interaction.guild.voice_client:
        await interaction.send("Voice is already connected.")
        return

    if channel:
        await channel.connect(recordable=True, prevent_leakage=True)
        await interaction.send(f"Connected to {channel.mention}")
        return

    author_voice: Optional[nextcord.VoiceState] = interaction.user.voice
    if author_voice and (channel := author_voice.channel):
        await author_voice.channel.connect(recordable=True, prevent_leakage=True)
        await interaction.send(f"Connected to your voice channel {channel.mention}")
        return

    await interaction.send("You are not in a voice channel, and no voice channel was specified.")


# start recording command
@bot.slash_command(
    description="Start recording in the connected voice channel.",
    dm_permission=False,
    default_member_permissions=8,  # admins only
)
async def start_recording(interaction: nextcord.Interaction):
    assert interaction.guild
    assert isinstance(interaction.user, nextcord.Member)

    voice_client = interaction.guild.voice_client

    if not voice_client:
        await interaction.send("I am not connected to a voice channel. Use `/connect`")
        return

    if not isinstance(voice_client, RecorderClient):
        await interaction.send("I am not connected with a recordable client.")
        return

    await voice_client.start_recording()
    await interaction.send(f"Recording started in {voice_client.channel}")


# slash options for available export formats
formats = nextcord.SlashOption(
    name="export_format",
    description="The format to export the recordings in.",
    choices=[e.name for e in Formats],
)


# merging audio
# TODO: move this to main lib
def merge_audio(audio_files: Dict[int, AudioFile], format: Formats) -> Optional[nextcord.File]:
    try:
        import pydub  # pip install pydub
    except ImportError:
        print("pydub is not installed. Install pydub with `pip install pydub`")

    if not audio_files or len(audio_files) == 1:
        return None

    # format all AudioFiles into AudioSegments
    segments: List[tuple[pydub.AudioSegment, Optional[Silence]]] = [
        (
            pydub.AudioSegment.from_file(
                f.fp,
                format=str(f.filename).rsplit(".", 1)[-1],
                sample_width=AUDIO_CHANNELS,
                frame_rate=AUDIO_HZ,
                channels=AUDIO_CHANNELS,
            ),
            f.starting_silence,
        )
        for f in audio_files.values()
    ]

    # get the first segment, which will have a starting silence of `None`
    index, first_segment = next(
        iter((i, seg[0]) for i, seg in enumerate(segments) if seg[1] is None)
    )
    del segments[index]

    # merge
    for seg, start in segments:
        first_segment = first_segment.overlay(seg, position=int(start.milliseconds) if start else 0)

    # export the merged track
    final = BytesIO()
    format_str = format.name.lower()
    first_segment.export(final, format=get_ffmpeg_format(format_str))

    # seek all tracks to start
    final.seek(0)
    for f in audio_files.values():
        f.fp.seek(0)

    return nextcord.File(final, f"merged.{format_str}", force_close=True)


# stop recording command
@bot.slash_command(
    description="Stop recording in the connected voice channel.",
    dm_permission=False,
    default_member_permissions=8,  # admins only
)
async def stop_recording(
    interaction: nextcord.Interaction,
    export_format: str = formats,
    merge: bool = True,  # requires pydub
):
    assert interaction.guild
    assert isinstance(interaction.user, nextcord.Member)

    voice_client = interaction.guild.voice_client

    if not voice_client:
        await interaction.send("I am not connected to a voice channel.")
        return

    if not isinstance(voice_client, RecorderClient):
        await interaction.send("I am not connected with a recordable client.")
        return

    try:
        await interaction.response.defer()
        recordings = await voice_client.stop_recording(
            export_format=getattr(Formats, export_format),
            write_remaining_silence=True,  # makes sure the first track will fill length
        )
        assert not isinstance(recordings, AudioData)
    except Exception:
        print(exc := format_exc())
        await interaction.send(
            f"An error occured when exporting the recording\n```\n{exc[:1900]}\n```"
        )
        return

    if not recordings:
        await interaction.send("Export was unavailable.")
        return

    if merge:
        m = await interaction.channel.send("Merging exported recordings...")  # type: ignore (interaction channel cannot be Forum/Category)
        file = await asyncio.get_running_loop().run_in_executor(  # run merge in executor to avoid blocking call
            None, merge_audio, recordings, getattr(Formats, export_format)
        )

        if file:
            try:
                await m.edit(
                    content=f"Merged recordings for users <@{'> <@'.join(str(i) for i in recordings)}>",
                    file=file,
                )
            except Exception:
                print(format_exc())
                await m.edit(content="Merged filesize may have been too large to send.")

        else:
            await m.edit("There weren't enough tracks to require merging.")

    try:
        await interaction.send(
            f"Recording stopped in {voice_client.channel}", files=list(recordings.values())
        )
    except Exception:
        print(format_exc())
        await interaction.send(
            f"Recording stopped in {voice_client.channel} but failed to upload. Files may have been too large."
        )


bot.run("token")
