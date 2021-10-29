import os
import subprocess
import sys
import wave

from nextcord.enums import Enum
from nextcord.errors import ClientException

if sys.platform != 'win32':
    CREATE_NO_WINDOW = 0
else:
    CREATE_NO_WINDOW = 0x08000000

__all__ = (
    'Encodings',
    'Encoder',
    'generate_ffmpeg_encoder',
    'pcm_encoder',
    'wav_encoder'
)


class Encodings(Enum):
    # https://trac.ffmpeg.org/wiki/Encode/HighQualityAudio
    mp3 = 'mp3'
    mp4 = 'mp4'
    ogg = 'ogg'
    mkv = 'mkv'
    mka = 'mka'
    m4a = 'm4a'


class Encoder:
    """Used to define how to encode recorded data"""

    def __init__(self, func, name: str):
        self.func = func
        self.name = name


def pcm_encode(sink, audio):
    return


def wav_encode(sink, audio):
    with open(audio.file, 'rb') as pcm:
        data = pcm.read()
        pcm.close()

    wav_file = audio.file.split('.')[0] + '.wav'
    with wave.open(wav_file, 'wb') as f:
        f.setnchannels(sink.vc.decoder.CHANNELS)
        f.setsampwidth(sink.vc.decoder.SAMPLE_SIZE // sink.vc.decoder.CHANNELS)
        f.setframerate(sink.vc.decoder.SAMPLING_RATE)
        f.writeframes(data)
        f.close()

    os.remove(audio.file)


def generate_ffmpeg_encoder(type: Encodings) -> Encoder:
    """Generates an Encoder which uses FFMPEG to 
    encode the data to the specified type
    """

    def encode(sink, audio):
        new_file = audio.file.split('.')[0] + '.' + type.value
        args = ['ffmpeg', '-f', 's16le', '-ar', '48000', '-ac', '2', '-i', audio.file, new_file]
        if os.path.exists(new_file):
            raise FileExistsError(f"The file {new_file} already exists. Unable to convert to it. "
                                  f"PCM file cna be found at {audio.file}")
            # process will get stuck asking whether or not to overwrite, if file already exists.
        try:
            process = subprocess.Popen(args, creationflags=CREATE_NO_WINDOW)
        except FileNotFoundError:
            raise ClientException('ffmpeg was not found.') from None
        except subprocess.SubprocessError as exc:
            raise ClientException('Popen failed: {0.__class__.__name__}: {0}'.format(exc)) from exc
        process.wait()

        os.remove(audio.file)

    return Encoder(encode, type.value)


pcm_encoder = Encoder(pcm_encode, 'pcm')
wav_encoder = Encoder(wav_encode, 'wav')
