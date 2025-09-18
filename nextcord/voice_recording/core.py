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

import nextcord.voice_client as nc_vc  # `import as` to prevent circular import
from nextcord.utils import MISSING

from . import decrypter
from .errors import *
from .exporters import (
    AudioFile,
    export_as_PCM,
    export_as_WAV,
    export_one_as_PCM,
    export_one_as_WAV,
    export_one_with_ffmpeg,
    export_with_ffmpeg,
)
from .opus import DecoderThread
from .shared import *

if TYPE_CHECKING:
    from nextcord import Member, User
    from nextcord.abc import Connectable
    from nextcord.client import Client


AUDIO_HZ = DecoderThread.SAMPLING_RATE
AUDIO_CHANNELS = DecoderThread.CHANNELS
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

export_one_methods = {
    Formats.MP3: export_one_with_ffmpeg,
    Formats.MP4: export_one_with_ffmpeg,
    Formats.M4A: export_one_with_ffmpeg,
    Formats.MKA: export_one_with_ffmpeg,
    Formats.MKV: export_one_with_ffmpeg,
    Formats.OGG: export_one_with_ffmpeg,
    Formats.PCM: export_one_as_PCM,
    Formats.WAV: export_one_as_WAV,
}


class Silence:
    """Represents the number of frames where a recording has been silent

    Parameters
    ----------
    frames: :class:`int`
        The number of 20ms frames where this recording was silent

    Attributes
    ----------
    frames: :class:`int`
        The number of 20ms frames where this recording was silent
    milliseconds: :class:`float`
        The relative number of milliseconds based on the frames
    """

    __slots__ = ("frames",)

    def __init__(self, frames: int) -> None:
        self.frames: int = frames

    @property
    def milliseconds(self) -> float:
        return self.frames / (AUDIO_HZ / FRAME_SIZE) * 1000

    def write_to(self, buffer: BufferedIOBase) -> None:
        """Writes the silence to IO

        Parameters
        ----------
        buffer: :class:`BufferedIOBase`
            The buffer for which to write this silence to.
        """
        res, remainder = divmod(self.frames, STRUCT_SIZE)

        # write in a loop as to avoid generating a huge memory buffer
        if res:
            for _ in range(res):
                buffer.write(SILENCE_STRUCT)

        # write the rest
        if remainder:
            buffer.write(SILENCE_STRUCT[: remainder * FRAME_SIZE * AUDIO_CHANNELS])

    @classmethod
    def from_timedelta(cls, silence: int):
        """Creates a Silence object with the desginated timeframe.

        Parameters
        ----------
        silence: :class:`int`
            The number of Hz to convert to silence
            E.g. 48,000 for 1 second of silence when the audio frame size is 48,000Hz
        """
        half_frames = int(silence / FRAME_SIZE)
        return None if half_frames <= 0 else cls(half_frames * AUDIO_CHANNELS)


