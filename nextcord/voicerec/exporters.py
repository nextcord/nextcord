# SPDX-License-Identifier: MIT

import os
import subprocess
import wave
from asyncio import get_running_loop
from io import BufferedIOBase, BufferedRandom, BufferedWriter, BytesIO
from platform import system
from typing import Dict, Union

from nextcord import File

from . import opus
from .errors import *
from .shared import *

FLAG = subprocess.CREATE_NO_WINDOW if system() == "Windows" else 0


class AudioFile(File):
    def __init__(self, *args, sync_start: bool = True, starting_silence=None, **kwargs) -> None:
        self.starting_silence = starting_silence if sync_start else None
        super().__init__(*args, **kwargs)

    def close(self) -> None:
        # get file name if it's not a memory record
        name = self.fp.name if isinstance(self.fp, (BufferedRandom, BufferedWriter)) else None
        super().close()

        # delete temp file after closure
        if name:
            os.remove(name)


ffmpeg_default_arg = (
    "ffmpeg "
    "-f s16le "
    f"-ar {opus.DecoderThread.SAMPLING_RATE} "
    "-loglevel error "
    f"-ac {opus.DecoderThread.CHANNELS} "
    f"-i - "
    "-f "  # this is where the format goes
)


# format: (format_extension, output_format)
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
    data = buffer.read()

    buffer.close()  # TODO check memory

    if getattr(buffer, "name", None):
        os.remove(buffer.name)  # type: ignore

    return data


def _write_in_memory(bytes: bytes) -> BytesIO:
    buffer = BytesIO(bytes)
    buffer.seek(0)
    return buffer


def _open_tmp_file(writer, *args):
    f: BufferedWriter = open_tmp_file(writer.guild_id, writer.user_id, "ab+")
    f.seek(0)
    return f


class FFmpeg:
    @staticmethod
    def memory_tmp_conv(audio_format: str, writer):
        try:
            return subprocess.Popen(
                f"{ffmpeg_default_arg} {audio_format} pipe:1",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                creationflags=FLAG,
            ).communicate(_read_and_delete(writer.buffer))[0]
        except FileNotFoundError:
            raise NoFFmpeg(
                "FFmpeg is not installed or aliased improperly. Unable to launch `ffmpeg` command."
            )

    @staticmethod
    def file_tmp_conv(audio_format: str, writer):
        try:
            data = _read_and_delete(writer.buffer)  # must read first to delete file
            process = subprocess.Popen(
                f"{ffmpeg_default_arg} {audio_format} .rectmps/{writer.guild_id}.{writer.user_id}.tmp",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                creationflags=FLAG,
            )
            process.communicate(data)
        except FileNotFoundError:
            raise NoFFmpeg(
                "FFmpeg is not installed or aliased improperly. Unable to launch `ffmpeg` command."
            )


# FFMPEG converts


def _export_all_with_file_tmp(
    audio_data, audio_format: str, sync_start: bool
) -> Dict[int, AudioFile]:
    return {
        user_id: (
            AudioFile(
                _open_tmp_file(writer, FFmpeg.file_tmp_conv(audio_format[1], writer)),
                f"{user_id}.{audio_format[0]}",
                sync_start=sync_start,
                starting_silence=writer.starting_silence,
                force_close=True,
            )
        )
        for (user_id, writer) in audio_data.items()
    }


def _export_all_with_memory_tmp(
    audio_data, audio_format: str, sync_start: bool
) -> Dict[int, AudioFile]:
    return {
        user_id: (
            AudioFile(
                _write_in_memory(FFmpeg.memory_tmp_conv(audio_format[1], writer)),
                f"{user_id}.{audio_format[0]}",
                sync_start=sync_start,
                starting_silence=writer.starting_silence,
                force_close=True,
            )
        )
        for (user_id, writer) in audio_data.items()
    }


export_methods = {
    TempType.File: _export_all_with_file_tmp,
    TempType.Memory: _export_all_with_memory_tmp,
}


async def export_with_ffmpeg(
    audio_data, audio_format: Formats, temp_type: TempType, sync_start: bool
) -> Dict[int, AudioFile]:
    if not isinstance(temp_type, TempType):
        raise InvalidTempType(f"Arg `temp_type` must be of type TempType not `{type(temp_type)}`")

    if not isinstance(audio_format, Formats):
        raise TypeError(f"audio_format must be of type `Formats` not {type(audio_format)}")

    return await get_running_loop().run_in_executor(
        None, export_methods[temp_type], audio_data, ffmpeg_args[audio_format], sync_start
    )


# PCM


def _export_as_PCM(user_id: int, writer, sync_start: bool):
    buffer: Union[BufferedWriter, BytesIO] = writer.buffer

    buffer.seek(0)
    return AudioFile(
        buffer,
        f"{user_id}.pcm",
        sync_start=sync_start,
        starting_silence=writer.starting_silence,
        force_close=True,
    )


async def export_as_PCM(audio_data, *args, sync_start: bool) -> Dict[int, AudioFile]:
    run = get_running_loop().run_in_executor
    return {
        user_id: await run(None, _export_as_PCM, user_id, audio_writer, sync_start)
        for user_id, audio_writer in audio_data.items()
    }


# WAV


def _export_as_WAV(user_id: int, writer, decoder: opus.DecoderThread, sync_start):
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
        sync_start=sync_start,
        starting_silence=writer.starting_silence,
        force_close=True,
    )


async def export_as_WAV(audio_data, *args, sync_start: bool) -> Dict[int, AudioFile]:
    decoder = audio_data.decoder
    run = get_running_loop().run_in_executor
    return {
        user_id: await run(None, _export_as_WAV, user_id, audio_writer, decoder, sync_start)
        for user_id, audio_writer in audio_data.items()
    }
