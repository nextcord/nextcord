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
from io import BufferedWriter, BytesIO
from os import makedirs
from os.path import dirname
from pathlib import Path
from select import select
from struct import pack, unpack_from
from threading import Thread
from time import perf_counter, sleep, time as clock_timestamp
from typing import Optional, Union

from nextcord import File, StageChannel, VoiceChannel, VoiceClient
from nextcord.client import Client

from . import decrypter, exporters, opus
from .errors import *


class Formats(Enum):
    MP3 = 0
    MP4 = 1
    M4A = 2
    MKA = 3
    MKV = 4
    OGG = 5
    PCM = 6
    WAV = 7


formats = {
    Formats.MP3: "export_as_MP3",
    Formats.MP4: "export_as_MP4",
    Formats.M4A: "export_as_M4A",
    Formats.MKA: "export_as_MKA",
    Formats.MKV: "export_as_MKV",
    Formats.OGG: "export_as_OGG",
    Formats.PCM: "export_as_PCM",
    Formats.WAV: "export_as_WAV",
}


class TempType(Enum):
    Memory = 0
    File = 1


ConnectableVoiceChannels = Union[VoiceChannel, StageChannel]


AUDIO_HZ = 48_000
SILENCE_FRAME_SIZE = 960
FRAME_OF_SILENCE = b"\xf8\xff\xfe"
DIFFERENCE_THRESHOLD = 60

STUB = ()


SILENCE_STRUCT = pack("<h", 0) * SILENCE_FRAME_SIZE
SILENCE_STRUCT_10 = SILENCE_STRUCT * 10
SILENCE_STRUCT_100 = SILENCE_STRUCT * 100
SILENCE_STRUCT_1000 = SILENCE_STRUCT * 1000  # 3.4mb in size


class Silence:
    def __init__(self, frames: int) -> None:
        self.frames: int = frames

    def write_to(self, buffer: Union[BufferedWriter, BytesIO]) -> None:
        write = buffer.write
        frames = self.frames

        # write in a loop as to avoid generating a huge memory buffer
        while frames > 0:
            if frames > 1000:
                write(SILENCE_STRUCT_1000)
                frames -= 1000
            elif frames > 100:
                write(SILENCE_STRUCT_100)
                frames -= 100
            elif frames > 10:
                write(SILENCE_STRUCT_10)
                frames -= 10
            else:
                write(SILENCE_STRUCT)
                frames -= 1


class TimeTracker:
    def __init__(self) -> None:
        self.starting_time: Optional[float] = clock_timestamp()  # Also used as filename
        self.first_packet_time: Optional[float] = None
        self.stopping_time: Optional[float] = None

        self.users_times: dict[int, tuple[int, float]] = {}

    def add_user(self, user, start_time) -> None:
        if user not in self.users_times:
            self.users_times[user] = start_time

    def calculate_silence(self, user_id, timestamp, received_timestamp):
        # process a packet for a registered user
        if user_time := self.users_times.get(user_id):
            delta_created_time = timestamp - user_time[0]
            delta_received_time = (received_timestamp - user_time[1]) * AUDIO_HZ
            difference = abs(100 - (delta_created_time * 100 / delta_received_time))

            # calculate time since last audio packet
            if difference > DIFFERENCE_THRESHOLD and delta_created_time != SILENCE_FRAME_SIZE:
                silence = delta_received_time - SILENCE_FRAME_SIZE
            else:
                silence = delta_created_time - SILENCE_FRAME_SIZE

        # first packet ever
        elif not self.users_times:
            # register first packet ever
            self.first_packet_timestamp = received_timestamp
            silence = 0

        # first packet from user
        else:
            # calculate time since first packet from user
            silence = (
                (received_timestamp - self.first_packet_timestamp) * AUDIO_HZ
            ) - SILENCE_FRAME_SIZE

        # update receive times for next calculation
        self.users_times[user_id] = (timestamp, received_timestamp)

        return Silence(
            frames=(max(0, int(silence / SILENCE_FRAME_SIZE)) * opus.DecoderThread.CHANNELS)
        )


def _open_tmp_file(guild_id, user_id):
    path = Path(f".rectmps/{guild_id}.{user_id}.tmp")

    try:
        return open(path, "wb+")

    except FileNotFoundError:
        makedirs(dirname(path), exist_ok=True)  # Create missing dirs
        path.touch(exist_ok=True)  # create missing file
        return open(path, "wb+")


class AudioWriter:
    def __init__(self, temp_type: TempType, guild_id: int, user_id: int) -> None:
        self.buffer: Union[BufferedWriter, BytesIO]
        if temp_type == TempType.File:
            self.buffer = _open_tmp_file(guild_id, user_id)
        elif temp_type == TempType.Memory:
            self.buffer = BytesIO()
        else:
            raise InvalidTempType("Arg `temp_type` must be of type TempType")

    def write(self, bytes) -> None:
        if not self.buffer.closed:
            self.buffer.write(bytes)


