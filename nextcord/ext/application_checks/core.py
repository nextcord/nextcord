"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz
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

from __future__ import annotations

import asyncio
import functools
from typing import Callable, Union, TypeVar, TYPE_CHECKING

import nextcord
from nextcord.application_command import ApplicationSubcommand, Interaction
from .errors import (
    ApplicationCheckAnyFailure,
    ApplicationCheckFailure,
    ApplicationNoPrivateMessage,
    ApplicationMissingRole,
    ApplicationMissingAnyRole,
    ApplicationBotMissingRole,
    ApplicationBotMissingAnyRole,
    ApplicationMissingPermissions,
    ApplicationBotMissingPermissions,
    ApplicationPrivateMessageOnly,
    ApplicationNotOwner,
    ApplicationNSFWChannelRequired,
    ApplicationCheckForBotOnly,
)

if TYPE_CHECKING:
    from nextcord.types.checks import ApplicationCheck, CoroFunc


__all__ = (
    "check",
    "check_any",
    "has_role",
    "has_any_role",
    "bot_has_role",
    "bot_has_any_role",
    "has_permissions",
    "bot_has_permissions",
    "has_guild_permissions",
    "bot_has_guild_permissions",
    "dm_only",
    "guild_only",
    "is_owner",
    "is_nsfw",
    "application_command_before_invoke",
    "application_command_after_invoke",
)

T = TypeVar("T")


def check(predicate: "ApplicationCheck") -> Callable[[T], T]:
    r"""A decorator that adds a check to the :class:`.ApplicationCommand` or its
    subclasses. These checks are accessible via :attr:`.ApplicationCommand.checks`.

    These checks should be predicates that take in a single parameter taking
    a :class:`.Interaction`. If the check returns a ``False``\-like value, 
    an ApplicationCheckFailure is raised during invocation and sent to the 
    :func:`.on_application_command_error` event.

    If an exception should be thrown in the predicate then it should be a
    subclass of :exc:`.ApplicationError`. Any exception not subclassed from it
    will be propagated while those subclassed will be sent to
    :func:`on_application_command_error`.

    A special attribute named ``predicate`` is bound to the value
    returned by this decorator to retrieve the predicate passed to the
    decorator. This allows the following introspection and chaining to be done:

    .. code-block:: python3

        def owner_or_permissions(**perms):
            original = application_checks.has_permissions(**perms).predicate
            async def extended_check(interaction: Interaction):
                if interaction.guild is None:
                    return False

                return (
                    interaction.guild.owner_id == interaction.user.id
                    or await original(interaction)
                )
            return application_checks.check(extended_check)

    .. note::

        The function returned by ``predicate`` is **always** a coroutine,
        even if the original function was not a coroutine.

    Examples
    ---------

    Creating a basic check to see if the command invoker is you.

    .. code-block:: python3

        def check_if_it_is_me(interaction: Interaction):
            return interaction.message.author.id == 85309593344815104

        @bot.slash_command()
        @application_checks.check(check_if_it_is_me)
        async def only_for_me(interaction: Interaction):
            await interaction.response.send_message('I know you!')

    Transforming common checks into its own decorator:

    .. code-block:: python3

        def is_me():
            def predicate(interaction: Interaction):
                return interaction.user.id == 85309593344815104
            return application_checks.check(predicate)

        @bot.slash_command()
        @is_me()
        async def only_me(interaction: Interaction):
            await interaction.response.send_message('Only you!')

    Parameters
    -----------
    predicate: Callable[[:class:`~.Interaction`], :class:`bool`]
        The predicate to check if the command should be invoked.
    """

    def decorator(
        func: Union[ApplicationSubcommand, "CoroFunc"]
    ) -> Union[ApplicationSubcommand, "CoroFunc"]:
        if isinstance(func, ApplicationSubcommand):
            func.checks.insert(0, predicate)
        else:
            if not hasattr(func, "__slash_command_checks__"):
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


