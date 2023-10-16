# SPDX-License-Identifier: MIT

import logging
import os
from dataclasses import dataclass
from select import select
from struct import pack, unpack_from
from threading import Thread
from time import perf_counter, sleep, time as clock_timestamp
from typing import Any, Dict, Callable, Iterable, Optional, Union
from io import BufferedIOBase, BufferedRandom, BufferedWriter, BytesIO
from sys import version_info as PYTHON_VERSION

from nextcord import StageChannel, VoiceChannel, VoiceClient, Member, User
from nextcord.client import Client
from nextcord.utils import MISSING

from . import decrypter
from .exporters import (
    export_with_ffmpeg,
    export_as_PCM,
    export_as_WAV,
    AudioFile
)
from .opus import DecoderThread
from .errors import *
from .shared import *


ConnectableVoiceChannels = Union[VoiceChannel, StageChannel]


AUDIO_HZ = DecoderThread.SAMPLING_RATE
SILENCE_FRAME_SIZE = 960
RECV_SIZE = 4096
FRAME_OF_SILENCE = b"\xf8\xff\xfe"
DIFFERENCE_THRESHOLD = 60

STUB = ()


SILENCE_STRUCT = pack("<h", 0) * SILENCE_FRAME_SIZE
SILENCE_STRUCT_10 = SILENCE_STRUCT * 10
SILENCE_STRUCT_100 = SILENCE_STRUCT * 100
SILENCE_STRUCT_1000 = SILENCE_STRUCT * 1000  # 3.4mb in size


export_methods = {
    Formats.MP3: export_with_ffmpeg,
    Formats.MP4: export_with_ffmpeg,
    Formats.M4A: export_with_ffmpeg,
    Formats.MKA: export_with_ffmpeg,
    Formats.MKV: export_with_ffmpeg,
    Formats.OGG: export_with_ffmpeg,
    Formats.PCM: export_as_PCM,
    Formats.WAV: export_as_WAV,
}


class Silence:
    __slots__ = ("frames", )

    def __init__(self, frames: int) -> None:
        self.frames: int = frames

    @property
    def milliseconds(self) -> float:
        return self.frames / (AUDIO_HZ / SILENCE_FRAME_SIZE) * 1000

    def write_to(self, buffer: BufferedIOBase) -> None:
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

    @classmethod
    def from_timedelta(cls, silence: int):
        half_frames = int(silence / SILENCE_FRAME_SIZE)
        if half_frames <= 0:
            return None
        return cls(half_frames * DecoderThread.CHANNELS)


class UserFilter:
    __slots__ = ("users", "client")

    def __init__(
        self,
        client = None,
        iterable: Optional[Iterable[Union[int, User, Member]]] = None
    ) -> None:
        self.users = set()
        self.client: Optional[RecorderClient] = client
        
        if iterable:
            self.users.update(iterable)

    def _get_id(self, user: Union[int, User, Member]) -> int:
        if self.client and self.client.time_tracker:
            raise OngoingRecordingError(
                "Cannot modify filters while recording. "
                "Filters can be modified before, or passed when exporting."
            )

        if isinstance(user, int):
            return user
        
        if isinstance(user, (Member, User)):
            return user.id

        raise TypeError("Each user must be of type `int`, `User`, or `Member`")

    def add(self, user: Union[int, User, Member]) -> None:
        return self.users.add(self._get_id(user))

    def extend(self, iterable: Iterable[Union[int, User, Member]]) -> None:
        users = set(
            self._get_id(u)
            for u in iterable
        )

        return self.users.update(users)

    def remove(self, user: Union[int, User, Member]) -> None:
        return self.users.remove(self._get_id(user))

    def discard(self, user: Union[int, User, Member]) -> None:
        return self.users.discard(self._get_id(user))

    def __contains__(self, key: Union[int, User, Member]) -> bool:
        return self._get_id(key) in self.users


