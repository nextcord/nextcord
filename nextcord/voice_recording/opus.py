# SPDX-License-Identifier: MIT

from __future__ import annotations

import gc
import logging
from threading import Event, Thread
from time import sleep
from typing import TYPE_CHECKING, Dict

import nextcord as nc

if TYPE_CHECKING:
    from .core import OpusFrame, RecorderClient


class DecoderThread(Thread, nc.opus._OpusStruct):
    def __init__(self, recorder) -> None:
        super().__init__(daemon=True)

        self.recorder: RecorderClient = recorder
        self.decode_queue: list[OpusFrame] = []
        self.decoder: Dict[int, nc.opus.Decoder] = {}
        self._end = Event()

    def start(self) -> None:
        self._end = Event()
        super().start()

    def decode(self, opus_frame) -> None:
        self.decode_queue.append(opus_frame)

    def run(self) -> None:
        while not self._end.is_set():
            try:
                opus_frame: OpusFrame = self.decode_queue.pop(0)

            except IndexError:
                sleep(0.001)
                continue

            try:
                if opus_frame.decrypted_data is None:
                    continue

                decoder = self.get_decoder(opus_frame.ssrc)
                opus_frame.decoded_data = decoder.decode(opus_frame.decrypted_data, fec=False)
            except nc.InvalidArgument:
                print("Error occurred while decoding opus frame.")
                continue

            self.recorder._process_decoded_audio(opus_frame)

    def stop(self) -> None:
        self._end.set()
        self.decode_queue.clear()
        self.decoder.clear()
        gc.collect()
        logging.debug("Decoder process killed.")

    def get_decoder(self, ssrc) -> nc.opus.Decoder:
        if (d := self.decoder.get(ssrc)) is not None:
            return d
        d = self.decoder[ssrc] = nc.opus.Decoder()
        return d
