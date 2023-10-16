# SPDX-License-Identifier: MIT

from pathlib import Path
from shutil import rmtree
from os import getcwd

from .shared import TMP_DIR


def cleanup_tmp_dir():
    rmtree(
        Path(f"{getcwd()}/{TMP_DIR}"),
        ignore_errors=True
    )