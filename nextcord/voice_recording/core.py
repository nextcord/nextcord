# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from io import BufferedIOBase, BufferedRandom, BufferedWriter, BytesIO
from select import select
from struct import pack, unpack_from
from sys import version_info as PYTHON_VERSION
from threading import Thread
from time import perf_counter, sleep, time as clock_timestamp
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Union

import nextcord.voice_client as nc_vc
from nextcord.utils import MISSING

from . import decrypter
from .errors import *
from .exporters import AudioFile, export_as_PCM, export_as_WAV, export_with_ffmpeg
from .opus import DecoderThread
from .shared import *

if TYPE_CHECKING:
    from nextcord import Member, User
    from nextcord.abc import Connectable
    from nextcord.client import Client


AUDIO_HZ = DecoderThread.SAMPLING_RATE
FRAME_SIZE = 960
FPS = AUDIO_HZ / FRAME_SIZE
RECV_SIZE = 4096
FRAME_OF_SILENCE = b"\xf8\xff\xfe"
DIFFERENCE_THRESHOLD = 60

STUB = ()

STRUCT_SIZE = 512
SILENCE_STRUCT = pack("<h", 0) * FRAME_SIZE * STRUCT_SIZE  # 1.8mb in size at 512

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
    __slots__ = ("frames",)

    def __init__(self, frames: int) -> None:
        self.frames: int = frames

    @property
    def milliseconds(self) -> float:
        return self.frames / (AUDIO_HZ / FRAME_SIZE) * 1000

    def write_to(self, buffer: BufferedIOBase) -> None:
        res, remainder = divmod(self.frames, STRUCT_SIZE)

        # write in a loop as to avoid generating a huge memory buffer
        if res:
            for _ in range(res):
                buffer.write(SILENCE_STRUCT)

        # write the rest
        if remainder:
            buffer.write(SILENCE_STRUCT[: remainder * FRAME_SIZE * DecoderThread.CHANNELS])

    @classmethod
    def from_timedelta(cls, silence: int):
        half_frames = int(silence / FRAME_SIZE)
        return None if half_frames <= 0 else cls(half_frames * DecoderThread.CHANNELS)


class RecordingFilter:
    __slots__ = ("users", "client", "ignored_after")

    def __init__(
        self,
        client=None,
        iterable: Optional[Iterable[Union[int, User, Member]]] = None,
        ignored_after: Optional[int] = None,
    ) -> None:
        self.users = set()
        self.client: Optional[RecorderClient] = client
        self.ignored_after = ignored_after

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
        users = {self._get_id(u) for u in iterable}

        return self.users.update(users)

    def remove(self, user: Union[int, User, Member]) -> None:
        return self.users.remove(self._get_id(user))

    def discard(self, user: Union[int, User, Member]) -> None:
        return self.users.discard(self._get_id(user))

    def clear(self) -> None:
        self.users.clear()

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
            raise TypeError(f"Arg `tmp_type` must be of type `TmpType` not `{type(tmp_type)}`")

    def write(self, bytes) -> None:
        if not self.buffer.closed:
            self.buffer.write(bytes)

    def close(self) -> None:
        name = (
            self.buffer.name if isinstance(self.buffer, (BufferedRandom, BufferedWriter)) else None
        )
        self.buffer.close()

        if name:
            os.remove(name)


