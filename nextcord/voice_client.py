# SPDX-License-Identifier: MIT
"""
Some documentation to refer to:

- Our main web socket (mWS) sends opcode 4 with a guild ID and channel ID.
- The mWS receives VOICE_STATE_UPDATE and VOICE_SERVER_UPDATE.
- We pull the session_id from VOICE_STATE_UPDATE.
- We pull the token, endpoint and server_id from VOICE_SERVER_UPDATE.
- Then we initiate the voice web socket (vWS) pointing to the endpoint.
- We send opcode 0 with the user_id, server_id, session_id and token using the vWS.
- The vWS sends back opcode 2 with an ssrc, port, modes(array) and hearbeat_interval.
- We send a UDP discovery packet to endpoint:port and receive our IP and our port in LE.
- Then we send our IP and port via vWS with opcode 1.
- When that's all done, we receive opcode 4 from the vWS.
- Finally we can transmit data to endpoint:port.
"""

from __future__ import annotations

import asyncio
import logging
import socket
import struct
import threading
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, Union, cast

from . import opus, utils
from .backoff import ExponentialBackoff
from .errors import ClientException, ConnectionClosed
from .gateway import *
from .player import AudioPlayer, AudioSource
from .utils import MISSING

if TYPE_CHECKING:
    import dave

    from . import abc
    from .client import Client
    from .guild import Guild
    from .opus import Encoder
    from .state import ConnectionState
    from .types.voice import (
        GuildVoiceState as GuildVoiceStatePayload,
        SupportedModes,
        VoiceServerUpdate as VoiceServerUpdatePayload,
    )
    from .user import ClientUser

    nacl = MISSING


has_nacl: bool

try:
    import nacl.secret

    has_nacl = True
except ImportError:
    has_nacl = False

has_dave: bool

try:
    import dave

    has_dave = True
except ImportError:
    has_dave = False

__all__ = (
    "VoiceClient",
    "VoiceProtocol",
)


_log = logging.getLogger(__name__)


class VoiceProtocol:
    """A class that represents the Discord voice protocol.

    This is an abstract class. The library provides a concrete implementation
    under :class:`VoiceClient`.

    This class allows you to implement a protocol to allow for an external
    method of sending voice, such as Lavalink_ or a native library implementation.

    These classes are passed to :meth:`abc.Connectable.connect <VoiceChannel.connect>`.

    .. _Lavalink: https://github.com/freyacodes/Lavalink

    Parameters
    ----------
    client: :class:`Client`
        The client (or its subclasses) that started the connection request.
    channel: :class:`abc.Connectable`
        The voice channel that is being connected to.
    """

    def __init__(self, client: Client, channel: abc.Connectable) -> None:
        self.client: Client = client
        self.channel: abc.Connectable = channel

    async def on_voice_state_update(self, data: GuildVoiceStatePayload) -> None:
        """|coro|

        An abstract method that is called when the client's voice state
        has changed. This corresponds to ``VOICE_STATE_UPDATE``.

        Parameters
        ----------
        data: :class:`dict`
            The raw `voice state payload`__.

            .. _voice_state_update_payload: https://discord.com/developers/docs/resources/voice#voice-state-object

            __ voice_state_update_payload_
        """
        raise NotImplementedError

    async def on_voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        """|coro|

        An abstract method that is called when initially connecting to voice.
        This corresponds to ``VOICE_SERVER_UPDATE``.

        Parameters
        ----------
        data: :class:`dict`
            The raw `voice server update payload`__.

            .. _voice_server_update_payload: https://discord.com/developers/docs/topics/gateway#voice-server-update-voice-server-update-event-fields

            __ voice_server_update_payload_
        """
        raise NotImplementedError

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        """|coro|

        An abstract method called when the client initiates the connection request.

        When a connection is requested initially, the library calls the constructor
        under ``__init__`` and then calls :meth:`connect`. If :meth:`connect` fails at
        some point then :meth:`disconnect` is called.

        Within this method, to start the voice connection flow it is recommended to
        use :meth:`Guild.change_voice_state` to start the flow. After which,
        :meth:`on_voice_server_update` and :meth:`on_voice_state_update` will be called.
        The order that these two are called is unspecified.

        Parameters
        ----------
        timeout: :class:`float`
            The timeout for the connection.
        reconnect: :class:`bool`
            Whether reconnection is expected.
        """
        raise NotImplementedError

    async def disconnect(self, *, force: bool) -> None:
        """|coro|

        An abstract method called when the client terminates the connection.

        See :meth:`cleanup`.

        Parameters
        ----------
        force: :class:`bool`
            Whether the disconnection was forced.
        """
        raise NotImplementedError

    def cleanup(self) -> None:
        """This method *must* be called to ensure proper clean-up during a disconnect.

        It is advisable to call this from within :meth:`disconnect` when you are
        completely done with the voice protocol instance.

        This method removes it from the internal state cache that keeps track of
        currently alive voice clients. Failure to clean-up will cause subsequent
        connections to report that it's still connected.
        """
        key_id, _ = self.channel._get_voice_client_key()
        self.client._connection._remove_voice_client(key_id)