class RecordingFilter:
    """Represents a filter used to restrict the recording.
    Allowlist overwrites blocklist. If a user is allowlisted and blocklisted, they
    will not be affected by the blocklist. List will only affect the filter
    if they are not empty.

    Parameters
    ----------
    client: Optional[:class:`RecorderClient`]
        The recorder client for which to use this filter on.
        Is optional for creation but not for when used.
    iterable: Optional[:class:`RecorderClient`]
        An optional iterable containing pre-existing data to convert to filter.

    Raises
    ------
    TypeError
        The argument passed for any `user` was not :class:`int`, :class:`User` or :class:`Member`
    """

    __slots__ = ("blocklist", "allowlist", "client")

    def __init__(
        self,
        client=None,
        *,
        blocklist: Optional[Iterable[Union[int, User, Member]]] = None,
        allowlist: Optional[Iterable[Union[int, User, Member]]] = None,
    ) -> None:
        self.blocklist = set()
        self.allowlist = set()

        self.client: Optional[RecorderClient] = client

        if blocklist:
            self.blocklist.update(blocklist)
        if allowlist:
            self.allowlist.update(allowlist)

    def _get_id(self, user: Union[int, User, Member]) -> int:
        if isinstance(user, int):
            return user

        if isinstance(user, (Member, User)):
            return user.id

        raise TypeError("Each user must be of type `int`, `User`, or `Member`")

    def add_blocked(self, user: Union[int, User, Member]) -> None:
        """Add a user to the blocklist filter.
        When set during a recording, their packets will be ignored.
        When set for export, their track will not be exported.

        Parameters
        ----------
        user: Union[:class:`int`, :class:`User`, :class:`Member`]
            The user to add to the blocklist.
        """
        return self.blocklist.add(self._get_id(user))

    def add_allowed(self, user: Union[int, User, Member]) -> None:
        """Add a user to the allowlist filter.
        Audio from user will always pass through.

        Parameters
        ----------
        user: Union[:class:`int`, :class:`User`, :class:`Member`]
            The user to add to the allowlist.
        """
        return self.allowlist.add(self._get_id(user))

    def extend_blocked(self, iterable: Iterable[Union[int, User, Member]]) -> None:
        """Extend the blocklist with an iterable containing more users.

        Parameters
        ----------
        iterable: Iterable[Union[:class:`int`, :class:`User`, :class:`Member`]]
            An iterable containing users to add to the blocklist.
        """
        users = {self._get_id(u) for u in iterable}

        return self.blocklist.update(users)

    def extend_allowed(self, iterable: Iterable[Union[int, User, Member]]) -> None:
        """Extend the allowlist with an iterable containing more users.

        Parameters
        ----------
        iterable: Iterable[Union[:class:`int`, :class:`User`, :class:`Member`]]
            An iterable containing users to add to the allowlist.
        """
        users = {self._get_id(u) for u in iterable}

        return self.allowlist.update(users)

    def remove_blocked(self, user: Union[int, User, Member]) -> None:
        """Remove a user from the blocklist.

        Parameters
        ----------
        user: Union[:class:`int`, :class:`User`, :class:`Member`]
            The user to remove from the blocklist.

        Raises
        ------
        KeyError
            When the user is not found.
        """
        return self.blocklist.remove(self._get_id(user))

    def remove_allowed(self, user: Union[int, User, Member]) -> None:
        """Remove a user from the allowlist.

        Parameters
        ----------
        user: Union[:class:`int`, :class:`User`, :class:`Member`]
            The user to remove from the allowlist.

        Raises
        ------
        KeyError
            When the user is not found.
        """
        return self.allowlist.remove(self._get_id(user))

    def discard_blocked(self, user: Union[int, User, Member]) -> None:
        """Discard a user from the blocklist.

        Parameters
        ----------
        user: Union[:class:`int`, :class:`User`, :class:`Member`]
            The user to discard from the blocklist.
        """
        return self.blocklist.discard(self._get_id(user))

    def discard_allowed(self, user: Union[int, User, Member]) -> None:
        """Discard a user from the allowlist.

        Parameters
        ----------
        user: Union[:class:`int`, :class:`User`, :class:`Member`]
            The user to discard from the allowlist.
        """
        return self.allowlist.discard(self._get_id(user))

    def clear_blocked(self) -> None:
        """Clear all users from the blocklist."""
        self.blocklist.clear()

    def clear_allowed(self) -> None:
        """Clear all users from the allowlist."""
        self.allowlist.clear()

    def is_allowed(self, user: Union[int, User, Member]) -> bool:
        """Whether or not a user should be allowed based on both the blocklist and allowlist

        Parameters
        ----------
        user: Union[:class:`int`, :class:`User`, :class:`Member`]
            The user to check for whether they are allowed.
        """

        uid = self._get_id(user)
        if uid in self.allowlist:
            return True

        return False if uid in self.blocklist else not self.allowlist

    def is_empty(self) -> bool:
        """Whether if the filter has no effect, when it is empty."""
        return not self.blocklist and not self.allowlist


