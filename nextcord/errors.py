# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from aiohttp import ClientResponse, ClientWebSocketResponse
    from requests import Response

    _ResponseType = Union[ClientResponse, Response]

    from .interactions import Interaction

__all__ = (
    "DiscordException",
    "ClientException",
    "NoMoreItems",
    "GatewayNotFound",
    "HTTPException",
    "Forbidden",
    "NotFound",
    "DiscordServerError",
    "InvalidData",
    "InvalidArgument",
    "LoginFailure",
    "ConnectionClosed",
    "PrivilegedIntentsRequired",
    "InteractionResponded",
    "ApplicationError",
    "ApplicationInvokeError",
    "ApplicationCheckFailure",
    "ApplicationCommandOptionMissing",
)


class DiscordException(Exception):
    """Base exception class for nextcord

    Ideally speaking, this could be caught to handle any exceptions raised from this library.
    """


class ClientException(DiscordException):
    """Exception that's raised when an operation in the :class:`Client` fails.

    These are usually for exceptions that happened due to user input.
    """


class NoMoreItems(DiscordException):
    """Exception that is raised when an async iteration operation has no more items."""


class GatewayNotFound(DiscordException):
    """An exception that is raised when the gateway for Discord could not be found"""

    def __init__(self) -> None:
        message = "The gateway to connect to discord was not found."
        super().__init__(message)