class VoiceClient(VoiceProtocol):
    """Represents a Discord voice connection.

    You do not create these, you typically get them from
    e.g. :meth:`VoiceChannel.connect`.

    Warning
    -------
    In order to use PCM based AudioSources, you must have the opus library
    installed on your system and loaded through :func:`opus.load_opus`.
    Otherwise, your AudioSources must be opus encoded (e.g. using :class:`FFmpegOpusAudio`)
    or the library will not be able to transmit audio.

    Attributes
    ----------
    session_id: :class:`str`
        The voice connection session ID.
    token: :class:`str`
        The voice connection token.
    endpoint: :class:`str`
        The endpoint we are connecting to.
    channel: :class:`abc.Connectable`
        The voice channel connected to.
    loop: :class:`asyncio.AbstractEventLoop`
        The event loop that the voice client is running on.
    """

    endpoint_ip: str
    voice_port: int
    secret_key: List[int]
    ssrc: int
    ip: str
    port: int

    def __init__(self, client: Client, channel: abc.Connectable) -> None:
        if not has_nacl:
            raise RuntimeError("PyNaCl library needed in order to use voice")

        super().__init__(client, channel)
        state = client._connection
        self.token: str = MISSING
        self.socket = MISSING
        self.loop: asyncio.AbstractEventLoop = state.loop
        self._state: ConnectionState = state
        # this will be used in the AudioPlayer thread
        self._connected: threading.Event = threading.Event()

        self._handshaking: bool = False
        self._potentially_reconnecting: bool = False
        self._voice_state_complete: asyncio.Event = asyncio.Event()
        self._voice_server_complete: asyncio.Event = asyncio.Event()

        self.mode: str = MISSING
        self._connections: int = 0
        self.sequence: int = 0
        self.timestamp: int = 0
        self.timeout: float = 0
        self._runner: asyncio.Task = MISSING
        self._player: Optional[AudioPlayer] = None
        self.encoder: Encoder = MISSING
        self._incr_nonce: int = 0
        self.ws: DiscordVoiceWebSocket = MISSING
        self.e2ee_state: Optional[E2EEState] = E2EEState(self) if has_dave else None

    warn_nacl = not has_nacl
    supported_modes: Tuple[SupportedModes, ...] = ("aead_xchacha20_poly1305_rtpsize",)

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild we're connected to, if applicable."""
        return getattr(self.channel, "guild", None)

    @property
    def user(self) -> ClientUser:
        """:class:`ClientUser`: The user connected to voice (i.e. ourselves)."""
        return self._state.user  # type: ignore # [should exist]

    def checked_add(self, attr, value, limit: int) -> None:
        val = getattr(self, attr)
        if val + value > limit:
            setattr(self, attr, 0)
        else:
            setattr(self, attr, val + value)

    # connection related

    async def on_voice_state_update(self, data: GuildVoiceStatePayload) -> None:
        self.session_id = data["session_id"]
        channel_id = cast(Optional[Union[str, int]], data["channel_id"])

        if not self._handshaking or self._potentially_reconnecting:
            # If we're done handshaking then we just need to update ourselves
            # If we're potentially reconnecting due to a 4014, then we need to differentiate
            # a channel move and an actual force disconnect
            if channel_id is None:
                # We're being disconnected so cleanup
                await self.disconnect(force=True)
            else:
                guild = self.guild
                self.channel = channel_id and guild and guild.get_channel(int(channel_id))  # type: ignore
        else:
            self._voice_state_complete.set()

    async def on_voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        if self._voice_server_complete.is_set():
            _log.info(msg="Ignoring extraneous voice server update.")
            return

        self.token = data.get("token")
        self.server_id = int(data["guild_id"])
        endpoint = data.get("endpoint")

        if endpoint is None or self.token is MISSING:
            _log.warning(
                "Awaiting endpoint... This requires waiting. "
                "If timeout occurred considering raising the timeout and reconnecting."
            )
            return

        self.endpoint = endpoint.removeprefix("wss://")

        # This gets set later
        self.endpoint_ip = MISSING

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)

        if not self._handshaking:
            # If we're not handshaking then we need to terminate our previous connection in the websocket
            await self.ws.close(4000)
            return

        self._voice_server_complete.set()

    async def voice_connect(self) -> None:
        # TODO: protocol should be fixed for guild
        await self.channel.guild.change_voice_state(channel=self.channel)  # type: ignore

    async def voice_disconnect(self) -> None:
        _log.info("The voice handshake is being terminated for Channel ID %s (Guild ID %s)", self.channel.id, self.guild.id)  # type: ignore
        await self.channel.guild.change_voice_state(channel=None)  # type: ignore

    def prepare_handshake(self) -> None:
        self._voice_state_complete.clear()
        self._voice_server_complete.clear()
        self._handshaking = True
        _log.info("Starting voice handshake... (connection attempt %d)", self._connections + 1)
        self._connections += 1

    def finish_handshake(self) -> None:
        _log.info("Voice handshake complete. Endpoint found %s", self.endpoint)
        self._handshaking = False
        self._voice_server_complete.clear()
        self._voice_state_complete.clear()

    async def connect_websocket(self) -> None:
        self.ws = await DiscordVoiceWebSocket.from_client(self)
        self._connected.clear()
        while self.ws.secret_key is None:
            await self.ws.poll_event()
        self._connected.set()

    async def connect(self, *, reconnect: bool, timeout: float) -> None:
        _log.info("Connecting to voice...")
        self.timeout = timeout

        for i in range(5):
            self.prepare_handshake()

            # This has to be created before we start the flow.
            futures = [
                self._voice_state_complete.wait(),
                self._voice_server_complete.wait(),
            ]

            # Start the connection flow
            await self.voice_connect()

            try:
                await utils.sane_wait_for(futures, timeout=timeout)
            except asyncio.TimeoutError:
                await self.disconnect(force=True)
                raise

            self.finish_handshake()

            try:
                await self.connect_websocket()
                break
            except (ConnectionClosed, asyncio.TimeoutError):
                if reconnect:
                    _log.exception("Failed to connect to voice... Retrying...")
                    await asyncio.sleep(1 + i * 2.0)
                    await self.voice_disconnect()
                    continue
                raise

        if self._runner is MISSING:
            self._runner = self.loop.create_task(self.poll_voice_ws(reconnect))

    async def potential_reconnect(self) -> bool:
        # Attempt to stop the player thread from playing early
        self._connected.clear()
        self.prepare_handshake()
        self._potentially_reconnecting = True
        try:
            # We only care about VOICE_SERVER_UPDATE since VOICE_STATE_UPDATE can come before we get disconnected
            await asyncio.wait_for(self._voice_server_complete.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            self._potentially_reconnecting = False
            await self.disconnect(force=True)
            return False

        self.finish_handshake()
        self._potentially_reconnecting = False
        try:
            await self.connect_websocket()
        except (ConnectionClosed, asyncio.TimeoutError):
            return False
        else:
            return True

    @property
    def latency(self) -> float:
        """:class:`float`: Latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This could be referred to as the Discord Voice WebSocket latency and is
        an analogue of user's voice latencies as seen in the Discord client.

        .. versionadded:: 1.4
        """
        ws = self.ws
        return float("inf") if not ws else ws.latency

    @property
    def average_latency(self) -> float:
        """:class:`float`: Average of most recent 20 HEARTBEAT latencies in seconds.

        .. versionadded:: 1.4
        """
        ws = self.ws
        return float("inf") if not ws else ws.average_latency

    async def poll_voice_ws(self, reconnect: bool) -> None:
        backoff = ExponentialBackoff()
        while True:
            try:
                await self.ws.poll_event()
            except (ConnectionClosed, asyncio.TimeoutError) as exc:
                if isinstance(exc, ConnectionClosed):
                    # The following close codes are undocumented so I will document them here.
                    # 1000 - normal closure (obviously)
                    # 4014 - voice channel has been deleted.
                    # 4015 - voice server has crashed, we should resume
                    if exc.code == 1000:
                        _log.info("Disconnecting from voice normally, close code %d.", exc.code)
                        await self.disconnect()
                        break
                    if exc.code == 4014:
                        _log.info("Disconnected from voice by force... potentially reconnecting.")
                        successful = await self.potential_reconnect()
                        if not successful:
                            _log.info(
                                "Reconnect was unsuccessful, disconnecting from voice normally..."
                            )
                            await self.disconnect()
                            break
                        continue
                    if exc.code == 4015:
                        _log.info("Disconnected from voice, trying to resume...")
                        try:
                            await self.ws.resume()
                        except asyncio.TimeoutError:
                            _log.info("Could not resume the voice connection... Disconnecting...")
                            if self._connected.is_set():
                                await self.disconnect(force=True)
                        else:
                            _log.info("Successfully resumed voice connection")
                            continue

                if not reconnect:
                    await self.disconnect()
                    raise

                retry = backoff.delay()
                _log.exception("Disconnected from voice... Reconnecting in %.2fs.", retry)
                self._connected.clear()
                await asyncio.sleep(retry)
                await self.voice_disconnect()
                try:
                    await self.connect(reconnect=True, timeout=self.timeout)
                except asyncio.TimeoutError:
                    # at this point we've retried 5 times... let's continue the loop.
                    _log.warning("Could not connect to voice... Retrying...")
                    continue

    async def disconnect(self, *, force: bool = False) -> None:
        """|coro|

        Disconnects this voice client from voice.
        """
        if not force and not self.is_connected():
            return

        self.stop()
        self._connected.clear()

        try:
            if self.ws:
                await self.ws.close()

            await self.voice_disconnect()
        finally:
            self.cleanup()
            if self.socket:
                self.socket.close()

    async def move_to(self, channel: abc.Snowflake) -> None:
        """|coro|

        Moves you to a different voice channel.

        Parameters
        ----------
        channel: :class:`abc.Snowflake`
            The channel to move to. Must be a voice channel.
        """
        await self.channel.guild.change_voice_state(channel=channel)  # type: ignore # still protocol issue

    def is_connected(self) -> bool:
        """Indicates if the voice client is connected to voice."""
        return self._connected.is_set()

    # audio related

    def _get_voice_packet(self, data) -> bytes:
        e2ee_state = self.e2ee_state
        if e2ee_state is not None and e2ee_state.can_encrypt():
            frame = e2ee_state.encrypt(data)

            if frame is None:
                msg = "Failed to encrypt voice packet."
                raise RuntimeError(msg)
        else:
            frame = data

        header = bytearray(12)

        # Formulate rtp header
        header[0] = 0x80
        header[1] = 0x78
        struct.pack_into(">H", header, 2, self.sequence)
        struct.pack_into(">I", header, 4, self.timestamp)
        struct.pack_into(">I", header, 8, self.ssrc)

        encrypt_packet = getattr(self, "_encrypt_" + self.mode)
        return encrypt_packet(header, frame)

    def _encrypt_aead_xchacha20_poly1305_rtpsize(self, header: bytes, data) -> bytes:
        box = nacl.secret.Aead(bytes(self.secret_key))
        nonce = bytearray(24)

        nonce[:4] = struct.pack(">I", self._incr_nonce)
        self.checked_add("_incr_nonce", 1, 4294967295)

        return header + box.encrypt(bytes(data), bytes(header), bytes(nonce)).ciphertext + nonce[:4]

    def play(
        self, source: AudioSource, *, after: Optional[Callable[[Optional[Exception]], Any]] = None
    ) -> None:
        """Plays an :class:`AudioSource`.

        The finalizer, ``after`` is called after the source has been exhausted
        or an error occurred.

        If an error happens while the audio player is running, the exception is
        caught and the audio player is then stopped.  If no after callback is
        passed, any caught exception will be displayed as if it were raised.

        Parameters
        ----------
        source: :class:`AudioSource`
            The audio source we're reading from.
        after: Callable[[Optional[:class:`Exception`]], Any]
            The finalizer that is called after the stream is exhausted.
            This function must have a single parameter, ``error``, that
            denotes an optional exception that was raised during playing.
            If the function is a coroutine, it will be awaited when called.

        Raises
        ------
        ClientException
            Already playing audio or not connected.
        TypeError
            Source is not a :class:`AudioSource` or after is not a callable.
        OpusNotLoaded
            Source is not opus encoded and opus is not loaded.
        """

        if not self.is_connected():
            raise ClientException("Not connected to voice.")

        if self.is_playing():
            raise ClientException("Already playing audio.")

        if not isinstance(source, AudioSource):
            raise TypeError(f"source must be an AudioSource not {source.__class__.__name__}")

        if not self.encoder and not source.is_opus():
            self.encoder = opus.Encoder()

        self._player = AudioPlayer(source, self, after=after)
        self._player.start()

    def is_playing(self) -> bool:
        """Indicates if we're currently playing audio."""
        return self._player is not None and self._player.is_playing()

    def is_paused(self) -> bool:
        """Indicates if we're playing audio, but if we're paused."""
        return self._player is not None and self._player.is_paused()

    def stop(self) -> None:
        """Stops playing audio."""
        if self._player:
            self._player.stop()
            self._player = None

    def pause(self) -> None:
        """Pauses the audio playing."""
        if self._player:
            self._player.pause()

    def resume(self) -> None:
        """Resumes the audio playing."""
        if self._player:
            self._player.resume()

    @property
    def source(self) -> Optional[AudioSource]:
        """Optional[:class:`AudioSource`]: The audio source being played, if playing.

        This property can also be used to change the audio source currently being played.
        """
        return self._player.source if self._player else None

    @source.setter
    def source(self, value: AudioSource) -> None:
        if not isinstance(value, AudioSource):
            raise TypeError(f"Expected AudioSource not {value.__class__.__name__}.")

        if self._player is None:
            raise ValueError("Not playing anything.")

        self._player._set_source(value)

    def send_audio_packet(self, data: bytes, *, encode: bool = True) -> None:
        """Sends an audio packet composed of the data.

        You must be connected to play audio.

        Parameters
        ----------
        data: :class:`bytes`
            The :term:`py:bytes-like object` denoting PCM or Opus voice data.
        encode: :class:`bool`
            Indicates if ``data`` should be encoded into Opus.

        Raises
        ------
        ClientException
            You are not connected.
        opus.OpusError
            Encoding the data failed.
        """

        self.checked_add("sequence", 1, 65535)
        encoded_data = self.encoder.encode(data, self.encoder.SAMPLES_PER_FRAME) if encode else data
        packet = self._get_voice_packet(encoded_data)
        try:
            self.socket.sendto(packet, (self.endpoint_ip, self.voice_port))
        except BlockingIOError:
            _log.warning(
                "A packet has been dropped (seq: %s, timestamp: %s)", self.sequence, self.timestamp
            )

        self.checked_add("timestamp", opus.Encoder.SAMPLES_PER_FRAME, 4294967295)

    def get_max_dave_protocol_version(self) -> int:
        if not has_dave:
            return 0

        return min(
            E2EEState.MAX_SUPPORTED_PROTOCOL_VERSION,
            dave.get_max_supported_protocol_version(),
        )


class E2EEState:
    MAX_SUPPORTED_PROTOCOL_VERSION = 1
    NEW_MLS_GROUP_EPOCH = 1

    def __init__(self, voice_client: VoiceClient) -> None:
        self.voice_client: VoiceClient = voice_client

        # transition_id -> protocol_version
        self._prepared_transitions: dict[int, int] = {}
        # protocol_version -> SignatureKeyPair
        self._transient_keys: dict[int, dave.SignatureKeyPair] = {}
        self._recognised_users: set[int] = {voice_client.user.id}

        self._encryptor: Optional[dave.Encryptor] = None
        self._session: dave.Session = dave.Session(self._handle_mls_failure)

    def can_encrypt(self) -> bool:
        return self._encryptor is not None and self._encryptor.has_key_ratchet()

    def encrypt(self, data: bytes) -> bytes | None:
        if not self._encryptor:
            msg = "Cannot encrypt data, encryptor is not initialised."
            raise RuntimeError(msg)

        return self._encryptor.encrypt(dave.MediaType.audio, self.voice_client.ssrc, data)

    def _handle_mls_failure(self, source: str, reason: str) -> None:
        _log.error("MLS failure in %s: %s", source, reason)

    def add_recognised_user(self, user_id: int) -> None:
        self._recognised_users.add(user_id)

    def remove_recognised_user(self, user_id: int) -> None:
        if user_id == self.voice_client.user.id:
            # Ignore attempts to remove self, always recognise self within an active vc.
            return

        self._recognised_users.discard(user_id)

    async def initialise(self, protocol_version: int) -> None:
        max_version = self.voice_client.get_max_dave_protocol_version()
        if protocol_version > max_version:
            msg = (
                f"Unsupported DAVE protocol version {protocol_version} received from Discord. "
                f"Maximum supported version is {max_version}."
            )
            raise RuntimeError(msg)

        if protocol_version > 0:
            _log.debug(f"Initialising E2EE state with DAVE protocol version {protocol_version}.")

            await self.prepare_epoch(1, protocol_version)
            self._encryptor = dave.Encryptor()
            self._encryptor.assign_ssrc_to_codec(self.voice_client.ssrc, dave.Codec.opus)
        else:
            # Upon receiving this opcode for a transition to protocol version 0, clients immediately transition their send-side encoded transform to passthrough mode.
            await self.prepare_transition(0, 0)

    def _set_ratchet(self, user_id: int, version: int) -> None:
        if user_id != self.voice_client.user.id:
            # We only set up ratchets for ourselves since we don't do decryption.
            return

        if self._session.has_established_group():
            ratchet = self._session.get_key_ratchet(str(user_id))
        else:
            ratchet = None

        _log.debug("Setting up ratchet for user ID %d with protocol version %d.", user_id, version)
        if self._encryptor is None:
            # should never happen
            _log.error("Failed to set up ratchet, encryptor is not initialised.")
            return

        self._encryptor.set_key_ratchet(ratchet)

    async def prepare_transition(self, transition_id: int, protocol_version: int) -> None:
        # "This can occur when:
        # - the call is upgrading/downgrading to/from E2EE (in the initial transition phase),
        # - changing protocol versions,
        # - or when the MLS group is changing."
        # No need to worry about MLS groups here as decryption is not supported.

        self._prepared_transitions[transition_id] = protocol_version

        if transition_id == 0:
            # Upon receiving dave_protocol_prepare_transition opcode (21) with transition_id = 0,
            # the client immediately executes the transition.
            #
            # + This happens also with sole member voice calls.
            self.execute_transition(transition_id)
        else:
            _log.debug("sending ready for transition ID %d", transition_id)
            await self.voice_client.ws.send_dave_protocol_transition_ready(transition_id)

    def execute_transition(self, transition_id: int) -> None:
        version = self._prepared_transitions.pop(transition_id, None)

        if version is None:
            _log.warning(
                "Received unexpected protocol transition execution for ID %d.",
                transition_id,
            )
            return

        _log.debug(
            "Executing protocol transition for ID %d to protocol version %d.",
            transition_id,
            version,
        )

        # https://daveprotocol.com/#downgrade-to-transport-only-encryption
        # receivers temporarily retain the key ratchets for previous protocol epochs
        # for a period of up to ten seconds, in case frames in-flight before transition
        # execution arrive and require decryption.
        if version == 0:
            self._session.reset()

        self._set_ratchet(self.voice_client.user.id, version)

    async def prepare_epoch(self, epoch: int, protocol_version: int) -> None:
        _log.debug("Preparing epoch %d for protocol version %d.", epoch, protocol_version)

        # Receiving Opcode 24 DAVE Protocol Prepare Epoch with epoch = 1 indicates that a new MLS group is being created.
        # Participants must:

        # - prepare a local MLS group with the parameters appropriate for the DAVE protocol version
        # - generate and send Opcode 26 DAVE MLS Key Package to deliver a new MLS key package to the voice gateway

        if epoch == self.NEW_MLS_GROUP_EPOCH:
            channel_id = self.voice_client.channel.id  # type: ignore
            _log.debug("Reinitialising MLS group %d for epoch %d.", channel_id, epoch)

            transient_key = self._transient_keys.get(protocol_version)
            if transient_key is None:
                transient_key = dave.SignatureKeyPair.generate(protocol_version)
                self._transient_keys[protocol_version] = transient_key

            self._session.init(
                version=protocol_version,
                group_id=channel_id,
                self_user_id=str(self.voice_client.user.id),
                transient_key=transient_key,
            )

            key_package = self._session.get_marshalled_key_package()
            await self.voice_client.ws.send_dave_mls_key_package(key_package)

        # When the epoch is greater than 1, the protocol version of the existing MLS group is changing.
        # No version above 1 is supported so no logic here yet.

    async def mls_announce_commit_transition(self, transition_id: int, data: bytes) -> None:
        _log.debug("Handling MLS commit transition for ID %d.", transition_id)

        commit_result = self._session.process_commit(data)

        if commit_result is dave.RejectType.ignored:
            _log.debug("Ignoring MLS commit transition")
            return
        if commit_result is dave.RejectType.failed:
            _log.error("MLS commit transition failed and was rejected.")
            # If the group received in an Opcode 30 DAVE MLS Welcome or Opcode 29 DAVE MLS Announce Commit Transition is unprocessable,
            # the member receiving the unprocessable message sends Opcode 31 DAVE MLS Invalid Commit Welcome
            # to the voice gateway. Additionally, the local group state is reset and a new key package is
            # generated and sent to the voice gateway via Opcode 26 DAVE MLS Key Package.

            await self.voice_client.ws.send_dave_mls_invalid_commit_welcome(transition_id)
            await self.initialise(self._session.get_protocol_version())
        else:
            _log.debug("Successful commit with keys %s", commit_result.keys())
            await self.prepare_transition(transition_id, self._session.get_protocol_version())

    async def mls_welcome(self, transition_id: int, data: bytes) -> None:
        _log.debug("Handling MLS welcome for ID %d.", transition_id)

        welcome_result = self._session.process_welcome(
            data,
            recognized_user_ids={str(user_id) for user_id in self._recognised_users},
        )

        if welcome_result is None:
            _log.error("Failed to process MLS welcome.")

            await self.voice_client.ws.send_dave_mls_invalid_commit_welcome(transition_id)
            await self.initialise(self._session.get_protocol_version())
        else:
            _log.debug("MLS welcome processed successfully with keys %s.", welcome_result.keys())
            await self.prepare_transition(transition_id, self._session.get_protocol_version())

    async def mls_proposals(self, data: bytes) -> None:
        # All members of the established or pending MLS group must append or revoke the proposals they receive,
        # and then produce an MLS commit message and optionally an MLS welcome message
        # which they send to the voice gateway via Opcode 28 DAVE MLS Commit Welcome.
        commit_welcome = self._session.process_proposals(
            data, recognized_user_ids={str(user_id) for user_id in self._recognised_users}
        )

        if commit_welcome is not None:
            _log.debug("Sending MLS Commit Welcome")
            await self.voice_client.ws.send_dave_mls_commit_welcome(commit_welcome)

    def mls_external_sender(self, data: bytes) -> None:
        _log.debug("Handling MLS external sender message.")
        self._session.set_external_sender(data)
