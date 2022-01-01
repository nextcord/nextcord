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
import asyncio
import functools
import nextcord
from typing import Callable, Union, TypeVar, TYPE_CHECKING

from .application_command import ApplicationSubcommand, Interaction
from .errors import (
    ApplicationCheckAnyFailure,
    ApplicationCheckFailure,
    ApplicationNoPrivateMessage,
    ApplicationMissingRole,
    ApplicationMissingAnyRole,
    ApplicationBotMissingRole,
    ApplicationBotMissingAnyRole,
    ApplicationMissingPermissions
)

if TYPE_CHECKING:
    from .application_command import ClientCog
    from .types.checks import ApplicationCheck, CoroFunc


__all__ = (
    "check",
    "check_any"
)

T = TypeVar('T')

def check(predicate: 'ApplicationCheck') -> Callable[[T], T]:
    r"""A decorator that adds a check to the :class:`ApplicationSubcommand` or its
    subclasses. These checks could be accessed via :attr:`ApplicationSubcommand.checks`.
    These checks should be predicates that take in a single parameter taking
    a :class:`.Interaction`. If the check returns a ``False``\-like value then
    during invocation a :exc:`ApplicationCheckFailure` exception is raised and sent to
    the :func:`.on_command_error` event.
    If an exception should be thrown in the predicate then it should be a
    subclass of :exc:`.ApplicationError`. Any exception not subclassed from it
    will be propagated while those subclassed will be sent to
    :func:`.on_application_command_error`.
    """

    def decorator(func: Union[ApplicationSubcommand, 'CoroFunc']) -> Union[ApplicationSubcommand, 'CoroFunc']:
        if isinstance(func, ApplicationSubcommand):
            func.checks.insert(0, predicate)
        else:
            if not hasattr(func, '__slash_command_checks__'):
                func.__slash_command_checks__ = []

            func.__slash_command_checks__.append(predicate)

        return func

    if asyncio.iscoroutinefunction(predicate):
        decorator.predicate = predicate
    else:
        @functools.wraps(predicate)
        async def wrapper(ctx):
            return predicate(ctx)
        decorator.predicate = wrapper

    return decorator

def check_any(*checks: 'ApplicationCheck') -> Callable[[T], T]:
    r"""A :func:`check` that is added that checks if any of the checks passed
    will pass, i.e. using logical OR.

    If all checks fail then :exc:`.ApplicationCheckAnyFailure` is raised to signal the failure.
    It inherits from :exc:`.ApplicationCheckFailure`.

    .. note::

        The ``predicate`` attribute for this function **is** a coroutine.

    Parameters
    ------------
    \*checks: Callable[[:class:`Interaction`], :class:`bool`]
        An argument list of checks that have been decorated with
        the :func:`check` decorator.

    Raises
    -------
    TypeError
        A check passed has not been decorated with the :func:`check`
        decorator.

    Examples
    ---------

    Creating a basic check to see if it's the bot owner or
    the server owner:

    .. code-block:: python3

        def is_guild_owner():
            def predicate(interaction: Interaction):
                return interaction.guild is not None and interaction.guild.owner_id == ctx.author.id
            return commands.check(predicate)

        @bot.command()
        @checks.check_any(checks.is_owner(), is_guild_owner())
        async def only_for_owners(interaction: Interaction):
            await interaction.response.send_message('Hello mister owner!')
    """

    unwrapped = []
    for wrapped in checks:
        try:
            pred = wrapped.predicate
        except AttributeError:
            raise TypeError(f'{wrapped!r} must be wrapped by checks.check decorator') from None
        else:
            unwrapped.append(pred)

    async def predicate(interaction: Interaction) -> bool:
        errors = []
        for func in unwrapped:
            try:
                value = await func(interaction)
            except ApplicationCheckFailure as e:
                errors.append(e)
            else:
                if value:
                    return True
        # if we're here, all checks failed
        raise ApplicationCheckAnyFailure(unwrapped, errors)

    return check(predicate)

def has_role(item: Union[int, str]) -> Callable[[T], T]:
    """A :func:`.check` that is added that checks if the member invoking the
    command has the role specified via the name or ID specified.

    If a string is specified, you must give the exact name of the role, including
    caps and spelling.

    If an integer is specified, you must give the exact snowflake ID of the role.

    If the message is invoked in a private message context then the check will
    return ``False``.

    This check raises one of two special exceptions, :exc:`.MissingRole` if the user
    is missing a role, or :exc:`.NoPrivateMessage` if it is used in a private message.
    Both inherit from :exc:`.ApplicationCheckFailure`.

    Parameters
    -----------
    item: Union[:class:`int`, :class:`str`]
        The name or ID of the role to check.
    """

    def predicate(interaction: Interaction) -> bool:
        if interaction.guild is None:
            raise ApplicationNoPrivateMessage()

        # interaction.guild is None doesn't narrow interaction.user to Member
        if isinstance(item, int):
            role = nextcord.utils.get(interaction.user.roles, id=item)  # type: ignore
        else:
            role = nextcord.utils.get(interaction.user.roles, name=item)  # type: ignore
        if role is None:
            raise ApplicationMissingRole(item)
        return True

    return check(predicate)

