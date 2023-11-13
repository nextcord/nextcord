# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import subprocess
import wave
from asyncio import get_running_loop
from io import BufferedIOBase, BufferedRandom, BufferedWriter, BytesIO
from platform import system
from typing import TYPE_CHECKING, Dict, Optional, Union

import nextcord.file as nc_file

from .errors import *
from .opus import DecoderThread
from .shared import *

if TYPE_CHECKING:
    from .core import AudioData, AudioWriter, RecordingFilter, Silence


FLAG = getattr(subprocess, "CREATE_NO_WINDOW", 0) if system() == "Windows" else 0


class AudioFile(nc_file.File):
    """
    This acts exactly like :class:`nextcord.File` other than some extra logic
    to handle closing file temporary storage properly.
    """

    def __init__(self, *args, starting_silence: Optional[Silence] = None, **kwargs) -> None:
        self.starting_silence: Optional[Silence] = starting_silence
        super().__init__(*args, **kwargs)

    def close(self) -> None:
        # get file name if it's not a memory record
        name = self.fp.name if isinstance(self.fp, (BufferedRandom, BufferedWriter)) else None
        super().close()

        # delete tmp file after closure
        if name:
            os.remove(name)


ffmpeg_default_arg = (
    "ffmpeg "
    "-f s16le "
    f"-ar {DecoderThread.SAMPLING_RATE} "
    "-loglevel error "
    f"-ac {DecoderThread.CHANNELS} "
    f"-i - "
    "-f "  # this is where the format goes
)


ffmpeg_args = {
    Formats.MP3: ("mp3", "mp3"),
    Formats.MP4: ("mp4", "mp4"),
    Formats.M4A: ("m4a", "ipod"),
    Formats.MKA: ("mka", "matroska"),
    Formats.MKV: ("mkv", "matroska"),
    Formats.OGG: ("ogg", "ogg"),
}


def _read_and_delete(buffer: BufferedIOBase) -> bytes:
    buffer.seek(0)
    data: bytes = buffer.read()

    buffer.close()
    if getattr(buffer, "name", None):
        os.remove(buffer.name)  # type: ignore

    return data


def _write_in_memory(bytes: bytes) -> BytesIO:
    buffer = BytesIO(bytes)
    buffer.seek(0)
    return buffer


def _open_tmp_file(writer: AudioWriter, *_) -> BufferedWriter:
    f: BufferedWriter = open_tmp_file(writer.guild_id, writer.user_id, "ab+")
    f.seek(0)
    return f


class FFmpeg:
    @staticmethod
    def memory_tmp_conv(audio_format: str, writer: AudioWriter) -> bytes:
        try:
            return subprocess.Popen(
                f"{ffmpeg_default_arg} {audio_format} pipe:1",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                creationflags=FLAG,
            ).communicate(_read_and_delete(writer.buffer))[0]
        except FileNotFoundError as e:
            raise NoFFmpeg(
                "FFmpeg is not installed or aliased improperly. Unable to launch `ffmpeg` command."
            ) from e

    @staticmethod
    def file_tmp_conv(audio_format: str, writer: AudioWriter) -> None:
        try:
            data = _read_and_delete(writer.buffer)  # must read first to delete file
            process = subprocess.Popen(
                f"{ffmpeg_default_arg} {audio_format} {TMP_DIR}/{writer.guild_id}.{writer.user_id}.tmp",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                creationflags=FLAG,
            )
            process.communicate(data)
        except FileNotFoundError as e:
            raise NoFFmpeg(
                "FFmpeg is not installed or aliased improperly. Unable to launch `ffmpeg` command."
            ) from e


# FFMPEG conversion exports


def _export_all_with_file_tmp(audio_data: AudioData, audio_format: str) -> Dict[int, AudioFile]:
    return {
        user_id: (
            AudioFile(
                _open_tmp_file(writer, FFmpeg.file_tmp_conv(audio_format[1], writer)),
                f"{user_id}.{audio_format[0]}",
                starting_silence=writer.starting_silence,
                force_close=True,
            )
        )
        for (user_id, writer) in audio_data.items()
    }


def _export_all_with_memory_tmp(audio_data: AudioData, audio_format: str) -> Dict[int, AudioFile]:
    return {
        user_id: (
            AudioFile(
                _write_in_memory(FFmpeg.memory_tmp_conv(audio_format[1], writer)),
                f"{user_id}.{audio_format[0]}",
                starting_silence=writer.starting_silence,
                force_close=True,
            )
        )
        for (user_id, writer) in audio_data.items()
    }


export_methods = {
    TmpType.File: _export_all_with_file_tmp,
    TmpType.Memory: _export_all_with_memory_tmp,
}


async def export_with_ffmpeg(
    audio_data: AudioData,
    audio_format: Formats,
    tmp_type: TmpType,
    filters: Optional[RecordingFilter] = None,
) -> Dict[int, AudioFile]:
    if not isinstance(tmp_type, TmpType):
        raise TypeError(f"Arg `tmp_type` must be of type `TmpType` not `{type(tmp_type)}`")

    if not isinstance(audio_format, Formats):
        raise TypeError(f"audio_format must be of type `Formats` not {type(audio_format)}")

    audio_data.process_filters(filters)

    return await get_running_loop().run_in_executor(
        None, export_methods[tmp_type], audio_data, ffmpeg_args[audio_format]
    )


# .pcm exports


def _export_as_PCM(user_id: int, writer: AudioWriter) -> AudioFile:
    buffer: Union[BufferedWriter, BytesIO] = writer.buffer

    buffer.seek(0)
    return AudioFile(
        buffer,
        f"{user_id}.pcm",
        starting_silence=writer.starting_silence,
        force_close=True,
    )


async def export_as_PCM(
    audio_data: AudioData, *_, filters: Optional[RecordingFilter] = None
) -> Dict[int, AudioFile]:
    run = get_running_loop().run_in_executor

    audio_data.process_filters(filters)

    return {
        user_id: await run(None, _export_as_PCM, user_id, audio_writer)
        for user_id, audio_writer in audio_data.items()
    }


# .wav exports


def _export_as_WAV(user_id: int, writer: AudioWriter, decoder: DecoderThread) -> AudioFile:
    buffer: Union[BufferedWriter, BytesIO] = writer.buffer

    buffer.seek(0)
    with wave.open(buffer, "wb") as file:
        file.setnchannels(decoder.CHANNELS)
        file.setsampwidth(decoder.SAMPLE_SIZE // decoder.CHANNELS)
        file.setframerate(decoder.SAMPLING_RATE)

    buffer.seek(0)
    return AudioFile(
        buffer,
        f"{user_id}.wav",
        starting_silence=writer.starting_silence,
        force_close=True,
    )


async def export_as_WAV(
    audio_data: AudioData, *_, filters: Optional[RecordingFilter] = None
) -> Dict[int, AudioFile]:
    decoder = audio_data.decoder
    run = get_running_loop().run_in_executor

    audio_data.process_filters(filters)

    return {
        user_id: await run(None, _export_as_WAV, user_id, audio_writer, decoder)
        for user_id, audio_writer in audio_data.items()
    }
