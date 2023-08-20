"""
The MIT License (MIT)

:copyright: (c) 2015-2021 Rapptz
:copyright: (c) 2021-present Tag-Epic
:copyright: (c) 2021-present Nextcord Developers

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


import logging
from nextcord import opus
from time import sleep
import threading
import gc

class DecoderThread(threading.Thread, opus._OpusStruct):
    def __init__(self, recorder):
        super().__init__(daemon=True)

        self.recorder = recorder
        self.decode_queue = []
        self.decoder = {}
        self._end_thread = threading.Event()

    def decode(self, opus_frame):
        self.decode_queue.append(opus_frame)

    def run(self):
        while not self._end_thread.is_set():
            try:
                (
                    sequence,
                    timestamp,
                    received_timestamp,
                    ssrc,
                    decrypted_data
                ) = self.decode_queue.pop(0)
            except IndexError:
                sleep(0.001)
                continue

            try:

                if decrypted_data is None:
                    continue
                else:
                    decoder = self.get_decoder(ssrc)
                    decoded_data = decoder.decode(decrypted_data, fec=False)
            except opus.InvalidArgument:
                print("Error occurred while decoding opus frame.")
                continue

            self.recorder._process_decoded_audio(sequence, timestamp, received_timestamp, ssrc, decoded_data)

    def stop(self):
        while self.decoding:
            sleep(0.1)
            self.decoder = {}
            gc.collect()
            logging.debug("Decoder process killed.")
        self._end_thread.set()

    def get_decoder(self, ssrc) -> opus.Decoder:
        if (d := self.decoder.get(ssrc)) is not None:
            return d
        d = self.decoder[ssrc] = opus.Decoder()
        return d

    @property
    def decoding(self):
        return bool(self.decode_queue)