def has_any_role(*items: Union[int, str]) -> Callable[[T], T]:
    r"""A :func:`.check` that is added that checks if the member invoking the
    command has **any** of the roles specified. This means that if they have
    one out of the three roles specified, then this check will return `True`.

    Similar to :func:`.has_role`\, the names or IDs passed in must be exact.

    This check raises one of two special exceptions, :exc:`.MissingAnyRole` if the user
    is missing all roles, or :exc:`.NoPrivateMessage` if it is used in a private message.
    Both inherit from :exc:`.ApplicationCheckFailure`.

    Parameters
    -----------
    items: List[Union[:class:`str`, :class:`int`]]
        An argument list of names or IDs to check that the member has roles wise.

    Example
    --------

    .. code-block:: python3

        @bot.slash_command()
        @checks.has_any_role('Library Devs', 'Moderators', 492212595072434186)
        async def cool(interaction: Interaction):
            await interaction.response.send_message('You are cool indeed')
    """
    def predicate(interaction: Interaction) -> bool:
        if interaction.guild is None:
            raise ApplicationNoPrivateMessage()

        # interaction.guild is None doesn't narrow interaction.user to Member
        getter = functools.partial(nextcord.utils.get, interaction.user.roles)  # type: ignore
        if any(getter(id=item) is not None if isinstance(item, int) else getter(name=item) is not None for item in items):
            return True
        raise ApplicationMissingAnyRole(list(items))

    return check(predicate)

def bot_has_role(item: int) -> Callable[[T], T]:
    """Similar to :func:`.has_role` except checks if the bot itself has the
    role.

    This check raises one of two special exceptions, :exc:`.ApplicationBotMissingRole` if the bot
    is missing the role, or :exc:`.ApplicationNoPrivateMessage` if it is used in a private message.
    Both inherit from :exc:`.ApplicationCheckFailure`.
    """

    def predicate(interaction: Interaction) -> bool:
        if interaction.guild is None:
            raise ApplicationNoPrivateMessage()

        me = interaction.guild.me
        if isinstance(item, int):
            role = nextcord.utils.get(me.roles, id=item)
        else:
            role = nextcord.utils.get(me.roles, name=item)
        if role is None:
            raise ApplicationBotMissingRole(item)
        return True
    return check(predicate)

def bot_has_any_role(*items: int) -> Callable[[T], T]:
    """Similar to :func:`.has_any_role` except checks if the bot itself has
    any of the roles listed.

    This check raises one of two special exceptions, :exc:`.ApplicationBotMissingAnyRole` if the bot
    is missing all roles, or :exc:`.ApplicationNoPrivateMessage` if it is used in a private message.
    Both inherit from :exc:`.ApplicationCheckFailure`.
    """
    def predicate(interaction: Interaction) -> bool:
        if interaction.guild is None:
            raise ApplicationNoPrivateMessage()

        me = interaction.guild.me
        getter = functools.partial(nextcord.utils.get, me.roles)
        if any(getter(id=item) is not None if isinstance(item, int) else getter(name=item) is not None for item in items):
            return True
        raise ApplicationBotMissingAnyRole(list(items))
    return check(predicate)

def has_permissions(**perms: bool) -> Callable[[T], T]:
    """A :func:`.check` that is added that checks if the member has all of
    the permissions necessary.

    Note that this check operates on the current channel permissions, not the
    guild wide permissions.

    The permissions passed in must be exactly like the properties shown under
    :class:`.nextcord.Permissions`.

    This check raises a special exception, :exc:`.ApplicationMissingPermissions`
    that is inherited from :exc:`.ApplicationCheckFailure`.

    Parameters
    ------------
    perms
        An argument list of permissions to check for.

    Example
    ---------

    .. code-block:: python3

        @bot.slash_command()
        @checks.has_permissions(manage_messages=True)
        async def test(interaction: Interaction):
            await interaction.response.send_message('You can manage messages.')

    """

    invalid = set(perms) - set(nextcord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: Interaction) -> bool:
        ch = interaction.channel
        permissions = ch.permissions_for(interaction.user)  # type: ignore

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise ApplicationMissingPermissions(missing)

    return check(predicate)