from .check_failure import CheckFailure
from nextcord.types.snowflake import Snowflake

class MissingRole(CheckFailure):
    """Exception raised when the command invoker lacks a role to run a command.

    This inherits from :exc:`CheckFailure`

    .. versionadded:: 1.1

    Attributes
    -----------
    missing_role: Union[:class:`str`, :class:`int`]
        The required role that is missing.
        This is the parameter passed to :func:`~.commands.has_role`.
    """

    def __init__(self, missing_role: Snowflake) -> None:
        self.missing_role: Snowflake = missing_role
        message = f'Role {missing_role!r} is required to run this command.'
        super().__init__(message)