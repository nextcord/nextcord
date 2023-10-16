# SPDX-License-Identifier: MIT

from enum import Enum
from os import makedirs, getcwd
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


def open_tmp_file(guild_id, user_id, mode):
    path = Path(f"{getcwd()}/{TMP_DIR}/{guild_id}.{user_id}.tmp")

    try:
        return open(path, mode)

    except FileNotFoundError:
        makedirs(dirname(path), exist_ok=True)  # Create missing dirs
        path.touch(exist_ok=True)  # create missing file
        return open(path, mode)
