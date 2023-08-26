# SPDX-License-Identifier: MIT


import gc
import logging
import threading
from time import sleep

from nextcord import opus


class DecoderThread(threading.Thread, opus._OpusStruct):
    def __init__(self, recorder) -> None:
        super().__init__(daemon=True)

        self.recorder = recorder
        self.decode_queue = []
        self.decoder = {}
        self._end_thread = threading.Event()

    def decode(self, opus_frame) -> None:
        self.decode_queue.append(opus_frame)

    def run(self) -> None:
        while not self._end_thread.is_set():
            try:
                (
                    sequence,
                    timestamp,
                    received_timestamp,
                    ssrc,
                    decrypted_data,
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

            self.recorder._process_decoded_audio(
                sequence, timestamp, received_timestamp, ssrc, decoded_data
            )

    def stop(self) -> None:
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
