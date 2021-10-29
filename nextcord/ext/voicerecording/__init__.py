"""
The MIT License (MIT)

Copyright (c) 2021-present Tag-Epic
Copyright (c) 2015-present Rapptz
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
import datetime
import os
import random
import shutil
import tempfile
import typing
from typing import Optional, List, AnyStr
from .encoder import *


from nextcord.errors import ClientException
from nextcord.sink import *
from nextcord.sink import default_filters

__all__ = (
    'FileSink',
    'cleanuptempdir',
    'Encodings',
    'Encoder',
    'generate_ffmpeg_encoder',
    'pcm_encoder',
    'wav_encoder'
)

from nextcord.utils import MISSING


class FileSink(Sink):
    """A Sink "stores" all the audio data into a file.

    .. versionadded:: 2.0

    Parameters
    ----------
    encoding: :class:`Encodings`
        The encoding to use. Valid types include wav, mp3, and pcm (even though it's not an actual encoding).

    filters:
        The filters to apply. Should be a dict. Currently supported are time, users and max_size. Time takes an integer
        as amount of seconds after listening shall stop, users should be a list of user ids to ignore (ints) and
        max_size is a limit for the max file of the pcms (bytes amounts as int). Please note that converting to
        other formats might change the file size a bit

    Raises
    ------
    ClientException
        An invalid encoding type was specified.
    """

    def __init__(self, *, encoding: Encoder = pcm_encoder, filters: Optional[dict] = MISSING,
                 tempfolder: Optional[os.PathLike] = MISSING):
        if filters is MISSING:
            filters = default_filters
        self.filters = filters
        FiltersMixin.__init__(self, **self.filters)

        self.encoding: Encoder = encoding
        self.vc = None
        self.audio_data: typing.Dict[int, AudioData] = {}
        if tempfolder is MISSING:
            tempfolder = tempfile.gettempdir() + "/nextcord/voicerecs/pcmtemps"
        tempfolder = os.path.abspath(tempfolder + "/" + hex(id(self)))
        rint = str(random.randint(-100000, 100000))
        maxcounter = 5
        while os.path.exists(tempfolder+rint):
            if maxcounter < 0:
                raise FileExistsError("Unable to create a new tempdir. pls. consider cleaning them up")
            maxcounter -= 1
            rint = str(random.randint(-100000, 100000))
        self.file_path = tempfolder+rint
        os.makedirs(self.file_path, exist_ok=True)

    def init(self, vc):  # called under start_listening
        self.vc = vc
        super().init(vc)

    @FiltersMixin.filter_decorator
    def write(self, data, user):
        if user not in self.audio_data:
            ssrc = self.vc.get_ssrc(user)
            file = os.path.join(self.file_path, f'{ssrc}-{datetime.datetime.utcnow().timestamp()}.pcm')
            self.audio_data.update({user: AudioData(file)})

        file = self.audio_data[user]
        if self.max_size <= 0 or self.max_size >= len(file) + 3840:
            file.write(data)

    def cleanup(self):
        """Formats audio and ends listening"""
        self.finished = True
        for file in self.audio_data.values():
            file.cleanup()
            self.format_audio(file)
        try:
            self.secondsfiler.stop()
        except Exception:
            pass

    def format_audio(self, audio):
        """Formats one Audio File"""
        if self.vc.listening:
            raise ClientException("Audio may only be formatted after listening is finished.")
        self.encoding.func(self, audio)
        audio.on_format(self.encoding)

    def destroy(self):
        """Removes its tempdirectory
        Will delete this sink
        """
        shutil.rmtree(self.file_path, ignore_errors=True)
        del self

    def get_files(self) -> List[AnyStr]:
        """Gives back all file paths
        Note: These will be temporary pcm files until cleanup is called
        """
        return [os.path.realpath(x.file) for x in self.audio_data.values()]


def cleanuptempdir(tempfolder: Optional[os.PathLike] = MISSING):
    """Attempts to remove all files out of the voicerecs tempfolder

    .. versionadded:: 2.0
    """
    if tempfolder is MISSING:
        tempfolder = tempfile.gettempdir() + "/nextcord/voicerecs/pcmtemps"
    shutil.rmtree(tempfolder, ignore_errors=True)
