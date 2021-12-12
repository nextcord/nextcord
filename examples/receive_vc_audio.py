import os

import nextcord
import nextcord.ext.commands as commands
import nextcord.ext.voicerecording as voicerecording

bot = commands.Bot(command_prefix=commands.when_mentioned_or("$"), intents=nextcord.Intents.all())
bot.connections = {}


async def get_vc(message: nextcord.Message):
    """Finds the corresponding VC to a message user or generates a new one"""
    vc = message.author.voice
    if not vc:
        await message.channel.send("You're not in a vc right now")
        return
    connection = bot.connections.get(message.guild.id)
    if connection:
        if connection.channel.id == message.author.voice.channel.id:
            return connection

        await connection.move_to(vc.channel)
        return connection
    else:
        vc = await vc.channel.connect()
        bot.connections.update({message.guild.id: vc})
        return vc


async def finished_callback(sink: voicerecording.FileSink, channel, *args):
    # Note: sink.audio_data = {user_id: AudioData}
    recorded_users = [f" <@{str(user_id)}> ({os.path.split(audio.file)[1]}) " for user_id, audio in
                      sink.audio_data.items()]
    await channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.")
    for f in sink.get_files():
        print(f)
        await channel.send(file=nextcord.File(f, f, spoiler=True))
    sink.destroy()


@bot.command(name="record", aliases=["start_recording", "start"])
async def start(ctx: commands.Context, time: int = 0, size: int = 1000000):
    # please note: There is an upload limit for Files, so it is suggested to have a low enough size
    vc = await get_vc(ctx.message)
    await vc.start_listening(
        voicerecording.FileSink(encoding=voicerecording.wav_encoder, filters={'time': time, 'max_size': size}),
        finished_callback, [ctx.channel])
    await ctx.reply("The recording has started!")


@bot.command(name="pause", aliases=["pause_recording", "toggle"])
async def pause(ctx: commands.Context):
    vc = await get_vc(ctx.message)
    await vc.toggle_listening_pause()
    await ctx.reply(f"The recording has been {'paused' if vc.listening_paused else 'unpaused'}")


@bot.command(name="stop", aliases=["stop_recording", "end"])
async def stop(ctx: commands.Context):
    vc = await get_vc(ctx.message)
    print("stopping")
    await vc.stop_listening()


@bot.listen
async def on_voice_state_update(self, member, before, after):
    if member.id != self.user.id:
        return
    # Filter out updates other than when we leave a channel we're connected to
    if member.guild.id not in self.connections or (not before.channel and after.channel) or (
            before.channel == after.channel):
        return
    del self.connections[member.guild.id]
    print("Disconnected")


if __name__ == '__main__':
    voicerecording.cleanuptempdir()
    bot.run('token')
