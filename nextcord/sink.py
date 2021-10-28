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
import asyncio
import datetime
import os
import struct
import sys
from typing import Optional, Any

from .backoff import ExponentialBackoff
from .errors import ClientException

__all__ = (
    'FiltersMixin',
    'Sink',
    'AudioData',
    'RawData',
)

from .ext import tasks
from .ext.tasks import LF

from .utils import MISSING

if sys.platform != 'win32':
    CREATE_NO_WINDOW = 0
else:
    CREATE_NO_WINDOW = 0x08000000

default_filters = {
    'time': 0,
    'users': [],
    'max_size': 0,
}


class _Scheduler(tasks.Loop):
    def __init__(self, coro: LF, time: datetime.datetime):
        super().__init__(coro=coro,
                         seconds=1,
                         hours=0,
                         minutes=0,
                         time=MISSING,
                         count=1,
                         reconnect=True,
                         loop=MISSING)
        self.scheduledtime = time

    def _get_next_sleep_time(self) -> datetime.datetime:
        return self.scheduledtime

    async def _loop(self, *args: Any, **kwargs: Any) -> None:
        backoff = ExponentialBackoff()
        await self._call_loop_function('before_loop')
        self._last_iteration_failed = False
        now = datetime.datetime.now(datetime.timezone.utc)
        if self.scheduledtime > now:
            self._next_iteration = self.scheduledtime
        else:
            self._next_iteration = now
        try:
            await self._try_sleep_until(self._next_iteration)
            while True:
                if not self._last_iteration_failed:
                    self._last_iteration = self._next_iteration
                    self._next_iteration = self._get_next_sleep_time()
                try:
                    await self.coro(*args, **kwargs)
                    self._last_iteration_failed = False
                except self._valid_exception:
                    self._last_iteration_failed = True
                    if not self.reconnect:
                        raise
                    await asyncio.sleep(backoff.delay())
                else:
                    await self._try_sleep_until(self._next_iteration)

                    if self._stop_next_iteration:
                        return

                    now = datetime.datetime.now(datetime.timezone.utc)
                    if now > self._next_iteration:
                        self._next_iteration = now
                        if self._time is not MISSING:
                            self._prepare_time_index(now)

                    self._current_loop += 1
                    if self._current_loop == self.count:
                        break
        except asyncio.CancelledError:
            self._is_being_cancelled = True
            raise
        except Exception as exc:
            self._has_failed = True
            await self._call_loop_function('error', exc)
            raise exc
        finally:
            await self._call_loop_function('after_loop')
            self._handle.cancel()
            self._is_being_cancelled = False
            self._current_loop = 0
            self._stop_next_iteration = False
            self._has_failed = False


class FiltersMixin:
    def __init__(self, **kwargs):
        self.filtered_users = kwargs.get('users', default_filters['users'])
        self.seconds = kwargs.get('time', default_filters['time'])
        self.max_size = kwargs.get('max_size', default_filters['max_size'])
        self.finished = False
        self.secondsfiler = MISSING

    @staticmethod
    def filter_decorator(func):  # Contains all filters
        def _filter(self, data, user):
            if not self.filtered_users or user in self.filtered_users:
                return func(self, data, user)

        return _filter

    def init(self, vc):
        if self.seconds > 0:
            self.secondsfiler = _Scheduler(coro=self.wait_and_stop,
                                           time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                                               seconds=self.seconds))
            self.secondsfiler.start()

    async def wait_and_stop(self):
        if not self.finished:
            await self.vc.stop_listening()


class RawData:
    """Handles raw data from Discord so that it can be decrypted and decoded to be used.

    .. versionadded:: 2.0
    """

    def __init__(self, data, client):
        self.data = bytearray(data)
        self.client = client
        self.header = data[:12]
        self.data = self.data[12:]
        self.sequence, self.timestamp, self.ssrc = struct.Struct('>xxHII').unpack_from(self.header)
        self.decrypted_data = getattr(self.client, '_decrypt_' + self.client.mode)(self.header, self.data)
        self.decoded_data = None
        self.user_id = None


class AudioData:
    """Handles data that's been completely decrypted and decoded and is ready to be saved to file.

    .. versionadded:: 2.0
    """

    def __init__(self, file):
        self.file = open(file, 'ab')
        self.dir_path = os.path.split(file)[0]
        self.finished = False
        self._size = 0

    def write(self, data):
        if self.finished:
            raise ClientException("This AudioData is already finished writing.")
        try:
            self._size += self.file.write(data)
        except ValueError:
            pass

    def cleanup(self):
        if self.finished:
            raise ClientException("This AudioData is already finished writing.")
        self.file.close()
        self.file = os.path.join(self.dir_path, self.file.name)
        self.finished = True

    def on_format(self, encoding):
        if not self.finished:
            raise ClientException("This AudioData is still writing.")
        if encoding.name != 'pcm':
            name = os.path.split(self.file)[1]
            name = name.split('.')[0] + f'.{encoding.name}'
            self.file = os.path.join(self.dir_path, name)

    def __len__(self):
        return self._size


class Sink(FiltersMixin):
    """A Sink handling all decoded voice packets.

    .. versionadded:: 2.0

    Parameters
    ---------
    coro:
        A coroutine to handle data input. Should take to positional arguments data and user. Data will be pcm, user the
        user id

    filters:
        The filters to apply. Should be a dict. Currently supported are time and users. Time takes an integer
        as amount of seconds after listening shall stop, users should be a list of user ids to ignore (ints). Please
        note that converting to
        other formats might change the file size a bit

    Raises
    ------
    ClientException
        An invalid encoding type was specified.
    """

    def __init__(self, *, coro: LF, filters: Optional[dict] = MISSING):
        if filters is MISSING:
            filters = default_filters
        self.filters = filters
        FiltersMixin.__init__(self, **self.filters)
        self.coro = coro
        self.loop = asyncio.get_running_loop()
        self.vc = None

    def init(self, vc):  # called under start_listening
        self.vc = vc
        super().init(vc)

    @FiltersMixin.filter_decorator
    def write(self, data, user):
        asyncio.run_coroutine_threadsafe(self.coro(data, user), self.loop)

    def cleanup(self):
        """
        Stops time filter if present
        """
        self.finished = True
        try:
            self.secondsfiler.stop()
        except Exception:
            pass