class AudioWriter:
    __slots__ = ("guild_id", "user_id", "buffer", "starting_silence")

    def __init__(self, tmp_type: TmpType, guild_id: int, user_id: int) -> None:
        self.guild_id = guild_id
        self.user_id = user_id

        self.buffer: Union[BufferedWriter, BytesIO]
        self.starting_silence: Optional[Silence] = None

        if tmp_type == TmpType.File:
            self.buffer = open_tmp_file(guild_id, user_id, "wb+")
        elif tmp_type == TmpType.Memory:
            self.buffer = BytesIO()
        else:
            raise TypeError(
                f"Arg `tmp_type` must be of type `TmpType` not `{type(tmp_type)}`"
            )

    def write(self, bytes) -> None:
        if not self.buffer.closed:
            self.buffer.write(bytes)
    
    def close(self):
        name = self.buffer.name if isinstance(self.buffer, (BufferedRandom, BufferedWriter)) else None
        self.buffer.close()

        if name:
            os.remove(name)


class TimeTracker:
    __slots__ = ("starting_time", "first_packet_time", "users_times")

    def __init__(self) -> None:
        self.starting_time: Optional[float] = clock_timestamp()  # Also used as filename
        self.first_packet_time: Optional[float] = None

        self.users_times: Dict[int, tuple[int, float]] = {}

    def add_user(self, user, start_time) -> None:
        if user not in self.users_times:
            self.users_times[user] = start_time

    def calculate_silence(
        self, writer: AudioWriter, user_id, timestamp, received_timestamp
    ) -> Optional[Silence]:
        # process a packet for a registered user
        if user_time := self.users_times.get(user_id):
            delta_created_time = timestamp - user_time[0]
            delta_received_time = (received_timestamp - user_time[1]) * AUDIO_HZ
            difference = abs(100 - (delta_created_time * 100 / delta_received_time))

            # calculate time since last audio packet
            if (
                difference > DIFFERENCE_THRESHOLD
                and delta_created_time != SILENCE_FRAME_SIZE
            ):
                silence = delta_received_time - SILENCE_FRAME_SIZE
            else:
                silence = delta_created_time - SILENCE_FRAME_SIZE

        # first packet ever
        elif not self.users_times:
            # register first packet
            self.first_packet_time = received_timestamp
            silence = 0

        # first packet from user
        else:
            # calculate time since first packet
            silence = (
                (received_timestamp - self.first_packet_time) * AUDIO_HZ
            ) - SILENCE_FRAME_SIZE

            # store first silence to write later if needed
            writer.starting_silence = Silence.from_timedelta(silence)
            # update receive times for next calculation
            self.users_times[user_id] = (timestamp, received_timestamp)

            return None  # starting silence written later in export

        # update receive times for next calculation
        self.users_times[user_id] = (timestamp, received_timestamp)

        return Silence.from_timedelta(silence)


class AudioData(dict[int, AudioWriter]):
    def __init__(self, decoder: DecoderThread) -> None:
        self.time_tracker: Optional[TimeTracker] = None
        self.decoder: DecoderThread = decoder

    def get_writer(
        self, tmp_type: TmpType, guild_id: int, user_id: int
    ) -> AudioWriter:
        return self.get(user_id) or self.add_new_writer(
            user_id, AudioWriter(tmp_type, guild_id, user_id)
        )

    def add_new_writer(self, user_id: int, writer: AudioWriter) -> AudioWriter:
        self[user_id] = writer
        return writer
    
    def remove_writer(self, user_id: int):
        return w.close() if (w := self.pop(user_id, None)) else w

    def process_filters(self, filters: Optional[UserFilter] = None) -> None:
        if not filters:
            return

        filtered_writers = [uid for uid in self if uid in filters]
        for user_id in filtered_writers:
            self.remove_writer(user_id)

    async def export(
        self,
        audio_format: Formats,
        tmp_type: TmpType,
        sync_start: bool = True,
        filters: Optional[UserFilter] = None
    ) -> Dict[int, AudioFile]:
        if not self.time_tracker:
            raise OngoingRecordingError(
                "Cannot export a recording before it is stopped!"
            )

        if not isinstance(audio_format, Formats):
            raise TypeError(
                f"audio_format must be of type `Formats` not {type(audio_format)}"
            )

        return await export_methods[audio_format](
            self, audio_format, tmp_type, sync_start=sync_start, filters=filters  # individual files
        )


