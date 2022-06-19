"""
The MIT License (MIT)
Copyright (c) 2021-present tag-epic

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

from nextcord.abc import GuildChannel
from nextcord.channel import PartialMessageable
from nextcord.errors import ApplicationCheckFailure
from nextcord.interactions import Interaction
from nextcord.threads import Thread
from nextcord.types.snowflake import Snowflake, SnowflakeList

__all__ = (
    "ApplicationCheckAnyFailure",
    "ApplicationNoPrivateMessage",
    "ApplicationMissingRole",
    "ApplicationMissingAnyRole",
    "ApplicationBotMissingRole",
    "ApplicationBotMissingAnyRole",
    "ApplicationMissingPermissions",
    "ApplicationBotMissingPermissions",
    "ApplicationPrivateMessageOnly",
    "ApplicationNotOwner",
    "ApplicationNSFWChannelRequired",
    "ApplicationCheckForBotOnly",
)


class ApplicationCheckAnyFailure(ApplicationCheckFailure):
    """Exception raised when all predicates in :func:`check_any` fail.

    This inherits from :exc:`~.ApplicationCheckFailure`.

    Attributes
    ------------
    errors: List[:class:`~.ApplicationCheckFailure`]
        A list of errors that were caught during execution.
    checks: List[Callable[[:class:`~.Interaction`], :class:`bool`]]
        A list of check predicates that failed.
    """

    def __init__(
        self,
        checks: List[ApplicationCheckFailure],
        errors: List[Callable[[Interaction], bool]],
    ) -> None:
        self.checks: List[ApplicationCheckFailure] = checks
        self.errors: List[Callable[[Interaction], bool]] = errors
        super().__init__("You do not have permission to run this command.")


class ApplicationNoPrivateMessage(ApplicationCheckFailure):
    """Exception raised when an operation does not work in private message
    contexts.

    This inherits from :exc:`~.ApplicationCheckFailure`
    """

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "This command cannot be used in private messages.")


class ApplicationMissingRole(ApplicationCheckFailure):
    """Exception raised when the command invoker lacks a role to run a command.

    This inherits from :exc:`~.ApplicationCheckFailure`

    .. versionadded:: 1.1

    Attributes
    -----------
    missing_role: Union[:class:`str`, :class:`int`]
        The required role that is missing.
        This is the parameter passed to :func:`~.application_checks.has_role`.
    """

    def __init__(self, missing_role: Snowflake) -> None:
        self.missing_role: Snowflake = missing_role
        message = f"Role {missing_role!r} is required to run this command."
        super().__init__(message)


class ApplicationMissingAnyRole(ApplicationCheckFailure):
    """Exception raised when the command invoker lacks any of
    the roles specified to run a command.

    This inherits from :exc:`~.ApplicationCheckFailure`

    Attributes
    -----------
    missing_roles: List[Union[:class:`str`, :class:`int`]]
        The roles that the invoker is missing.
        These are the parameters passed to :func:`has_any_role`.
    """

    def __init__(self, missing_roles: SnowflakeList) -> None:
        self.missing_roles: SnowflakeList = missing_roles

        missing = [f"'{role}'" for role in missing_roles]

        if len(missing) > 2:
            fmt = "{}, or {}".format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = " or ".join(missing)

        message = f"You are missing at least one of the required roles: {fmt}"
        super().__init__(message)


class ApplicationBotMissingRole(ApplicationCheckFailure):
    """Exception raised when the bot's member lacks a role to run a command.

    This inherits from :exc:`~.ApplicationCheckFailure`

    .. versionadded:: 1.1

    Attributes
    -----------
    missing_role: Union[:class:`str`, :class:`int`]
        The required role that is missing.
        This is the parameter passed to :func:`has_role`.
    """

    def __init__(self, missing_role: Snowflake) -> None:
        self.missing_role: Snowflake = missing_role
        message = f"Bot requires the role {missing_role!r} to run this command"
        super().__init__(message)


class ApplicationBotMissingAnyRole(ApplicationCheckFailure):
    """Exception raised when the bot's member lacks any of
    the roles specified to run a command.

    This inherits from :exc:`~.ApplicationCheckFailure`

    .. versionadded:: 1.1

    Attributes
    -----------
    missing_roles: List[Union[:class:`str`, :class:`int`]]
        The roles that the bot's member is missing.
        These are the parameters passed to :func:`has_any_role`.

    """

    def __init__(self, missing_roles: SnowflakeList) -> None:
        self.missing_roles: SnowflakeList = missing_roles

        missing = [f"'{role}'" for role in missing_roles]

        if len(missing) > 2:
            fmt = "{}, or {}".format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = " or ".join(missing)

        message = f"Bot is missing at least one of the required roles: {fmt}"
        super().__init__(message)


class ApplicationMissingPermissions(ApplicationCheckFailure):
    """Exception raised when the command invoker lacks permissions to run a
    command.

    This inherits from :exc:`~.ApplicationCheckFailure`

    Attributes
    -----------
    missing_permissions: List[:class:`str`]
        The required permissions that are missing.
    """

    def __init__(self, missing_permissions: List[str], *args: Any) -> None:
        self.missing_permissions: List[str] = missing_permissions

        missing = [
            perm.replace("_", " ").replace("guild", "server").title()
            for perm in missing_permissions
        ]

        if len(missing) > 2:
            fmt = "{}, and {}".format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = " and ".join(missing)
        message = f"You are missing {fmt} permission(s) to run this command."
        super().__init__(message, *args)


class ApplicationBotMissingPermissions(ApplicationCheckFailure):
    """Exception raised when the bot's member lacks permissions to run a
    command.

    This inherits from :exc:`~.ApplicationCheckFailure`

    Attributes
    -----------
    missing_permissions: List[:class:`str`]
        The required permissions that are missing.
    """

    def __init__(self, missing_permissions: List[str], *args: Any) -> None:
        self.missing_permissions: List[str] = missing_permissions

        missing = [
            perm.replace("_", " ").replace("guild", "server").title()
            for perm in missing_permissions
        ]

        if len(missing) > 2:
            fmt = "{}, and {}".format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = " and ".join(missing)
        message = f"Bot requires {fmt} permission(s) to run this command."
        super().__init__(message, *args)


class ApplicationPrivateMessageOnly(ApplicationCheckFailure):
    """Exception raised when an operation does not work outside of private
    message contexts.

    This inherits from :exc:`~.ApplicationCheckFailure`
    """

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "This command can only be used in private messages.")


class ApplicationNotOwner(ApplicationCheckFailure):
    """Exception raised when the message author is not the owner of the bot.

    This inherits from :exc:`~.ApplicationCheckFailure`
    """

    pass


class ApplicationNSFWChannelRequired(ApplicationCheckFailure):
    """Exception raised when a channel does not have the required NSFW setting.

    This inherits from :exc:`~.ApplicationCheckFailure`.

    Parameters
    -----------
    channel: Optional[Union[:class:`.abc.GuildChannel`, :class:`.Thread`, :class:`PartialMessageable`]]
        The channel that does not have NSFW enabled.
    """

    def __init__(self, channel: Optional[Union[GuildChannel, Thread, PartialMessageable]]) -> None:
        self.channel = channel
        super().__init__(f"Channel '{channel}' needs to be NSFW for this command to work.")


class ApplicationCheckForBotOnly(ApplicationCheckFailure):
    """Exception raised when the application check may only be used for :class:`~ext.commands.Bot`.

    This inherits from :exc:`~.ApplicationCheckFailure`
    """

    def __init__(self) -> None:
        super().__init__("This application check can only be used for ext.commands.Bot.")
