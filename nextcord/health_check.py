# SPDX-License-Identifier: MIT

from importlib.metadata import PackageNotFoundError, metadata
from warnings import warn

__all__ = ("incompatible_libraries",)


class DistributionWarning(RuntimeWarning):
    ...


incompatible_libraries = ["discord.py", "discord", "pyfork", "enhanced-dpy", "py-cord"]

for library in incompatible_libraries:
    try:
        metadata(library)
        # Library is installed. Throw a warning
        message = (
            f"{library} is installed which is incompatible with nextcord. "
            f"Please remove this library by using `pip3 uninstall {library}`"
        )

        warn(message, DistributionWarning, stacklevel=0)
    except PackageNotFoundError:
        pass