# slots only work on python 3.10 with dataclasses
@dataclass(**{"slots": True} if PYTHON_VERSION >= (3, 10) else {})
class OpusFrame:
    sequence: int
    timestamp: float
    received_timestamp: float
    ssrc: int
    decrypted_data: bytes
    decoded_data: Optional[bytes] = None
    user_id: Optional[int] = None


class RecorderClient(VoiceClient):
    def __init__(
        self,
        client: Client,
        channel: ConnectableVoiceChannels,
        auto_deaf: bool = True,
        tmp_type: TmpType = TmpType.File,
    ) -> None:
        super().__init__(client, channel)
        self.channel: ConnectableVoiceChannels

        # data
        self.time_tracker: Optional[TimeTracker] = None
        self.audio_data: Optional[AudioData] = None
        self.recording_paused: bool = False
        self.filters = UserFilter()

        # processes
        self.decoder = DecoderThread(self)
        self.process: Optional[Thread] = None
        self.auto_deaf: bool = auto_deaf
        self.tmp_type: TmpType = tmp_type

        # handlers private
        self.__handler_set: bool = False
        self.__record_alongside_handler: bool = False
        self.__raw_data_handler: Optional[Callable[[bytes], Any]] = None
        self.__decrypted_data_handler: Optional[Callable[[OpusFrame], Any]] = None
        self.__decoded_data_handler: Optional[Callable[[OpusFrame], Any]] = None

    async def voice_connect(self, deaf=None, mute=None) -> None:
        await self.channel.guild.change_voice_state(
            channel=self.channel,
            self_deaf=(
                deaf if deaf is not None else (True if self.auto_deaf else False)
            ),
            self_mute=mute or False,
        )

    # custom output stuff

    def set_data_handler(
        self,
        *,
        raw_data_handler: Optional[Callable[[bytes], Any]] = None,
        decrypted_data_handler: Optional[Callable[[OpusFrame], Any]] = None,
        decoded_data_handler: Optional[Callable[[OpusFrame], Any]] = None,
        record_alongside_handler=False,
    ) -> None:
        self.__record_alongside_handler = record_alongside_handler
        self.__raw_data_handler = raw_data_handler
        self.__decrypted_data_handler = decrypted_data_handler
        self.__decoded_data_handler = decoded_data_handler

        handlers = (
            self.__raw_data_handler,
            self.__decrypted_data_handler,
            self.__decoded_data_handler,
        )

        if sum(bool(method) for method in handlers) > 1:
            self.__raw_data_handler = None
            self.__decrypted_data_handler = None
            self.__decoded_data_handler = None
            raise MultipleHandlersError(
                "You may only set one handler! The lowest level handler will be called ommiting the rest.\n"
                "`raw_data_handler` being the lowest level for handling raw data from discord.\n"
                "`decrypted_data_handler` will give you valid decrypted opus audio data.\n"
                "`decoded_data_handler` will give you the decrypted data and pcm audio bytes.\n"
            )

        if not self.__record_alongside_handler:
            self.__handler_set = True

    # recording stuff

    def _process_decoded_audio(
        self,
        opus_frame: OpusFrame,
    ) -> None:
        if self.__decoded_data_handler:
            self.__decoded_data_handler(opus_frame)
            # terminate early after calling custom decoded handler method if not set to record too
            if not self.__record_alongside_handler:
                return

        if self.audio_data is None or self.time_tracker is None or not self.guild:
            return

        ssrc_cache = self.ws.ssrc_cache
        while not (user_data := ssrc_cache.get(opus_frame.ssrc)):
            sleep(0.05)

        user_id = user_data["user_id"]
        if user_id in self.filters:
            return self.audio_data.remove_writer(user_id)
        
        writer = self.audio_data.get_writer(self.tmp_type, self.guild.id, user_id)

        silence: Optional[Silence] = self.time_tracker.calculate_silence(
            writer,
            user_id,
            opus_frame.timestamp,
            opus_frame.received_timestamp,
        )

        if silence is not None:
            silence.write_to(writer.buffer)

        writer.write(opus_frame.decoded_data)

    def _decode_audio(self, data: bytes) -> None:
        if 200 <= data[1] <= 204:
            return  # RTCP concention info, not useful

        data = bytearray(data)

        header = data[:12]
        data = data[12:]

        sequence, timestamp, ssrc = unpack_from(">xxHII", header)
        decrypted_data = getattr(decrypter, f"decrypt_{self.mode}")(
            self.secret_key, header, data
        )

        opus_frame = OpusFrame(
            sequence, timestamp, perf_counter(), ssrc, decrypted_data
        )

        if self.__decrypted_data_handler:
            self.__decrypted_data_handler(opus_frame)
            # terminate early after calling custom decrypt handler method if not set to record too
            if not self.__record_alongside_handler:
                return

        if decrypted_data == FRAME_OF_SILENCE:
            return

        # decoder will call `_process_decoded_audio` once finished decoding
        self.decoder.decode(opus_frame)

    def _process_audio_packet(self, data: bytes) -> None:
        if self.audio_data is None:
            return

        if self.__raw_data_handler:
            self.__raw_data_handler(data)
            # terminate early after calling custom decoded handler method if not set to record too
            if not self.__record_alongside_handler:
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
                if self.recording_paused:
                    self.socket.recv(RECV_SIZE)
                else:
                    self._process_audio_packet(self.socket.recv(RECV_SIZE))
            except OSError:
                return self._stop_recording()

    def _start_recording(self) -> None:
        self.recording_paused = False

        if (
            self.__record_alongside_handler  # requires recording alongside
            or self.__decoded_data_handler  # requires decoding data
            or not self.__handler_set  # normal recording
        ):
            self.decoder.start()

        Thread(target=self._start_packets_recording).start()

    async def start_recording(
        self, channel: Optional[ConnectableVoiceChannels] = None
    ) -> None:
        if self.time_tracker:
            raise OngoingRecordingError(
                f"A recording has already started at {self.time_tracker.starting_time}"
            )

        if channel:
            self.channel = channel
            await self.voice_connect(deaf=False)

        elif self.auto_deaf:
            await self.voice_connect(deaf=False)

        if not self.is_connected():
            raise NotConnectedError("Not connected to a voice channel.")

        self._start_recording()

    def pause_recording(self) -> None:
        self.recording_paused = True

    def resume_recording(self) -> None:
        self.recording_paused = False

    def toggle_recording_paused(self) -> None:
        self.recording_paused = True if self.recording_paused is False else True

    def _stop_recording(self) -> AudioData:
        if not (time_tracker := self.time_tracker):  # stops the recording loop
            raise NotRecordingError(f"There is no ongoing recording to stop.")

        if (audio_data := self.audio_data) is None:
            raise TmpNotFound("Audio data not found!")

        self.recording_paused = True

        self.decoder.stop()

        audio_data.decoder = self.decoder
        audio_data.time_tracker = time_tracker

        self.time_tracker = None
        self.audio_data = None

        return audio_data

    async def stop_recording(
        self,
        disconnect: bool = False,
        export_format: Optional[Formats] = None,
        tmp_type: TmpType = TmpType.File,  # memory tmp export will not work with m4a & mp4
        sync_start: bool = True,
        filters: Optional[UserFilter] = MISSING
    ) -> Optional[Union[AudioData, Dict[int, AudioFile]]]:
        audio_data: AudioData = self._stop_recording()

        if disconnect:
            await self.disconnect()

        if not disconnect and self.auto_deaf:
            await self.voice_connect()

        if self.__handler_set:
            if export_format:
                raise ExportUnavailable(
                    "Cannot export incomplete audio recordings due to setting a custom handler!"
                )
            return

        if not export_format:
            return audio_data
        
        if filters:
            return await audio_data.export(export_format, tmp_type, sync_start, filters)
        elif filters is MISSING:
            return await audio_data.export(export_format, tmp_type, sync_start, self.filters)
        else:
            return await audio_data.export(export_format, tmp_type, sync_start)
