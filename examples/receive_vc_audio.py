import nextcord
import os


def vc_required(func):
    async def get_vc(self, msg: nextcord.Message):
        vc = await self.get_vc(msg)
        if not vc:
            return
        await func(self, msg, vc)
    return get_vc


def args_to_filters(args):
    filters = {}
    if '--time' in args:
        index = args.index('--time')
        try:
            seconds = args[index+1]
        except IndexError:
            return "You must provide an amount of seconds for the time."
        try:
            seconds = int(seconds)
        except ValueError:
            return "You must provide an integer value."
        filters.update({'time': seconds})
    if '--users' in args:
        users = []
        index = args.index('--users')+1
        while True:
            try:
                users.append(int(args[index]))
            except IndexError:
                break
            except ValueError:
                break
            index += 1
        if not users:
            return "You must provide at least one user, or multiple users separated by spaces."
        filters.update({'users': users})
    return filters


def get_encoding(args):
    if '--output' in args:
        index = args.index('--output')
        return args[index+1].lower()
    else:
        return 'wav'


class Client(nextcord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connections = {voice.guild.id: voice for voice in self.voice_clients}
        self.playlists = {}

        self.commands = {
            '$start': self.start_recording,
            '$stop': self.stop_recording,
            '$pause': self.toggle_pause,
        }

    async def get_vc(self, message: nextcord.Message):
        vc = message.author.voice
        if not vc:
            await message.channel.send("You're not in a vc right now")
            return
        connection = self.connections.get(message.guild.id)
        if connection:
            if connection.channel.id == message.author.voice.channel.id:
                return connection

            await connection.move_to(vc.channel)
            return connection
        else:
            vc = await vc.channel.connect()
            self.connections.update({message.guild.id: vc})
            return vc

    async def on_message(self, msg):
        if not msg.content:
            return
        cmd = msg.content.split()[0]
        if cmd in self.commands:
            await self.commands[cmd](msg)

    @vc_required
    async def start_recording(self, msg, vc):
        args = msg.content.split()[1:]
        filters = args_to_filters(args)
        if type(filters) == str:
            return await msg.channel.send(filters)
        encoding = get_encoding(args)
        if encoding is None:
            return await msg.channel.send("You must provide a valid output encoding.")

        vc.start_recording(nextcord.Sink(encoding=nextcord  .Encodings(encoding), filters=filters), self.finished_callback, msg.channel)

        await msg.channel.send("The recording has started!")

    @vc_required
    async def toggle_pause(self, msg, vc):
        vc.pause_recording()
        await msg.channel.send(f"The recording has been {'paused' if vc.recording_paused else 'unpaused'}")

    @vc_required
    async def stop_recording(self, msg, vc):
        print("stopping")
        vc.stop_recording()

    async def finished_callback(self, sink: nextcord.Sink, channel, *args):
        # Note: sink.audio_data = {user_id: AudioData}
        recorded_users = [f" <@{str(user_id)}> ({os.path.split(audio.file)[1]}) " for user_id, audio in sink.audio_data.items()]
        await channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.")
        for f in sink.get_files():
            print(f)
            await channel.send(file=nextcord.File(f, f, spoiler=True))
        sink.destroy()

    async def on_voice_state_update(self, member, before, after):
        if member.id != self.user.id:
            return
        # Filter out updates other than when we leave a channel we're connected to
        if member.guild.id not in self.connections or (not before.channel and after.channel):
            return

        del self.connections[member.guild.id]
        print("Disconnected")


if __name__ == "__main__":
    nextcord.cleanuptempdir()
    intents = nextcord.Intents.default()
    client = Client(intents=intents)
    client.run('token')
