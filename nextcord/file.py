# SPDX-License-Identifier: MIT

from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING, Optional, Union

__all__ = ("File",)


class File:
    r"""A parameter object used for :meth:`abc.Messageable.send`
    for sending file objects.

    .. note::

        File objects are single use and are not meant to be reused in
        multiple :meth:`abc.Messageable.send`\s.

    Parameters
    ----------

    fp: Union[str, bytes, os.PathLike, io.BufferedIOBase]
        A file-like object opened in binary mode and read mode
        or a filename representing a file in the hard drive to
        open.

        .. note::

            If the file-like object passed is opened via ``open`` then the
            modes 'rb' should be used.

            To pass binary data, consider usage of ``io.BytesIO``.
    filename: Optional[:class:`str`]
        The filename to display when uploading to Discord.
        If this is not given then it defaults to ``fp.name`` or if ``fp`` is
        a string then the ``filename`` will default to the string given.
    description: Optional[:class:`str`]
        The description for the file. This is used to display alternative text
        in the Discord client.
    spoiler: :class:`bool`
        Whether the attachment is a spoiler.
    force_close: :class:`bool`
        Whether to forcibly close the bytes used to create the file
        when ``.close()`` is called.
        This will also make the file bytes unusable by flushing it from
        memory after it is sent once.
        Enable this if you don't wish to reuse the same bytes.

        .. versionadded:: 2.2

    Attributes
    ----------
    fp: Union[:class:`io.BufferedReader`, :class:`io.BufferedIOBase`]
        A file-like object opened in binary mode and read mode.
        This will be a :class:`io.BufferedIOBase` if an
        object of type :class:`io.IOBase` was passed, or a
        :class:`io.BufferedReader` if a filename was passed.
    filename: Optional[:class:`str`]
        The filename to display when uploading to Discord.
    description: Optional[:class:`str`]
        The description for the file. This is used to display alternative text
        in the Discord client.
    spoiler: :class:`bool`
        Whether the attachment is a spoiler.
    force_close: :class:`bool`
        Whether to forcibly close the bytes used to create the file
        when ``.close()`` is called.
        This will also make the file bytes unusable by flushing it from
        memory after it is sent or used once.
        Enable this if you don't wish to reuse the same bytes.

        .. versionadded:: 2.2
    """

    __slots__ = (
        "fp",
        "filename",
        "spoiler",
        "force_close",
        "_original_pos",
        "_owner",
        "_closer",
        "description",
    )

    if TYPE_CHECKING:
        fp: Union[io.BufferedReader, io.BufferedIOBase]
        filename: Optional[str]
        description: Optional[str]
        spoiler: bool
        force_close: bool

    def __init__(
        self,
        fp: Union[str, bytes, os.PathLike, io.BufferedIOBase],
        filename: Optional[str] = None,
        *,
        description: Optional[str] = None,
        spoiler: bool = False,
        force_close: bool = False,
    ) -> None:
        if isinstance(fp, io.IOBase):
            if not (fp.seekable() and fp.readable()):
                raise ValueError(f"File buffer {fp!r} must be seekable and readable")
            self.fp = fp
            self._original_pos = fp.tell()
            self._owner = False
        else:
            self.fp = open(fp, "rb")
            self._original_pos = 0
            self._owner = True

        self.force_close = force_close

        # aiohttp only uses two methods from IOBase
        # read and close, since I want to control when the files
        # close, I need to stub it so it doesn't close unless
        # I tell it to
        self._closer = self.fp.close
        self.fp.close = lambda: None

        if filename is None:
            if isinstance(fp, str):
                _, self.filename = os.path.split(fp)
            else:
                self.filename = getattr(fp, "name", None)
        else:
            self.filename = filename

        self.description = description

        if spoiler and self.filename is not None and not self.filename.startswith("SPOILER_"):
            self.filename = "SPOILER_" + self.filename

        self.spoiler = spoiler or (
            self.filename is not None and self.filename.startswith("SPOILER_")
        )

    def reset(self, *, seek: Union[int, bool] = True) -> None:
        # The `seek` parameter is needed because
        # the retry-loop is iterated over multiple times
        # starting from 0, as an implementation quirk
        # the resetting must be done at the beginning
        # before a request is done, since the first index
        # is 0, and thus false, then this prevents an
        # unnecessary seek since it's the first request
        # done.
        if seek:
            self.fp.seek(self._original_pos)

    def close(self) -> None:
        self.fp.close = self._closer
        if self._owner or self.force_close:
            self._closer()
