from pkg_resources import get_distribution
from warnings import warn
__all__ = ("incompatible_libraries", )
incompatible_libraries = ["discord.py", "discord", "pyfork", "enhanced-dpy"]

for library in incompatible_libraries:
    try:
        get_distribution(library)
        # Library is installed. Throw a warning
        warn(f"{library} is installed which is incompatible with nextcord. We strongly encourage you to remove this. This can be removed by using `pip3 uninstall {library}`")
    except:
        pass