class TimeTracker:
    __slots__ = (
        "starting_time",
        "starting_perf",
        "first_packet_time",
        "users_times",
        "last_periodic_write",
    )

    def __init__(self) -> None:
        self.starting_time: float = clock_timestamp()  # also used as filename
        self.starting_perf: float = perf_counter()  # used for leakage detection
        self.first_packet_time: Optional[float] = None

        self.users_times: Dict[int, tuple[int, float]] = {}
        self.last_periodic_write: float = perf_counter()

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
            if difference > DIFFERENCE_THRESHOLD and delta_created_time != FRAME_SIZE:
                silence = delta_received_time - FRAME_SIZE
            else:
                silence = delta_created_time - FRAME_SIZE

        # first packet ever
        elif not self.users_times:
            # register first packet
            self.first_packet_time = received_timestamp
            silence = 0

        # first packet from user
        else:
            # calculate time since first packet
            silence = ((received_timestamp - self.first_packet_time) * AUDIO_HZ) - FRAME_SIZE

            # store first silence to write later if needed
            writer.starting_silence = Silence.from_timedelta(silence)
            # update receive times for next calculation
            self.users_times[user_id] = (timestamp, received_timestamp)

            return None  # starting silence written later in export

        # update receive times for next calculation
        self.users_times[user_id] = (timestamp, received_timestamp)

        return Silence.from_timedelta(silence)

    # helper method for inserting to a different dict during dict comprehension
    @staticmethod
    def _add_user_time_with_insert(
        user_map: dict, user: int, x: Union[int, float], u_t: int
    ) -> float:
        user_map[user] = u_t
        return x + u_t

    def write_periodic_silence(
        self, period: int, audio_data: Optional[AudioData], tmp_type: TmpType, guild_id: int
    ) -> None:
        if not audio_data:
            return

        # time at which a user's audio should have silence written to
        t = perf_counter()

        # ensure this method doesnt called more often than needed
        if (
            self.last_periodic_write + (period * 0.8) > t
        ):  # multiply by 0.8 to give some leeway time
            return
        self.last_periodic_write = t

        # users which havent been updated in over `period` seconds
        users_to_write: Dict[int, int] = {}
        users_to_update: Dict[int, tuple[int, float]] = {
            user: (
                t_create + (u_t * FRAME_SIZE),
                self._add_user_time_with_insert(users_to_write, user, t_receive, u_t),
            )
            for user, (t_create, t_receive) in self.users_times.items()
            if (u_t := int(t - t_receive)) > period  # if user hasn't been written to in x time
        }
        self.users_times.update(users_to_update)

        const = FRAME_SIZE * (AUDIO_HZ // FRAME_SIZE)

        # write silence to each user
        for user, u_t in users_to_write.items():
            if silence := Silence.from_timedelta(u_t * const):
                logging.debug(
                    "Periodically wrote %d seconds of silence to user %d from guild %d",
                    u_t,
                    user,
                    guild_id,
                )
                silence.write_to(audio_data.get_writer(tmp_type, guild_id, user).buffer)

    def write_remaining_silence(  # called when ending recording
        self, t, audio_data: Optional[AudioData], tmp_type: TmpType, guild_id: int
    ) -> None:
        if not audio_data:
            return

        # get all users' writes
        users_to_write: Dict[int, float] = {
            user: t - t_receive for user, (_, t_receive) in self.users_times.items()
        }

        const = FRAME_SIZE * (AUDIO_HZ // FRAME_SIZE)

        # write silence to each user
        for user, u_t in users_to_write.items():
            if silence := Silence.from_timedelta(int(u_t * const)):
                logging.debug(
                    "Wrote %d seconds of final silence to user %d from guild %d",
                    u_t,
                    user,
                    guild_id,
                )
                silence.write_to(audio_data.get_writer(tmp_type, guild_id, user).buffer)


class AudioData(Dict[int, AudioWriter]):
    """A container to hold the :class:`AudioWriter` associated with each user's id
    during a recording, as well as the :class:`TimeTracker` specifying the details of
    the timings of the received packets (assigned on recording stopped).

    This is usually not meant to be created, it is received when you stop a recording
    without specifying an export format.
    """

    def __init__(self, decoder: DecoderThread) -> None:
        self.time_tracker: Optional[TimeTracker] = None
        self.decoder: DecoderThread = decoder

    def _add_writer(self, user_id: int, writer: AudioWriter) -> AudioWriter:
        self[user_id] = writer
        return writer

    def get_writer(self, tmp_type: TmpType, guild_id: int, user_id: int) -> AudioWriter:
        """Gets or creates an :class:`AudioWriter` for a specific user.

        Parameters
        ----------
        tmp_type: class:`TmpType`
            The type of temporary storage to create the writer with when it is necessary.
        guild_id: :class:`int`
            The guild id used for creating the writer when it is necessary.
        user_id: :class:`int`
            The user id to get the writer for.

        Returns
        -------
        AudioWriter
            The writer containing the audio data of a specific user.
        """
        return self.get(user_id) or self._add_writer(
            user_id, AudioWriter(tmp_type, guild_id, user_id)
        )

    def remove_writer(self, user_id: int) -> None:
        """Remove an :class:`AudioWriter` if it exists.

        Parameters
        ----------
        user_id: :class:`int`
            The user id to remove from this map.
        """
        return w.close() if (w := self.pop(user_id, None)) else None

    def process_filters(self, filters: Optional[RecordingFilter]) -> None:
        """Removes the writers that match the designated filters

        Parameters
        ----------
        filters: :class:`RecordingFilter`
            The filter to use to filter the writers map.
        """
        if not filters:
            return

        filtered_writers = [uid for uid in self if uid in filters]
        for user_id in filtered_writers:
            self.remove_writer(user_id)

    async def export(
        self,
        audio_format: Formats,
        tmp_type: TmpType,
        filters: Optional[RecordingFilter] = None,
    ) -> Dict[int, AudioFile]:
        """
        Exports the stored references to each writer containing the audio data
        to the specified format.

        audio_format: :class:`Formats`
            The format to export this this container to.
        tmp_type :class:`TmpType`:
            The type of temporary storage to use for exporting. Exporting in memory is **not**
            supported for `m4a` and `mp4` formats.
        filters Optional[:class:`RecordingFilter`] = None
            The filters to use when exporting.

        Raises
        ------
        OngoingRecordingError
            A recording must be stopped before exporting.
            This is raised when a recording is still ongoing.
        TypeError
            When the audio format is not a supported format from the local enum.

        Returns
        -------
        Dict[int, AudioFile]
            A map of the each user to their respective exported :class:`AudioFile`.
        """
        if not self.time_tracker:
            raise OngoingRecordingError("Cannot export a recording before it is stopped!")

        if not isinstance(audio_format, Formats):
            raise TypeError(f"audio_format must be of type `Formats` not {type(audio_format)}")

        return await export_methods[audio_format](
            self, audio_format, tmp_type, filters=filters  # individual files
        )


# slots only work on python 3.10 with dataclasses
@dataclass(**{"slots": True} if PYTHON_VERSION >= (3, 10) else {})
class OpusFrame:
    sequence: int
    timestamp: float
    received_timestamp: float
    ssrc: int
    decrypted_data: Optional[bytes]
    decoded_data: Optional[bytes] = None
    user_id: Optional[int] = None

    @property
    def is_silent(self):
        return self.decrypted_data == FRAME_OF_SILENCE

    def __repr__(self) -> str:
        attrs = (
            ("sequence", self.sequence),
            ("timestamp", self.timestamp),
            ("received_timestamp", self.received_timestamp),
            ("ssrc", self.ssrc),
            ("user_id", self.user_id),
        )
        joined = " ".join("%s=%r" % t for t in attrs)
        return f"<{self.__class__.__name__} {joined}>"


class RecorderClient(nc_vc.VoiceClient):
    """Represents a Discord voice connection that is able to receive audio packets.

    This is returned when passing `recordable=True` when connecting to a voice channel.

    Warning
    -------
    **Receiving audio:**
    In order to receive usable voice data,
    decryption is performed using the `PyNaCl` library

    **Playing audio:**
    In order to use PCM based AudioSources, you must have the opus library
    installed on your system and loaded through :func:`opus.load_opus`.
    Otherwise, your AudioSources must be opus encoded (e.g. using :class:`FFmpegOpusAudio`)
    or the library will not be able to transmit audio.

    Attributes
    ----------
    session_id: :class:`str`
        The voice connection session ID.
    token: :class:`str`
        The voice connection token.
    endpoint: :class:`str`
        The endpoint we are connecting to.
    channel: :class:`abc.Connectable`
        The voice channel connected to.
    loop: :class:`asyncio.AbstractEventLoop`
        The event loop that the voice client is running on.

    time_tracker: Optional[:class:`TimeTracker`]
        A container class that keeps track of all timings related to the current recording.
    audio_data: Optional[:class:`AudioData`]
        A container class that keeps track of all data related information relative to each
        user in the current recording.
    recording_paused: :class:`bool`
        Whether or not the recording is currently paused or stopped.
    filters: :class:`RecordingFilter`
        A container of the default filters that should be used with this recording client.
    decoder: :class:`DecoderThread`
        The decoder instance used to convert decrypted opus data into pcm data.
    process: Optional[:class:`Thread`]
        The process :class:`threading.Thread` of a recording instance.
    auto_deaf: :class:`bool`
        Whether or not the client will automatically deafen when not recording.
    tmp_type: :class:`TmpType`
        The type of temporary storage to contain recorded data.
    prevent_leakage: :class:`bool`
        Whether to attempt to prevent leekage. Unstable feature!
    periodic_write_seconds: :class:`int`
        The delay between periodic silence writes
    """

    def __init__(
        self,
        client: Client,
        channel: Connectable,
        auto_deaf: bool = True,
        tmp_type: TmpType = TmpType.File,
        filters: Optional[RecordingFilter] = None,
        periodic_write_seconds: Optional[int] = 5,
        prevent_leakage: bool = False,
    ) -> None:
        super().__init__(client, channel)
        self.channel: Connectable

        # data
        self.time_tracker: Optional[TimeTracker] = None
        self.audio_data: Optional[AudioData] = None
        self.recording_paused: bool = False
        self.filters: RecordingFilter = filters or RecordingFilter()

        # processes
        self.process: Optional[Thread] = None
        self.auto_deaf: bool = auto_deaf if isinstance(auto_deaf, bool) else True
        self.tmp_type: TmpType = tmp_type or TmpType.File

        # leakage calculation
        self.prevent_leakage: bool = prevent_leakage  # unstable feature
        self.time_info: Dict[int, tuple] = {}  # ssrc to tuple[timestamp, received]

        # periodically write silence
        self.periodic_write_seconds: Optional[int] = periodic_write_seconds

        # handlers private
        self.__handler_set: bool = False
        self.__record_alongside_handler: bool = False
        self.__raw_handler: Optional[Callable[[bytes], Any]] = None
        self.__decrypted_handler: Optional[Callable[[OpusFrame], Any]] = None
        self.__decoded_handler: Optional[Callable[[OpusFrame], Any]] = None

    @property
    def is_recording(self) -> bool:
        """Whether or not a recording is currently ongoing.
        This does **not** take into account whether the recording is paused.
        """
        return bool(self.time_tracker)

    async def voice_connect(self, deaf=None, mute=None) -> None:
        await self.channel.guild.change_voice_state(  # type: ignore
            channel=self.channel,
            self_deaf=(deaf if deaf is not None else (bool(self.auto_deaf))),
            self_mute=mute or False,
        )

    # custom output stuff

    def set_data_handler(
        self,
        *,
        raw_data_handler: Optional[Callable[[bytes], None]] = None,
        decrypted_data_handler: Optional[Callable[[OpusFrame], None]] = None,
        decoded_data_handler: Optional[Callable[[OpusFrame], None]] = None,
        record_alongside_handler: bool = False,
    ) -> None:
        """
        Setting a data handler allows the RecorderClient to output the data from discord
        to your own method for handling instead of recording the audio. This is useful if
        you are streaming this data somewhere else directly and don't want to record the data.

        .. note:: You may only set one data handler.

        Parameters
        ----------
        raw_data_handler: Optional[:class:`Callable[:class:`bytes`], None]`] = None
            Set a handler method receiving the raw audio data from Discord.
        decrypted_data_handler: Optional[:class:`Callable[:class:`OpusFrame`], None]`] = None
            Set a handler method receiving the decrypted opus audio data.
        decoded_data_handler: Optional[:class:`Callable[:class:`OpusFrame`], None]`] = None
            Set a handler method receiving the decoded pcm audio data.
            This contains the decrypted data as well.
        record_alongside_handler: :class:`bool` = False
            Whether or not to also record audio alongside your custom set data handler.

        Raises
        ------
        MultipleHandlersError
            Multiple handlers were passed when calling this method.
        """

        self.__record_alongside_handler = record_alongside_handler
        self.__raw_handler = raw_data_handler
        self.__decrypted_handler = decrypted_data_handler
        self.__decoded_handler = decoded_data_handler

        handlers = (
            self.__raw_handler,
            self.__decrypted_handler,
            self.__decoded_handler,
        )

        if sum(bool(method) for method in handlers) > 1:
            self.__raw_handler = None
            self.__decrypted_handler = None
            self.__decoded_handler = None
            raise MultipleHandlersError(
                "You may only set one handler! The lowest level handler will be called ommiting the rest.\n"
                "`raw_data_handler` being the lowest level for handling raw data from discord.\n"
                "`decrypted_data_handler` will give you valid decrypted opus audio data.\n"
                "`decoded_data_handler` will give you the decrypted data and pcm audio bytes.\n"
            )

        if not self.__record_alongside_handler:
            self.__handler_set = True

    # recording stuff

    def set_prevent_leakage(self, prevent_leakage: bool) -> None:
        """
        Attempts to prevent leekage of audio when starting a 2nd recording without reconnecting.

        Warning
        -------
        This feature is unstable and may cause the recording to start slightly delayed, or may
        not work at all in certain untested cases. Use at your own risk!

        Parameters
        ----------
        prevent_leakage: :class:`True`
            The value to set for `prevent_leakage`
        """
        self.prevent_leakage = prevent_leakage

    def _process_decoded_audio(
        self,
        opus_frame: OpusFrame,
    ) -> None:
        if self.__decoded_handler:
            self.__decoded_handler(opus_frame)
            # terminate early after calling custom decoded handler method if not set to record too
            if not self.__record_alongside_handler:
                return None

        if self.audio_data is None or self.time_tracker is None or not self.guild:
            return None

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
        return None

    def _calc_timestamp(self, ssrc: int, t: float) -> Union[int, float]:
        if not self.time_info:
            return 0
        if not (ti := self.time_info.get(ssrc)):
            return 0

        discord_rtp, clocktime = ti
        return (
            discord_rtp  # original rtp at the saved timestamp
            + (abs(t - clocktime) * FRAME_SIZE * FPS)  # offset to the current timestamp
            - (
                FRAME_SIZE * min(self.latency * 1000, 1000) / FRAME_SIZE
            )  # minus the latency (max 1s)
        )

    def _decode_audio(self, data: bytes) -> None:
        if not self.time_tracker:
            return

        # check & write silence when receiving any packet
        if self.guild and self.periodic_write_seconds is not None:
            self.time_tracker.write_periodic_silence(
                self.periodic_write_seconds, self.audio_data, self.tmp_type, self.guild.id
            )
        else:
            logging.debug(
                "Unable to write periodic silence due to no `time_tracker` or no `guild`."
            )

        # RTCP concention info, not useful
        if 200 <= data[1] <= 204:
            return

        # decryption
        data = bytearray(data)

        header = data[:12]
        data = data[12:]

        sequence, timestamp, ssrc = unpack_from(">xxHII", header)

        # in case timestamp from discord has reset
        if self.prevent_leakage:
            t = perf_counter()
            if ssrc not in self.time_info:
                pass
            elif self.time_info and timestamp < self.time_info[ssrc][0]:
                self.time_info = {}
            # try discard any packet leakage from previous recording
            elif self.time_tracker.starting_perf + 1 > t and timestamp < self._calc_timestamp(
                ssrc, t
            ):
                # kept for debug: print(f"[FAIL] {sequence} | {timestamp} vs {self._calc_timestamp(ssrc, t)}")
                return
            # kept for debug: print(f"[PASS] {sequence} | {timestamp} vs {self._calc_timestamp(ssrc, t)}")

            self.time_info[ssrc] = (timestamp, perf_counter())

        decrypted_data = getattr(decrypter, f"decrypt_{self.mode}")(self.secret_key, header, data)

        opus_frame = OpusFrame(sequence, timestamp, perf_counter(), ssrc, decrypted_data)

        if self.__decrypted_handler:
            self.__decrypted_handler(opus_frame)
            # terminate early after calling custom decrypt handler method if not set to record too
            if not self.__record_alongside_handler:
                return

        if decrypted_data == FRAME_OF_SILENCE:
            return

        # send to decoder now
        # decoder will call `_process_decoded_audio` once finished decoding
        self.decoder.decode(opus_frame)

    def _process_audio_packet(self, data: bytes) -> None:
        if self.audio_data is None:
            return None

        if self.__raw_handler:
            self.__raw_handler(data)
            # terminate early after calling custom decoded handler method if not set to record too
            if not self.__record_alongside_handler:
                return None

        return self._decode_audio(data)

    def _start_packets_recording(self) -> Optional[tuple[Optional[AudioData], TimeTracker]]:
        self.time_tracker = TimeTracker()
        self.audio_data = AudioData(self.decoder)

        pre_socket = [self.socket]

        while self.time_tracker:
            ready, _, error = select(pre_socket, STUB, pre_socket, 0.01)
            if not ready:
                if error:
                    logging.debug("Socket Error: %s", str(error))
                continue

            try:
                if self.recording_paused:
                    self.socket.recv(RECV_SIZE)
                else:
                    self._process_audio_packet(self.socket.recv(RECV_SIZE))
            except OSError:
                return self._stop_recording()

        return None

    def _start_recording(self) -> None:
        self.recording_paused = False

        if (
            self.__record_alongside_handler  # requires recording alongside
            or self.__decoded_handler  # requires decoding data
            or not self.__handler_set  # normal recording
        ):
            self.decoder = DecoderThread(self)
            self.decoder.start()

        Thread(target=self._start_packets_recording).start()

    async def start_recording(self, channel: Optional[Connectable] = None) -> None:
        """|coro|
        Start recording audio, and optionally connect to a voice channel.

        Parameters
        ----------
        channel: Optional[:class:`Connectable`] = None
        """
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
        """Set paused to be False.
        Effectively pausing a recording if there is an ongoing one
        """

        self.recording_paused = True

    def resume_recording(self) -> None:
        """Set paused to be False.
        Effectively resuming a recording if there is an ongoing one
        """

        self.recording_paused = False

    def toggle_recording_paused(self) -> None:
        """Toggleing whether a recording is paused if there is an ongoing one."""

        self.recording_paused = self.recording_paused is False

    def _stop_recording(self) -> tuple[Optional[AudioData], TimeTracker]:
        if not (time_tracker := self.time_tracker):  # stops the recording loop
            raise NotRecordingError("There is no ongoing recording to stop.")

        audio_data = self.audio_data

        self.recording_paused = True

        self.decoder.stop()

        if audio_data:
            audio_data.decoder = self.decoder
            audio_data.time_tracker = time_tracker

        self.time_tracker = None
        self.audio_data = None

        return audio_data, time_tracker

    async def stop_recording(
        self,
        disconnect: bool = False,
        export_format: Optional[Formats] = None,
        tmp_type: TmpType = TmpType.File,  # memory tmp export will not work with m4a & mp4
        filters: Optional[RecordingFilter] = MISSING,
        write_remaining_silence: bool = False,
    ) -> Optional[Union[AudioData, Dict[int, AudioFile]]]:
        """|coro|
        Stops a currently ongoing recording.

        Parameters
        ----------
        disconnect: class:`bool` = False
            Whether to disconnect the voice channel as well.
        export_format: Optional[:class:`Formats`] = None
            Select a format to export the audio in.
            Does not export when left as `None`.
        tmp_type: :class:`TmpType` = TmpType.File
            The type of temporary storage to use for exporting. Exporting in memory is **not**
            supported for `m4a` and `mp4` formats.
        filters: Optional[:class:`RecordingFilter`] = MISSING
            The filters to use when exporting. This defaults to the one set to the client if
            not specified. No filter will be used when this is `None`
        write_remaining_silence: Optional[:class:`bool`] = False
            This will add the missing silence to each recording
            Setting this to `True` while periodic writes are not on may result in a very
            large silence write before the recording ends.

        Raises
        ------
        ExportUnavailable
            Attempting to export an incomplete recording. This occurs when setting a data
            handler that does not record alongside it at any point during the recording.
        NotRecordingError
            Attempting to stop a recording when the client is not currently recording.
        TmpNotFound
            The temporary files storing the audio data were not found.

        Returns
        -------
            AudioData
                When export is not specified, you receive the the audio data map
                of each user's id to their respective :class:`AudioWriter`
            Dict[int, AudioFile]
                When export is specified, you will receive the dict containing
                each user's id to their respective :class:`AudioFile`
        """
        audio_data: Optional[AudioData]
        time_tracker: Optional[TimeTracker]
        audio_data, time_tracker = self._stop_recording()
        t = perf_counter()

        if disconnect:
            await self.disconnect()

        if not disconnect and self.auto_deaf:
            await self.voice_connect()

        if self.__handler_set:
            if export_format:
                raise ExportUnavailable(
                    "Cannot export incomplete audio recordings due to setting a custom handler!"
                )
            return None

        if not audio_data:
            raise TmpNotFound("Audio data not found!")

        if write_remaining_silence:
            if time_tracker and self.guild:
                time_tracker.write_remaining_silence(t, audio_data, self.tmp_type, self.guild.id)
            else:
                logging.debug(
                    "Unable to write periodic silence due to no `time_tracker` or no `guild`. "
                    "Silently ignored."
                )

        if not export_format:
            return audio_data

        if filters:
            return await audio_data.export(export_format, tmp_type, filters)
        elif filters is MISSING:
            return await audio_data.export(export_format, tmp_type, self.filters)
        else:
            return await audio_data.export(export_format, tmp_type)
