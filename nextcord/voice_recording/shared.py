# SPDX-License-Identifier: MIT

from enum import Enum
from os import getcwd, makedirs
from os.path import dirname
from pathlib import Path

TMP_DIR = ".rectmps"


class TmpType(Enum):
    Memory = 0
    File = 1


class Formats(Enum):
    MP3 = 0
    MP4 = 1
    M4A = 2
    MKA = 3
    MKV = 4
    OGG = 5
    PCM = 6
    WAV = 7


ffmpeg_formats = {
    Formats.MP3: ("mp3", "mp3"),
    Formats.MP4: ("mp4", "mp4"),
    Formats.M4A: ("m4a", "ipod"),
    Formats.MKA: ("mka", "matroska"),
    Formats.MKV: ("mkv", "matroska"),
    Formats.OGG: ("ogg", "ogg"),
    "mp3": ("mp3", "mp3"),
    "mp4": ("mp4", "mp4"),
    "m4a": ("m4a", "ipod"),
    "mka": ("mka", "matroska"),
    "mkv": ("mkv", "matroska"),
    "ogg": ("ogg", "ogg"),
}


def get_ffmpeg_format(format):
    """Attempts to transform the format to an ffmpeg format. Returns passed arg if failed."""
    return (ffmpeg_formats.get(format) or (None, format))[1]


def open_tmp_file(guild_id, user_id, mode):
    path = Path(f"{getcwd()}/{TMP_DIR}/{guild_id}.{user_id}.tmp")

    try:
        return open(path, mode)  # noqa: SIM115

    except FileNotFoundError:
        makedirs(dirname(path), exist_ok=True)  # Create missing dirs
        path.touch(exist_ok=True)  # create missing file
        return open(path, mode)  # noqa: SIM115