class AudioWriter:
    __slots__ = ("guild_id", "user_id", "buffer", "starting_silence")

    def __init__(self, tmp_type: TmpType, guild_id: int, user_id: int) -> None:
        self.guild_id = guild_id
        self.user_id = user_id

        self.buffer: Union[BufferedWriter, BytesIO]
        self.starting_silence: Optional[Silence] = None

        if tmp_type is TmpType.File:
            self.buffer = open_tmp_file(guild_id, user_id, "wb+")
        elif tmp_type is TmpType.Memory:
            self.buffer = BytesIO()
        else:
            raise TypeError(f"Arg `tmp_type` must be of type `TmpType` not `{type(tmp_type)}`")

    def write(self, data: bytes) -> None:
        """Write bytes to the buffer of this writer."""
        if not self.buffer.closed:
            self.buffer.write(data)

    def close(self) -> None:
        """Closes the buffer of this AudioWriter and removes any temp files if exists."""
        name = (
            self.buffer.name if isinstance(self.buffer, (BufferedRandom, BufferedWriter)) else None
        )
        self.buffer.close()

        if name:
            try:
                os.remove(name)
            except Exception:
                logging.error("Failed to remove tempfile object at path %s", name)

    async def export(
        self,
        audio_format: Formats,
        tmp_type: TmpType,
    ) -> AudioFile:
        """
        Exports the stored references to each writer containing the audio data
        to the specified format.

        audio_format: :class:`Formats`
            The format to export this this container to.
        tmp_type :class:`TmpType`:
            The type of temporary storage to use for exporting. Exporting in memory is **not**
            supported for `m4a` and `mp4` formats.

        Warning
        -------
        Exporting a single writer requires you to make sure the recording is stopped beforehand.
        If a writer is exported while it is being written to, there could be unexepected errors.

        Raises
        ------
        TypeError
            When the audio format is not a supported format from the local enum.

        Returns
        -------
        Dict[:class:`int`, :class:`AudioFile`]
            A map of the each user to their respective exported :class:`AudioFile`.
        """

        if not isinstance(audio_format, Formats):
            raise TypeError(f"audio_format must be of type `Formats` not {type(audio_format)}")

        return await export_one_methods[audio_format](
            self,
            audio_format=audio_format,
            tmp_type=tmp_type,
            decoder=DecoderThread,
        )


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

        # write silence to each user
        for user, u_t in users_to_write.items():
            if silence := Silence.from_timedelta(u_t * AUDIO_HZ):
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
        :class:`AudioWriter`
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

        filtered_writers = [uid for uid in self if not filters.is_allowed(uid)]
        for user_id in filtered_writers:
            self.remove_writer(user_id)

    async def export(
        self,
        audio_format: Formats,
        tmp_type: TmpType,
        filters: Optional[RecordingFilter] = None,
    ) -> Dict[int, AudioFile]:
        """|coro|
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
        Dict[:class:`int`, :class:`AudioFile`]
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
            self_deaf=(deaf if deaf is not None else self.auto_deaf),
            self_mute=bool(mute),
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

        Warning
        -------
        You may only set one data handler as each one acts as a breakpoint.

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
        OngoingRecordingError
            Attempting to set a handler whilst a recording is ongoing.
        MultipleHandlersError
            Multiple handlers were passed when calling this method.
        """

        if self.is_recording:
            raise OngoingRecordingError("Cannot set a data handler whilst recording.")

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

    def toggle_prevent_leakage(self, prevent_leakage: Optional[bool] = None) -> None:
        """
        Attempts to prevent leekage of audio when starting a 2nd recording without reconnecting.

        Warning
        -------
        This feature is unstable and may cause the recording to start slightly delayed, or may
        not work at all in certain untested cases. Use at your own risk!

        Parameters
        ----------
        prevent_leakage: Optional[:class:`bool`]
            The value to set for `prevent_leakage`
        """
        self.prevent_leakage = (
            prevent_leakage if prevent_leakage is not None else self.prevent_leakage is False
        )

    def _wait_for_user_id(self, ssrc: int) -> int:
        ssrc_cache = self.ws.ssrc_cache
        while not (user_data := ssrc_cache.get(ssrc)):
            sleep(0.02)

        return user_data["user_id"]

    def _process_decoded_audio(
        self,
        opus_frame: OpusFrame,
    ) -> None:
        user_id = self._wait_for_user_id(opus_frame.ssrc)
        if not self.filters.is_allowed(user_id):
            return  # ignore their packet

        opus_frame.user_id = user_id
        if self.__decoded_handler:
            self.__decoded_handler(opus_frame)
            # terminate early after calling custom decoded handler method if not set to record too
            if not self.__record_alongside_handler:
                return

        if (
            opus_frame.decoded_data is None
            or self.audio_data is None
            or self.time_tracker is None
            or not self.guild
        ):
            return

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
        return

    def _calc_timestamp(self, ssrc: int, t: float) -> Union[int, float]:
        if not self.time_info:
            return 0
        if not (ti := self.time_info.get(ssrc)):
            return 0

        discord_rtp, clocktime = ti
        return (
            discord_rtp  # original rtp at the saved timestamp
            + (abs(t - clocktime) * FRAME_SIZE * FPS)  # offset to the current timestamp
            - (FRAME_SIZE * min(self.latency * FPS, FPS))  # minus the latency (max 1s)
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
            if not self.filters.is_empty():  # get ssrc to process filters if its not empty
                user_id = self._wait_for_user_id(ssrc)
                if not self.filters.is_allowed(user_id):
                    return  # ignore their packet
                opus_frame.user_id = user_id

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
            if not self.filters.is_empty():
                ssrc = unpack_from(">xxHII", data[:12])[2]
                user_id = self._wait_for_user_id(ssrc)
                if not self.filters.is_allowed(user_id):
                    return None  # ignore their packet

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
        self.decoder = DecoderThread(self)

        if (
            self.__record_alongside_handler  # requires recording alongside
            or self.__decoded_handler  # requires decoding data
            or not self.__handler_set  # normal recording
        ):
            self.decoder.start()

        self.process = Thread(target=self._start_packets_recording)
        self.process.start()

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
        """Toggling whether a recording is paused if there is an ongoing one."""

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
        EmptyRecordingError
            Nothing was recorded.

        Returns
        -------
        :class:`AudioData`
            When export is not specified, you receive the the audio data map
            of each user's id to their respective :class:`AudioWriter`
        Dict[:class:`int`, :class:`AudioFile`]
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

        if audio_data is None:
            raise TmpNotFound("Audio data not found!")

        if not audio_data:
            raise EmptyRecordingError(
                "Nothing was recorded! Cannot return or export empty recording."
            )

        if write_remaining_silence:
            if time_tracker and self.guild:
                time_tracker.write_remaining_silence(t, audio_data, self.tmp_type, self.guild.id)
            else:
                logging.debug(
                    "Unable to write periodic silence due to no `time_tracker` or no `guild`."
                    "Silently ignored."
                )

        if not export_format:
            return audio_data

        if filters:
            return await audio_data.export(export_format, tmp_type, filters)

        if filters is MISSING:
            return await audio_data.export(export_format, tmp_type, self.filters)

        return await audio_data.export(export_format, tmp_type)
