"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present tag-epic

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from pkg_resources import get_distribution, DistributionNotFound
from warnings import warn

__all__ = ("incompatible_libraries", )

class DistributionWarning(RuntimeWarning):
    ...

incompatible_libraries = ["discord.py", "discord", "pyfork", "enhanced-dpy"]

for library in incompatible_libraries:
    try:
        get_distribution(library)
        # Library is installed. Throw a warning
        message = (
                f"{library} is installed which is incompatible with nextcord. "
                f"Please remove this library by using `pip3 uninstall {library}`"
        )

        warn(message, DistributionWarning, stacklevel=0)
    except DistributionNotFound:
        pass