class AudioData(dict):
    def __init__(self, decoder: opus.DecoderThread) -> None:
        self.time_tracker: Optional[TimeTracker] = None
        self.decoder: opus.DecoderThread = decoder

    def get_writer(self, temp_type: TempType, guild_id: int, user_id: int) -> AudioWriter:
        return self.get(user_id) or self.add_new_writer(
            user_id, AudioWriter(temp_type, guild_id, user_id)
        )

    def add_new_writer(self, user_id: int, writer: AudioWriter) -> AudioWriter:
        self[user_id] = writer
        return writer

    def append(
        self, temp_type: TempType, guild_id: int, user_id: int, silence: Silence, data: bytes
    ) -> None:
        writer = self.get_writer(temp_type, guild_id, user_id)
        silence.write_to(writer.buffer)
        writer.write(data)

    def export(self, audio_format: Formats) -> list[File]:
        if not self.time_tracker:
            raise OngoingRecordingError("Cannot export a recording before it is stopped!")

        if not isinstance(audio_format, Formats):
            raise TypeError("audio_format must be of type `Formats`")

        exporter = getattr(exporters, formats[audio_format])

        audio: list[File] = exporter(self)  # individual files + merged file

        return audio


class RecorderClient(VoiceClient):
    def __init__(
        self,
        client: Client,
        channel: ConnectableVoiceChannels,
        auto_deaf: bool = True,
        temp_type: TempType = TempType.File,
    ) -> None:
        super().__init__(client, channel)
        self.channel: ConnectableVoiceChannels

        self.time_tracker: Optional[TimeTracker] = None
        self.audio_data: Optional[AudioData] = None

        self.process: Optional[Thread] = None
        self.auto_deaf: bool = auto_deaf
        self.temp_type: TempType = temp_type

    async def voice_connect(self, deaf=None, mute=None) -> None:
        await self.channel.guild.change_voice_state(
            channel=self.channel,
            self_deaf=(deaf if deaf is not None else (True if self.auto_deaf else False)),
            self_mute=mute or False,
        )

    # recording stuff

    def _process_decoded_audio(
        self,
        _: int,  # sequence
        timestamp: int,
        received_timestamp: float,
        ssrc: int,
        decoded_data: bytes,
    ) -> None:
        if self.audio_data is None or self.time_tracker is None or not self.guild:
            return

        ssrc_cache = self.ws.ssrc_cache
        while not (user_data := ssrc_cache.get(ssrc)):
            sleep(0.05)

        silence = self.time_tracker.calculate_silence(
            (user_id := user_data["user_id"]),
            timestamp,
            received_timestamp,
        )

        self.audio_data.append(
            self.temp_type,
            self.guild.id,
            user_id,
            silence,
            decoded_data,
        )

    def _decode_audio(self, data) -> None:
        if 200 <= data[1] <= 204:
            return  # RTCP concention info, not useful

        data = bytearray(data)

        header = data[:12]
        data = data[12:]

        sequence, timestamp, ssrc = unpack_from(">xxHII", header)

        decrypted_data = getattr(decrypter, f"decrypt_{self.mode}")(self.secret_key, header, data)

        if decrypted_data == FRAME_OF_SILENCE:
            return

        # decoder will call `_process_decoded_audio` once finished decoding
        self.decoder.decode((sequence, timestamp, perf_counter(), ssrc, decrypted_data))

    def _process_audio_packet(self, data) -> None:
        if self.audio_data is None:
            return

        self._decode_audio(data)

    def _start_packets_recording(self) -> Optional[AudioData]:
        self.time_tracker = TimeTracker()
        self.audio_data = AudioData(self.decoder)

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

        self.process = Thread(target=self._start_packets_recording)
        self.process.start()
        return self.process

    async def start_recording(self, channel: Optional[ConnectableVoiceChannels] = None) -> Thread:
        if self.time_tracker:
            raise OngoingRecordingError(
                f"A recording has already started at {self.time_tracker.starting_time}"
            )

        if channel:
            self.channel = channel
            await self.voice_connect(deaf=False)

        if not self.is_connected():
            raise NotConnectedError("Not connected to a voice channel.")

        return self._start_recording()

    def _stop_recording(self) -> AudioData:
        if not (time_tracker := self.time_tracker):  # stops the recording loop
            raise NotRecordingError(f"There is no ongoing recording to stop.")

        if (audio_data := self.audio_data) is None:
            raise TempNotFound("Audio data not found!")

        audio_data.decoder = self.decoder
        audio_data.time_tracker = time_tracker

        self.time_tracker = None
        self.audio_data = None

        return audio_data

    async def stop_recording(
        self, disconnect: bool = False, export_format: Optional[Formats] = None
    ) -> Union[AudioData, list[File]]:
        audio_data: AudioData = self._stop_recording()

        if disconnect:
            await self.disconnect()

        if not disconnect and self.auto_deaf:
            await self.voice_connect()

        if not export_format:
            return audio_data

        return audio_data.export(export_format)