def check_any(*checks: "ApplicationCheck") -> Callable[[T], T]:
    r"""A :func:`check` that will pass if any of the given checks pass, 
    i.e. using logical OR.

    If all checks fail then :exc:`.ApplicationCheckAnyFailure` is raised to signal 
    the failure. It inherits from :exc:`.ApplicationCheckFailure`.

    .. note::

        The ``predicate`` attribute for this function **is** a coroutine.

    Parameters
    ------------
    \*checks: Callable[[:class:`~.Interaction`], :class:`bool`]
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
                return (
                    interaction.guild is not None
                    and interaction.guild.owner_id == interaction.user.id
                )
            return application_checks.check(predicate)

        @bot.slash_command()
        @application_checks.check_any(applications_checks.is_owner(), is_guild_owner())
        async def only_for_owners(interaction: Interaction):
            await interaction.response.send_message('Hello mister owner!')
    """

    unwrapped = []
    for wrapped in checks:
        try:
            pred = wrapped.predicate
        except AttributeError:
            raise TypeError(
                f"{wrapped!r} must be wrapped by application_checks.check decorator"
            ) from None
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

    Example
    --------

    .. code-block:: python3

        @bot.slash_command()
        @application_checks.has_role('Cool Role')
        async def cool(interaction: Interaction):
            await interaction.response.send_message('You are cool indeed')
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
        @application_checks.has_any_role('Moderators', 492212595072434186)
        async def cool(interaction: Interaction):
            await interaction.response.send_message('You are cool indeed')
    """

    def predicate(interaction: Interaction) -> bool:
        if interaction.guild is None:
            raise ApplicationNoPrivateMessage()

        # interaction.guild is None doesn't narrow interaction.user to Member
        getter = functools.partial(nextcord.utils.get, interaction.user.roles)  # type: ignore
        if any(
            getter(id=item) is not None
            if isinstance(item, int)
            else getter(name=item) is not None
            for item in items
        ):
            return True
        raise ApplicationMissingAnyRole(list(items))

    return check(predicate)


def bot_has_role(item: int) -> Callable[[T], T]:
    """Similar to :func:`.has_role` except checks if the bot itself has the
    role.

    This check raises one of two special exceptions, 
    :exc:`.ApplicationBotMissingRole` if the bot is missing the role, 
    or :exc:`.ApplicationNoPrivateMessage` if it is used in a private message.
    Both inherit from :exc:`.ApplicationCheckFailure`.
    
    Parameters
    -----------
    item: Union[:class:`int`, :class:`str`]
        The name or ID of the role to check.

    Example
    --------

    .. code-block:: python3

        @bot.slash_command()
        @application_checks.bot_has_role(492212595072434186)
        async def hasrole(interaction: Interaction):
            await interaction.response.send_message('I have the required role!')
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

    This check raises one of two special exceptions, 
    :exc:`.ApplicationBotMissingAnyRole` if the bot is missing all roles, 
    or :exc:`.ApplicationNoPrivateMessage` if it is used in a private message.
    Both inherit from :exc:`.ApplicationCheckFailure`.

    Parameters
    -----------
    items: List[Union[:class:`str`, :class:`int`]]
        An argument list of names or IDs to check that the bot has roles wise.

    Example
    --------

    .. code-block:: python3

        @bot.slash_command()
        @application_checks.bot_has_any_role('Moderators', 492212595072434186)
        async def cool(interaction: Interaction):
            await interaction.response.send_message('I have a required role!')
    """

    def predicate(interaction: Interaction) -> bool:
        if interaction.guild is None:
            raise ApplicationNoPrivateMessage()

        me = interaction.guild.me or interaction.client.user
        getter = functools.partial(nextcord.utils.get, me.roles)
        if any(
            getter(id=item) is not None
            if isinstance(item, int)
            else getter(name=item) is not None
            for item in items
        ):
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

    If this check is called in a DM context, it will raise an
    exception, :exc:`.ApplicationNoPrivateMessage`.

    Parameters
    ------------
    perms: :class:`bool`
        An argument list of permissions to check for.

    Example
    ---------

    .. code-block:: python3

        @bot.slash_command()
        @application_checks.has_permissions(manage_messages=True)
        async def testperms(interaction: Interaction):
            await interaction.response.send_message('You can manage messages.')

    """

    invalid = set(perms) - set(nextcord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: Interaction) -> bool:
        ch = interaction.channel
        try:
            permissions = ch.permissions_for(interaction.user)  # type: ignore
        except AttributeError:
            raise ApplicationNoPrivateMessage()

        missing = [
            perm for perm, value in perms.items() if getattr(permissions, perm) != value
        ]

        if not missing:
            return True

        raise ApplicationMissingPermissions(missing)

    return check(predicate)


