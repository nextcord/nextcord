from .command_error import CommandError


class CommandInvokeError(CommandError):
    """Exception raised when the command being invoked raised an exception.

    This inherits from :exc:`CommandError`

    Attributes
    -----------
    original: :exc:`Exception`
        The original exception that was raised. You can also get this via
        the ``__cause__`` attribute.
    """

    def __init__(self, e: Exception) -> None:
        self.original: Exception = e
        super().__init__(
            f'Command raised an exception: {e.__class__.__name__}: {e}')