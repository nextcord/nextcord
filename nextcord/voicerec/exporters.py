import os
import wave
from io import BufferedRandom, BufferedWriter, BytesIO

from nextcord import File

from . import opus


class AudioFile(File):
    def close(self) -> None:
        name = self.fp.name if isinstance(self.fp, BufferedRandom) else None
        super().close()

        # delete temp file after closure
        if name:
            os.remove(name)


# MP3


def export_as_MP3(audio_data) -> None:
    ...


# MP4


def export_as_MP4(audio_data) -> None:
    ...


# M4A


def export_as_M4A(audio_data) -> None:
    ...


# MKA


def export_as_MKA(audio_data) -> None:
    ...


# MKV


def export_as_MKV(audio_data) -> None:
    ...


# OGG


def export_as_OGG(audio_data) -> None:
    ...


# PCM


def _export_as_PCM(user_id: int, data):
    buffer: BufferedWriter | BytesIO = data.buffer
    buffer.seek(0)
    return AudioFile(buffer, f"{user_id}.pcm", force_close=True)


def export_as_PCM(audio_data) -> dict[int, AudioFile]:
    return {
        user_id: _export_as_PCM(user_id, audio_writer)
        for user_id, audio_writer in audio_data.items()
    }


# WAV


def _export_as_WAV(user_id: int, data, decoder: opus.DecoderThread):
    buffer: BufferedWriter | BytesIO = data.buffer

    buffer.seek(0)
    with wave.open(buffer, "wb") as file:
        file.setnchannels(decoder.CHANNELS)
        file.setsampwidth(decoder.SAMPLE_SIZE // decoder.CHANNELS)
        file.setframerate(decoder.SAMPLING_RATE)

    buffer.seek(0)
    return AudioFile(buffer, f"{user_id}.wav", force_close=True)


def export_as_WAV(audio_data) -> dict[int, AudioFile]:
    decoder = audio_data.decoder
    return {
        user_id: _export_as_WAV(user_id, audio_writer, decoder)
        for user_id, audio_writer in audio_data.items()
    }