def bot_has_permissions(**perms: bool) -> Callable[[T], T]:
    """Similar to :func:`.has_permissions` except checks if the bot itself has
    the permissions listed.

    This check raises a special exception, :exc:`.ApplicationBotMissingPermissions`
    that is inherited from :exc:`.ApplicationCheckFailure`.

    If this check is called in a DM context, it will raise an
    exception, :exc:`.ApplicationNoPrivateMessage`.
    """

    invalid = set(perms) - set(nextcord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: Interaction) -> bool:
        guild = interaction.guild
        me = guild.me if guild is not None else interaction.client.user
        ch = interaction.channel
        try:
            permissions = ch.permissions_for(me)  # type: ignore
        except AttributeError:
            raise ApplicationNoPrivateMessage()

        missing = [
            perm for perm, value in perms.items() if getattr(permissions, perm) != value
        ]

        if not missing:
            return True

        raise ApplicationBotMissingPermissions(missing)

    return check(predicate)


def has_guild_permissions(**perms: bool) -> Callable[[T], T]:
    """Similar to :func:`.has_permissions`, but operates on guild wide
    permissions instead of the current channel permissions.

    If this check is called in a DM context, it will raise an
    exception, :exc:`.ApplicationNoPrivateMessage`.

    Parameters
    -----------
    perms: :class:`bool`
        An argument list of guild permissions to check for.

    Example
    --------

    .. code-block:: python3

        @bot.slash_command()
        @application_checks.has_guild_permissions(manage_messages=True)
        async def permcmd(interaction: Interaction):
            await interaction.response.send_message('You can manage messages!')
    """

    invalid = set(perms) - set(nextcord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: Interaction) -> bool:
        if not interaction.guild:
            raise ApplicationNoPrivateMessage

        permissions = interaction.user.guild_permissions  # type: ignore
        missing = [
            perm for perm, value in perms.items() if getattr(permissions, perm) != value
        ]

        if not missing:
            return True

        raise ApplicationMissingPermissions(missing)

    return check(predicate)