def _flatten_error_dict(d: Dict[str, Any], key: str = "") -> Dict[str, str]:
    items: List[Tuple[str, str]] = []
    for k, v in d.items():
        new_key = key + "." + k if key else k

        if isinstance(v, dict):
            try:
                _errors: List[Dict[str, Any]] = v["_errors"]
            except KeyError:
                items.extend(_flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, " ".join(x.get("message", "") for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)


class HTTPException(DiscordException):
    """Exception that's raised when an HTTP request operation fails.

    Attributes
    ----------
    response: :class:`aiohttp.ClientResponse`
        The response of the failed HTTP request. This is an
        instance of :class:`aiohttp.ClientResponse`. In some cases
        this could also be a :class:`requests.Response`.

    text: :class:`str`
        The text of the error. Could be an empty string.
    status: :class:`int`
        The status code of the HTTP request.
    code: :class:`int`
        The Discord specific error code for the failure.
    """

    def __init__(
        self, response: _ResponseType, message: Optional[Union[str, Dict[str, Any]]]
    ) -> None:
        self.response: _ResponseType = response
        self.status: int = response.status  # type: ignore
        self.code: int
        self.text: str
        if isinstance(message, dict):
            self.code = message.get("code", 0)
            base = message.get("message", "")
            errors = message.get("errors")
            if errors:
                errors = _flatten_error_dict(errors)
                helpful = "\n".join("In %s: %s" % t for t in errors.items())
                self.text = base + "\n" + helpful
            else:
                self.text = base
        else:
            self.text = message or ""
            self.code = 0

        fmt = "{0.status} {0.reason} (error code: {1})"
        if len(self.text):
            fmt += ": {2}"

        super().__init__(fmt.format(self.response, self.code, self.text))


class Forbidden(HTTPException):
    """Exception that's raised for when status code 403 occurs.

    Subclass of :exc:`HTTPException`
    """


class NotFound(HTTPException):
    """Exception that's raised for when status code 404 occurs.

    Subclass of :exc:`HTTPException`
    """


class DiscordServerError(HTTPException):
    """Exception that's raised for when a 500 range status code occurs.

    Subclass of :exc:`HTTPException`.

    .. versionadded:: 1.5
    """


class InvalidData(ClientException):
    """Exception that's raised when the library encounters unknown
    or invalid data from Discord.
    """


class InvalidArgument(ClientException):
    """Exception that's raised when an argument to a function
    is invalid some way (e.g. wrong value or wrong type).

    This could be considered the analogous of ``ValueError`` and
    ``TypeError`` except inherited from :exc:`ClientException` and thus
    :exc:`DiscordException`.
    """


class LoginFailure(ClientException):
    """Exception that's raised when the :meth:`Client.login` function
    fails to log you in from improper credentials or some other misc.
    failure.
    """


class ConnectionClosed(ClientException):
    """Exception that's raised when the gateway connection is
    closed for reasons that could not be handled internally.

    Attributes
    ----------
    code: :class:`int`
        The close code of the websocket.
    reason: :class:`str`
        The reason provided for the closure.
    shard_id: Optional[:class:`int`]
        The shard ID that got closed if applicable.
    """

    def __init__(
        self,
        socket: ClientWebSocketResponse,
        *,
        shard_id: Optional[int],
        code: Optional[int] = None,
    ) -> None:
        # This exception is just the same exception except
        # reconfigured to subclass ClientException for users
        self.code: int = code or socket.close_code or -1
        # aiohttp doesn't seem to consistently provide close reason
        self.reason: str = ""
        self.shard_id: Optional[int] = shard_id
        super().__init__(f"Shard ID {self.shard_id} WebSocket closed with {self.code}")


class PrivilegedIntentsRequired(ClientException):
    """Exception that's raised when the gateway is requesting privileged intents
    but they're not ticked in the developer page yet.

    Go to https://discord.com/developers/applications/ and enable the intents
    that are required. Currently these are as follows:

    - :attr:`Intents.members`
    - :attr:`Intents.presences`

    Attributes
    ----------
    shard_id: Optional[:class:`int`]
        The shard ID that got closed if applicable.
    """

    def __init__(self, shard_id: Optional[int]) -> None:
        self.shard_id: Optional[int] = shard_id
        msg = (
            "Shard ID %s is requesting privileged intents that have not been explicitly enabled in the "
            "developer portal. It is recommended to go to https://discord.com/developers/applications/ "
            "and explicitly enable the privileged intents within your application's page. If this is not "
            "possible, then consider disabling the privileged intents instead."
        )
        super().__init__(msg % shard_id)


class InteractionResponded(ClientException):
    """Exception that's raised when sending another interaction response using
    :class:`InteractionResponse` when one has already been done before.

    An interaction can only respond once.

    .. versionadded:: 2.0

    Attributes
    ----------
    interaction: :class:`Interaction`
        The interaction that's already been responded to.
    """

    def __init__(self, interaction: Interaction) -> None:
        self.interaction: Interaction = interaction
        super().__init__("This interaction has already been responded to before")


class ApplicationError(DiscordException):
    r"""The base exception type for all command related errors.

    This inherits from :exc:`nextcord.DiscordException`.

    This exception and exceptions inherited from it are handled
    in a special way as they are caught and passed into a special event
    from :class:`.Bot`\, :func:`.on_command_error`.
    """

    def __init__(self, message: Optional[str] = None, *args: Any) -> None:
        if message is not None:
            # clean-up @everyone and @here mentions
            m = message.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
            super().__init__(m, *args)
        else:
            super().__init__(*args)


class ApplicationInvokeError(ApplicationError):
    """Exception raised when the command being invoked raised an exception.

    This inherits from :exc:`ApplicationError`

    Attributes
    ----------
    original: :exc:`Exception`
        The original exception that was raised. You can also get this via
        the ``__cause__`` attribute.
    """

    def __init__(self, e: Exception) -> None:
        self.original: Exception = e
        self.__cause__ = e
        super().__init__(f"Command raised an exception: {e.__class__.__name__}: {e}")


class ApplicationCheckFailure(ApplicationError):
    """Exception raised when the predicates in :attr:`.BaseApplicationCommand.checks` have failed.

    This inherits from :exc:`ApplicationError`
    """


class ApplicationCommandOptionMissing(ApplicationError):
    """Raised when an option that's supposed to be part of an application command is missing on our end."""
