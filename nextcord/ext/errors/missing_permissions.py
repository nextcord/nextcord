from typing import Any, List
from .check_failure import CheckFailure


class MissingPermissions(CheckFailure):
    """Exception raised when the command invoker lacks permissions to run a
    command.

    This inherits from :exc:`CheckFailure`

    Attributes
    -----------
    missing_permissions: List[:class:`str`]
        The required permissions that are missing.
    """

    def __init__(self, missing_permissions: List[str], *args: Any) -> None:
        self.missing_permissions: List[str] = missing_permissions

        missing = [perm.replace('_', ' ').replace(
            'guild', 'server').title() for perm in missing_permissions]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = f'You are missing {fmt} permission(s) to run this command.'
        super().__init__(message, *args)