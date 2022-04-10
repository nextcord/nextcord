import contextlib
from pkg_resources import get_distribution, DistributionNotFound
from warnings import warn

__all__ = ("incompatible_libraries",)


class DistributionWarning(RuntimeWarning):
    ...


incompatible_libraries = ["discord.py", "discord", "pyfork", "enhanced-dpy", "py-cord"]

for library in incompatible_libraries:
    with contextlib.suppress(DistributionNotFound):
        get_distribution(library)
        # Library is installed. Throw a warning
        message = (
            f"{library} is installed which is incompatible with nextcord. "
            f"Please remove this library by using `pip3 uninstall {library}`"
        )

        warn(message, DistributionWarning, stacklevel=0)