def bot_has_guild_permissions(**perms: bool) -> Callable[[T], T]:
    """Similar to :func:`.has_guild_permissions`, but checks the bot
    members guild permissions.
    """

    invalid = set(perms) - set(nextcord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(interaction: Interaction) -> bool:
        if not interaction.guild:
            raise ApplicationNoPrivateMessage

        permissions = interaction.guild.me.guild_permissions  # type: ignore
        missing = [
            perm for perm, value in perms.items() if getattr(permissions, perm) != value
        ]

        if not missing:
            return True

        raise ApplicationBotMissingPermissions(missing)

    return check(predicate)


def dm_only() -> Callable[[T], T]:
    """A :func:`.check` that indicates this command must only be used in a
    DM context. Only private messages are allowed when
    using the command.

    This check raises a special exception, :exc:`.ApplicationPrivateMessageOnly`
    that is inherited from :exc:`.ApplicationCheckFailure`.

    Example
    --------

    .. code-block:: python3

        @bot.slash_command()
        @application_checks.dm_only()
        async def dmcmd(interaction: Interaction):
            await interaction.response.send_message('This is in DMS!')
    """

    def predicate(interaction: Interaction) -> bool:
        if interaction.guild is not None:
            raise ApplicationPrivateMessageOnly()
        return True

    return check(predicate)


def guild_only() -> Callable[[T], T]:
    """A :func:`.check` that indicates this command must only be used in a
    guild context only. Basically, no private messages are allowed when
    using the command.

    This check raises a special exception, :exc:`.ApplicationNoPrivateMessage`
    that is inherited from :exc:`.ApplicationCheckFailure`.

    Example
    --------

    .. code-block:: python3

        @bot.slash_command()
        @application_checks.guild_only()
        async def dmcmd(interaction: Interaction):
            await interaction.response.send_message('This is in a GUILD!')
    """

    def predicate(interaction: Interaction) -> bool:
        if interaction.guild is None:
            raise ApplicationNoPrivateMessage()
        return True

    return check(predicate)


def is_owner() -> Callable[[T], T]:
    """A :func:`.check` that checks if the person invoking this command is the
    owner of the bot.

    This is powered by :meth:`.ext.commands.Bot.is_owner`.

    This check raises a special exception, :exc:`.ApplicationNotOwner` that is derived
    from :exc:`.ApplicationCheckFailure`.

    This check may only be used with :class:`~ext.commands.Bot`. Otherwise, it will
    raise :exc:`.ApplicationCheckForBotOnly`.

    Example
    --------

    .. code-block:: python3

        bot = commands.Bot(owner_id=297045071457681409)
    
        @bot.slash_command()
        @application_checks.is_owner()
        async def ownercmd(interaction: Interaction):
            await interaction.response.send_message('Only you!')
    """

    async def predicate(interaction: Interaction) -> bool:
        if not hasattr(interaction.client, "is_owner"):
            raise ApplicationCheckForBotOnly()

        if not await interaction.client.is_owner(interaction.user):
            raise ApplicationNotOwner("You do not own this bot.")
        return True

    return check(predicate)


def is_nsfw() -> Callable[[T], T]:
    """A :func:`.check` that checks if the channel is a NSFW channel.

    This check raises a special exception, :exc:`.ApplicationNSFWChannelRequired`
    that is derived from :exc:`.ApplicationCheckFailure`.

    Example
    --------

    .. code-block:: python3
    
        @bot.slash_command()
        @application_checks.is_nsfw()
        async def ownercmd(interaction: Interaction):
            await interaction.response.send_message('Only NSFW channels!')
    """

    def pred(interaction: Interaction) -> bool:
        ch = interaction.channel
        if interaction.guild is None or (
            isinstance(ch, (nextcord.TextChannel, nextcord.Thread)) and ch.is_nsfw()
        ):
            return True
        raise ApplicationNSFWChannelRequired(ch)  # type: ignore

    return check(pred)


def application_command_before_invoke(coro) -> Callable[[T], T]:
    """A decorator that registers a coroutine as a pre-invoke hook.

    This allows you to refer to one before invoke hook for several commands that
    do not have to be within the same cog.

    Example
    ---------

    .. code-block:: python3

        async def record_usage(interaction: Interaction):
            print(
                interaction.user,
                "used",
                interaction.application_command,
                "at",
                interaction.message.created_at
            )

        @bot.slash_command()
        @application_checks.application_command_before_invoke(record_usage)
        async def who(interaction: Interaction): # Output: <User> used who at <Time>
            await interaction.response.send_message("I am a bot")

        class What(commands.Cog):
            @application_checks.application_command_before_invoke(record_usage)
            @nextcord.slash_command()
            async def when(self, interaction: Interaction):
                # Output: <User> used when at <Time>
                await interaction.response.send_message(
                    f"and i have existed since {interaction.client.user.created_at}"
                )

            @nextcord.slash_command()
            async def where(self, interaction: Interaction): # Output: <Nothing>
                await interaction.response.send_message("on Discord")

            @nextcord.slash_command()
            async def why(self, interaction: Interaction): # Output: <Nothing>
                await interaction.response.send_message("because someone made me")

        bot.add_cog(What())
    """

    def decorator(
        func: Union[ApplicationSubcommand, "CoroFunc"]
    ) -> Union[ApplicationSubcommand, "CoroFunc"]:
        if isinstance(func, ApplicationSubcommand):
            func.application_command_before_invoke(coro)
        else:
            func.__application_command_before_invoke__ = coro
        return func

    return decorator  # type: ignore


def application_command_after_invoke(coro) -> Callable[[T], T]:
    """A decorator that registers a coroutine as a post-invoke hook.

    This allows you to refer to one after invoke hook for several commands that
    do not have to be within the same cog.
    """

    def decorator(
        func: Union[ApplicationSubcommand, "CoroFunc"]
    ) -> Union[ApplicationSubcommand, "CoroFunc"]:
        if isinstance(func, ApplicationSubcommand):
            func.application_command_after_invoke(coro)
        else:
            func.__application_command_after_invoke__ = coro
        return func

    return decorator  # type: ignore
