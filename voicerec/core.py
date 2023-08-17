"""
The MIT License (MIT)

:copyright: (c) 2021-present Nextcord Developers

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""


import logging

from enum import Enum
from nextcord import VoiceClient, VoiceChannel, StageChannel
from nextcord.client import Client
from io import BufferedWriter, BytesIO
from typing import Optional, Union
from time import sleep, time as clock_timestamp
from threading import Thread
from select import select
from pathlib import Path
from os import makedirs
from os.path import dirname
from struct import unpack_from
from . import opus

from .errors import *
from . import decrypter

class Formats(Enum):
    MP3 = 0
    MP4 = 1
    M4A = 2
    MKA = 3
    MKV = 4
    OGG = 5
    PCM = 6
    WAV = 7

class TMPFile:
    def __init__(self, filepath) -> None:
        self.file = open(Path(filepath), "ab")

    def write(self, b: bytes):
        self.file.write(b)


class TempType(Enum):
    Memory = 0
    File = 1


ConnectableVoiceChannels = Union[VoiceChannel, StageChannel]


AUDIO_HZ = 48_000
SILENCE_TIMEFRAME = 960

STUB = ()


class TimeTracker:
    def __init__(self) -> None:
        self.starting_time: Optional[float] = clock_timestamp()  # Also used as filename
        self.first_packet_time: Optional[float] = None
        self.stopping_time: Optional[float] = None
        
        self.users_times: dict[int, float] = {}

    def add_user(self, user, start_time):
        if user not in self.users_times:
            self.users_times[user] = start_time
    
    def calculate_time_updates(self, user_id, timestamp, received_timestamp):
        ...  # TODO

def _open_tmp_file(guild_id, user_id):
    path = Path(f".rectmps/{guild_id}-{user_id}.tmp")

    try:
        return open(path, "ab")

    except FileNotFoundError:
        makedirs(dirname(path), exist_ok=True)  # Create missing dirs
        path.touch(exist_ok=True)  # create missing file
        return open(path, "ab")


class AudioWriter:
    def __init__(self, temp_type: TempType, guild_id: int, user_id: int) -> None:
        self.buffer: Union[BufferedWriter, BytesIO]
        if temp_type == TempType.File:
            self.buffer = _open_tmp_file(guild_id, user_id)
        elif temp_type == TempType.Memory:
            self.buffer = BytesIO()
        else:
            raise InvalidTempType("Arg `temp_type` must be of type TempType")
    
    def write(self, bytes):
        self.buffer.write(bytes)


class AudioData(dict):
    def get_writer(self, temp_type: TempType, guild_id: int, user_id: int) -> AudioWriter:
        return (
            self.get(user_id)
            or self.add_new_writer(
                user_id,
                AudioWriter(temp_type, guild_id, user_id)
            )
        )
    
    def add_new_writer(self, user_id: int, writer: AudioWriter) -> AudioWriter:
        self[user_id] = writer
        return writer

    def append(self, temp_type: TempType, guild_id: int, user_id: int, data: bytes):
        writer = self.get_writer(temp_type, guild_id, user_id)
        writer.write(data)


class RecorderClient(VoiceClient):
    def __init__(
        self, client: Client,
        channel: ConnectableVoiceChannels,
        auto_deaf: bool = True,
        temp_type: TempType = TempType.File
    ) -> None:

        super().__init__(client, channel)
        self.channel: ConnectableVoiceChannels

        self.time_tracker: Optional[TimeTracker] = None
        self.audio_data: Optional[AudioData] = None

        self.process: Optional[Thread] = None
        self.auto_deaf: bool = auto_deaf
        self.temp_type: TempType = temp_type


    async def voice_connect(self) -> None:
        await self.channel.guild.change_voice_state(
            channel=self.channel,
            self_deaf=True if self.auto_deaf else False
        )


    # recording stuff

    def _process_decoded_audio(
        self,
        sequence: int,
        timestamp: float,
        received_timestamp: float,
        ssrc: int, decoded_data: bytes
    ):
        print(type(decoded_data), type(sequence), type(timestamp), type(ssrc))
        if self.audio_data is None or self.time_tracker is None or not self.guild:
            return

        ssrc_cache = self.ws.ssrc_cache
        while not (user_data := ssrc_cache.get(ssrc)):
            sleep(0.05)

        self.audio_data.append(
            self.temp_type,
            self.guild.id,
            (user_id := user_data["user_id"]),
            decoded_data
        )

        self.time_tracker.calculate_time_updates(user_id, timestamp, received_timestamp)

    def _decode_audio(self, data):
        if 200 <= data[1] <= 204:
            return  # RTCP concention info, not useful

        data = bytearray(data)

        header = data[:12]
        data = data[12:]

        sequence, timestamp, ssrc = unpack_from(">xxHII", header)

        decrypted_data = getattr(
            decrypter,
            f"decrypt_{self.mode}"
        )(self.secret_key, header, data)
        
        if decrypted_data == b"\xf8\xff\xfe":  # frame of silence
            return

        # decoder will call `_process_decoded_audio` once finished decoding
        self.decoder.decode((sequence, timestamp, clock_timestamp(), ssrc, decrypted_data))

    def _process_audio_packet(self, data):
        if self.audio_data is None:
            return

        self._decode_audio(data)

    def _start_packets_recording(self) -> Optional[tuple[TimeTracker, dict]]:
        self.time_tracker = TimeTracker()
        self.audio_data = AudioData()

        pre_socket = [self.socket]

        while self.time_tracker:
            ready, _, error = select(pre_socket, STUB, pre_socket, 0.01)
            if not ready:
                if error:
                    logging.debug(f"Socket Error: {error}")
                continue
            
            try:
                self._process_audio_packet(self.socket.recv(4096))
            except OSError:
                return self._stop_recording()


    def _start_recording(self) -> Thread:
        self.decoder = opus.DecoderThread(self)
        self.decoder.start()

        self.process = Thread(
            target=self._start_packets_recording
        )
        self.process.start()
        return self.process

    async def start_recording(self, channel: Optional[ConnectableVoiceChannels] = None) -> Thread:
        if self.time_tracker:
            raise OngoingRecordingError(f"A recording has already started at {self.time_tracker.starting_time}")
        
        if channel:
            self.channel = channel
            await self.voice_connect()

        if not self.is_connected():
            raise NotConnectedError("Not connected to a voice channel.")

        return self._start_recording()

    def _stop_recording(self, ) -> tuple[TimeTracker, dict]:
        if not (time_tracker := self.time_tracker):  # stops the recording loop
            raise NotRecordingError(f"There is no ongoing recording to stop.")
        self.time_tracker = None

        if (audio_data := self.audio_data) is None:
            raise TempNotFound("Audio data not found!")
        self.audio_data = None

        ...

        return time_tracker, audio_data

    async def stop_recording(self, ):  # TODO: TempFile that gets deleted, should superclass nextcord.File
        ...
