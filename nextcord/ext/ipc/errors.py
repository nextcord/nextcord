from nextcord import nextcordException


class IPCError(nextcordException):
    """Base IPC exception class"""

    pass


class NoEndpointFoundError(IPCError):
    """Raised upon requesting an invalid endpoint"""

    pass


class ServerConnectionRefusedError(IPCError):
    """Raised upon a server refusing to connect / not being found"""

    pass


class JSONEncodeError(IPCError):
    """Raise upon un-serializable objects are given to the IPC"""

    pass


class NotConnected(IPCError):
    """Raised upon websocket not connected"""

    pass
