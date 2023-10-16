# SPDX-License-Identifier: MIT

from os import getcwd
from pathlib import Path
from shutil import rmtree

from .shared import TMP_DIR


def cleanup_tmp_dir() -> None:
    rmtree(Path(f"{getcwd()}/{TMP_DIR}"), ignore_errors=True)
