.. _discord_ext_voicerecording:

``nextcord.ext.voicerecording``
====================================================

.. versionadded:: 2.0.0

Helps you recording voice to files with specified Encodings



.. _ext_voicerecording_api:

API Reference
---------------

FileSink
~~~~~~~~~~~~~~~~

.. attributetable:: nextcord.ext.voicerecording.FileSink

.. autoclass:: nextcord.ext.voicerecording.FileSink
    :members:
    :inherited-members:


Cleanup
~~~~~~~~~~~~~~~~~~~
Used to remove all files out of the tempdir

.. autofunction:: nextcord.ext.voicerecording.cleanuptempdir


Encoder
~~~~~~~

.. autoclass:: nextcord.ext.voicerecording.Encoder

    Represents an Encoder used for File Encoding

.. autodata:: nextcord.ext.voicerecording.pcm_encoder
.. autodata:: nextcord.ext.voicerecording.wav_encoder
.. autofunction:: nextcord.ext.voicerecording.generate_ffmpeg_encoder



Encodings
~~~~~~~~~~~~~

.. class:: nextcord.ext.voicerecording.Encodings

    Represents all curently available Encodings for files received by recording

    .. versionadded:: 2.0

    .. attribute:: wav

        Encodes in .wav format

    .. attribute:: mp3

        Encodes in .mp3 format. Requires ffmpeg to be present

    .. attribute:: pcm

        No Encoding. PCM is also what will be used when receiving until formatted

    .. attribute:: mp4

        Encodes in .mp4 format. Requires ffmpeg to be present

    .. attribute:: m4a

        Encodes in .m4a format. Requires ffmpeg to be present

    .. attribute:: mka

        Encodes in .mka format. Requires ffmpeg to be present

    .. attribute:: mkv

        Encodes in .mkv format. Requires ffmpeg to be present

    .. attribute:: ogg

        Encodes in .ogg format. Requires ffmpeg to be present
