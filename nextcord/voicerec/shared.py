"""
"""

from enum import Enum
from os import makedirs
from os.path import dirname
from pathlib import Path


class TempType(Enum):
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


format_exports = {
    Formats.MP3: "export_with_ffmpeg",
    Formats.MP4: "export_with_ffmpeg",
    Formats.M4A: "export_with_ffmpeg",
    Formats.MKA: "export_with_ffmpeg",
    Formats.MKV: "export_with_ffmpeg",
    Formats.OGG: "export_with_ffmpeg",
    Formats.PCM: "export_as_PCM",
    Formats.WAV: "export_as_WAV",
}


def open_tmp_file(guild_id, user_id, mode):
    path = Path(f".rectmps/{guild_id}.{user_id}.tmp")

    try:
        return open(path, mode)

    except FileNotFoundError:
        makedirs(dirname(path), exist_ok=True)  # Create missing dirs
        path.touch(exist_ok=True)  # create missing file
        return open(path, mode)
