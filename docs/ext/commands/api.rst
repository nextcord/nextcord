.. currentmodule:: nextcord

API Reference
=============

The following section outlines the API of nextcord's command extension module.

.. _ext_commands_api_bot:

Bots
----

Bot
~~~

.. attributetable:: nextcord.ext.commands.Bot

.. autoclass:: nextcord.ext.commands.Bot
    :members:
    :inherited-members:
    :exclude-members: after_invoke, before_invoke, check, check_once, command, event, group, listen

    .. automethod:: Bot.after_invoke()
        :decorator:

    .. automethod:: Bot.before_invoke()
        :decorator:

    .. automethod:: Bot.check()
        :decorator:

    .. automethod:: Bot.check_once()
        :decorator:

    .. automethod:: Bot.command(*args, **kwargs)
        :decorator:

    .. automethod:: Bot.event()
        :decorator:

    .. automethod:: Bot.group(*args, **kwargs)
        :decorator:

    .. automethod:: Bot.listen(name=None)
        :decorator:

AutoShardedBot
~~~~~~~~~~~~~~

.. attributetable:: nextcord.ext.commands.AutoShardedBot

.. autoclass:: nextcord.ext.commands.AutoShardedBot
    :members:

Prefix Helpers
--------------

.. autofunction:: nextcord.ext.commands.when_mentioned

.. autofunction:: nextcord.ext.commands.when_mentioned_or

.. _ext_commands_api_events:

Event Reference
---------------

These events function similar to :ref:`the regular events <discord-api-events>`, except they
are custom to the command extension module.

.. function:: nextcord.ext.commands.on_command_error(ctx, error)

    An error handler that is called when an error is raised
    inside a command either through user input error, check
    failure, or an error in your own code.

    A default one is provided (:meth:`.Bot.on_command_error`).

    :param ctx: The invocation context.
    :type ctx: :class:`.Context`
    :param error: The error that was raised.
    :type error: :class:`.CommandError` derived

.. function:: nextcord.ext.commands.on_command(ctx)

    An event that is called when a command is found and is about to be invoked.

    This event is called regardless of whether the command itself succeeds via
    error or completes.

    :param ctx: The invocation context.
    :type ctx: :class:`.Context`

.. function:: nextcord.ext.commands.on_command_completion(ctx)

    An event that is called when a command has completed its invocation.

    This event is called only if the command succeeded, i.e. all checks have
    passed and the user input it correctly.

    :param ctx: The invocation context.
    :type ctx: :class:`.Context`

.. _ext_commands_api_command:

Commands
--------

Decorators
~~~~~~~~~~

.. autofunction:: nextcord.ext.commands.command
    :decorator:

.. autofunction:: nextcord.ext.commands.group
    :decorator:

Command
~~~~~~~

.. attributetable:: nextcord.ext.commands.Command

.. autoclass:: nextcord.ext.commands.Command
    :members:
    :special-members: __call__
    :exclude-members: after_invoke, before_invoke, error

    .. automethod:: Command.after_invoke()
        :decorator:

    .. automethod:: Command.before_invoke()
        :decorator:

    .. automethod:: Command.error()
        :decorator:

Group
~~~~~

.. attributetable:: nextcord.ext.commands.Group

.. autoclass:: nextcord.ext.commands.Group
    :members:
    :inherited-members:
    :exclude-members: after_invoke, before_invoke, command, error, group

    .. automethod:: Group.after_invoke()
        :decorator:

    .. automethod:: Group.before_invoke()
        :decorator:

    .. automethod:: Group.command(*args, **kwargs)
        :decorator:

    .. automethod:: Group.error()
        :decorator:

    .. automethod:: Group.group(*args, **kwargs)
        :decorator:

GroupMixin
~~~~~~~~~~

.. attributetable:: nextcord.ext.commands.GroupMixin

.. autoclass:: nextcord.ext.commands.GroupMixin
    :members:
    :exclude-members: command, group

    .. automethod:: GroupMixin.command(*args, **kwargs)
        :decorator:

    .. automethod:: GroupMixin.group(*args, **kwargs)
        :decorator:

.. _ext_commands_api_cogs:

Cogs
----

Cog
~~~

.. attributetable:: nextcord.ext.commands.Cog

.. autoclass:: nextcord.ext.commands.Cog
    :members:

CogMeta
~~~~~~~

.. attributetable:: nextcord.ext.commands.CogMeta

.. autoclass:: nextcord.ext.commands.CogMeta
    :members:

.. _ext_commands_help_command:

Help Commands
-------------

HelpCommand
~~~~~~~~~~~

.. attributetable:: nextcord.ext.commands.HelpCommand

.. autoclass:: nextcord.ext.commands.HelpCommand
    :members:

DefaultHelpCommand
~~~~~~~~~~~~~~~~~~

.. attributetable:: nextcord.ext.commands.DefaultHelpCommand

.. autoclass:: nextcord.ext.commands.DefaultHelpCommand
    :members:
    :exclude-members: send_bot_help, send_cog_help, send_group_help, send_command_help, prepare_help_command

MinimalHelpCommand
~~~~~~~~~~~~~~~~~~

.. attributetable:: nextcord.ext.commands.MinimalHelpCommand

.. autoclass:: nextcord.ext.commands.MinimalHelpCommand
    :members:
    :exclude-members: send_bot_help, send_cog_help, send_group_help, send_command_help, prepare_help_command

Paginator
~~~~~~~~~

.. attributetable:: nextcord.ext.commands.Paginator

.. autoclass:: nextcord.ext.commands.Paginator
    :members:

Enums
-----

.. class:: BucketType
    :module: nextcord.ext.commands

    Specifies a type of bucket for, e.g. a cooldown.

    .. attribute:: default

        The default bucket operates on a global basis.
    .. attribute:: user

        The user bucket operates on a per-user basis.
    .. attribute:: guild

        The guild bucket operates on a per-guild basis.
    .. attribute:: channel

        The channel bucket operates on a per-channel basis.
    .. attribute:: member

        The member bucket operates on a per-member basis.
    .. attribute:: category

        The category bucket operates on a per-category basis.
    .. attribute:: role

        The role bucket operates on a per-role basis.

        .. versionadded:: 1.3


.. _ext_commands_api_checks:

Checks
------

.. autofunction:: nextcord.ext.commands.check(predicate)
    :decorator:

.. autofunction:: nextcord.ext.commands.check_any(*checks)
    :decorator:

.. autofunction:: nextcord.ext.commands.has_role(item)
    :decorator:

.. autofunction:: nextcord.ext.commands.has_permissions(**perms)
    :decorator:

.. autofunction:: nextcord.ext.commands.has_guild_permissions(**perms)
    :decorator:

.. autofunction:: nextcord.ext.commands.has_any_role(*items)
    :decorator:

.. autofunction:: nextcord.ext.commands.bot_has_role(item)
    :decorator:

.. autofunction:: nextcord.ext.commands.bot_has_permissions(**perms)
    :decorator:

.. autofunction:: nextcord.ext.commands.bot_has_guild_permissions(**perms)
    :decorator:

.. autofunction:: nextcord.ext.commands.bot_has_any_role(*items)
    :decorator:

.. autofunction:: nextcord.ext.commands.cooldown(rate, per, type=nextcord.ext.commands.BucketType.default)
    :decorator:

.. autofunction:: nextcord.ext.commands.dynamic_cooldown(cooldown, type=BucketType.default)
    :decorator:

.. autofunction:: nextcord.ext.commands.max_concurrency(number, per=nextcord.ext.commands.BucketType.default, *, wait=False)
    :decorator:

.. autofunction:: nextcord.ext.commands.before_invoke(coro)
    :decorator:

.. autofunction:: nextcord.ext.commands.after_invoke(coro)
    :decorator:

.. autofunction:: nextcord.ext.commands.guild_only(,)
    :decorator:

.. autofunction:: nextcord.ext.commands.dm_only(,)
    :decorator:

.. autofunction:: nextcord.ext.commands.is_owner(,)
    :decorator:

.. autofunction:: nextcord.ext.commands.is_nsfw(,)
    :decorator:

.. _ext_commands_api_context:

Cooldown
--------

.. attributetable:: nextcord.ext.commands.Cooldown

.. autoclass:: nextcord.ext.commands.Cooldown
    :members:

Context
-------

.. attributetable:: nextcord.ext.commands.Context

.. autoclass:: nextcord.ext.commands.Context
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: nextcord.ext.commands.Context.history
        :async-for:

    .. automethod:: nextcord.ext.commands.Context.typing
        :async-with:

.. _ext_commands_api_converters:

Converters
----------

.. autoclass:: nextcord.ext.commands.Converter
    :members:

.. autoclass:: nextcord.ext.commands.ObjectConverter
    :members:

.. autoclass:: nextcord.ext.commands.MemberConverter
    :members:

.. autoclass:: nextcord.ext.commands.UserConverter
    :members:

.. autoclass:: nextcord.ext.commands.MessageConverter
    :members:

.. autoclass:: nextcord.ext.commands.PartialMessageConverter
    :members:

.. autoclass:: nextcord.ext.commands.GuildChannelConverter
    :members:

.. autoclass:: nextcord.ext.commands.TextChannelConverter
    :members:

.. autoclass:: nextcord.ext.commands.VoiceChannelConverter
    :members:

.. autoclass:: nextcord.ext.commands.StageChannelConverter
    :members:

.. autoclass:: nextcord.ext.commands.CategoryChannelConverter
    :members:

.. autoclass:: nextcord.ext.commands.InviteConverter
    :members:

.. autoclass:: nextcord.ext.commands.GuildConverter
    :members:

.. autoclass:: nextcord.ext.commands.RoleConverter
    :members:

.. autoclass:: nextcord.ext.commands.GameConverter
    :members:

.. autoclass:: nextcord.ext.commands.ColourConverter
    :members:

.. autoclass:: nextcord.ext.commands.EmojiConverter
    :members:

.. autoclass:: nextcord.ext.commands.PartialEmojiConverter
    :members:

.. autoclass:: nextcord.ext.commands.ThreadConverter
    :members:

.. autoclass:: nextcord.ext.commands.GuildStickerConverter
    :members:

.. autoclass:: nextcord.ext.commands.clean_content
    :members:

.. autoclass:: nextcord.ext.commands.Greedy()

.. autofunction:: nextcord.ext.commands.run_converters

Flag Converter
~~~~~~~~~~~~~~

.. autoclass:: nextcord.ext.commands.FlagConverter
    :members:

.. autoclass:: nextcord.ext.commands.Flag()
    :members:

.. autofunction:: nextcord.ext.commands.flag

.. _ext_commands_api_errors:

Warnings
--------

.. autoclass:: nextcord.ext.commands.MissingMessageContentIntentWarning

Exceptions
----------

.. autoexception:: nextcord.ext.commands.CommandError
    :members:

.. autoexception:: nextcord.ext.commands.ConversionError
    :members:

.. autoexception:: nextcord.ext.commands.MissingRequiredArgument
    :members:

.. autoexception:: nextcord.ext.commands.ArgumentParsingError
    :members:

.. autoexception:: nextcord.ext.commands.UnexpectedQuoteError
    :members:

.. autoexception:: nextcord.ext.commands.InvalidEndOfQuotedStringError
    :members:

.. autoexception:: nextcord.ext.commands.ExpectedClosingQuoteError
    :members:

.. autoexception:: nextcord.ext.commands.BadArgument
    :members:

.. autoexception:: nextcord.ext.commands.BadUnionArgument
    :members:

.. autoexception:: nextcord.ext.commands.BadLiteralArgument
    :members:

.. autoexception:: nextcord.ext.commands.PrivateMessageOnly
    :members:

.. autoexception:: nextcord.ext.commands.NoPrivateMessage
    :members:

.. autoexception:: nextcord.ext.commands.CheckFailure
    :members:

.. autoexception:: nextcord.ext.commands.CheckAnyFailure
    :members:

.. autoexception:: nextcord.ext.commands.CommandNotFound
    :members:

.. autoexception:: nextcord.ext.commands.DisabledCommand
    :members:

.. autoexception:: nextcord.ext.commands.CommandInvokeError
    :members:

.. autoexception:: nextcord.ext.commands.TooManyArguments
    :members:

.. autoexception:: nextcord.ext.commands.UserInputError
    :members:

.. autoexception:: nextcord.ext.commands.CommandOnCooldown
    :members:

.. autoexception:: nextcord.ext.commands.MaxConcurrencyReached
    :members:

.. autoexception:: nextcord.ext.commands.NotOwner
    :members:

.. autoexception:: nextcord.ext.commands.MessageNotFound
    :members:

.. autoexception:: nextcord.ext.commands.MemberNotFound
    :members:

.. autoexception:: nextcord.ext.commands.GuildNotFound
    :members:

.. autoexception:: nextcord.ext.commands.UserNotFound
    :members:

.. autoexception:: nextcord.ext.commands.ChannelNotFound
    :members:

.. autoexception:: nextcord.ext.commands.ScheduledEventNotFound
    :members:

.. autoexception:: nextcord.ext.commands.ChannelNotReadable
    :members:

.. autoexception:: nextcord.ext.commands.ThreadNotFound
    :members:

.. autoexception:: nextcord.ext.commands.BadColourArgument
    :members:

.. autoexception:: nextcord.ext.commands.RoleNotFound
    :members:

.. autoexception:: nextcord.ext.commands.BadInviteArgument
    :members:

.. autoexception:: nextcord.ext.commands.EmojiNotFound
    :members:

.. autoexception:: nextcord.ext.commands.PartialEmojiConversionFailure
    :members:

.. autoexception:: nextcord.ext.commands.GuildStickerNotFound
    :members:

.. autoexception:: nextcord.ext.commands.BadBoolArgument
    :members:

.. autoexception:: nextcord.ext.commands.MissingPermissions
    :members:

.. autoexception:: nextcord.ext.commands.BotMissingPermissions
    :members:

.. autoexception:: nextcord.ext.commands.MissingRole
    :members:

.. autoexception:: nextcord.ext.commands.BotMissingRole
    :members:

.. autoexception:: nextcord.ext.commands.MissingAnyRole
    :members:

.. autoexception:: nextcord.ext.commands.BotMissingAnyRole
    :members:

.. autoexception:: nextcord.ext.commands.NSFWChannelRequired
    :members:

.. autoexception:: nextcord.ext.commands.FlagError
    :members:

.. autoexception:: nextcord.ext.commands.BadFlagArgument
    :members:

.. autoexception:: nextcord.ext.commands.MissingFlagArgument
    :members:

.. autoexception:: nextcord.ext.commands.TooManyFlags
    :members:

.. autoexception:: nextcord.ext.commands.MissingRequiredFlag
    :members:

.. autoexception:: nextcord.ext.commands.ExtensionError
    :members:

.. autoexception:: nextcord.ext.commands.ExtensionAlreadyLoaded
    :members:

.. autoexception:: nextcord.ext.commands.ExtensionNotLoaded
    :members:

.. autoexception:: nextcord.ext.commands.NoEntryPointError
    :members:

.. autoexception:: nextcord.ext.commands.InvalidSetupArguments
    :members:

.. autoexception:: nextcord.ext.commands.ExtensionFailed
    :members:

.. autoexception:: nextcord.ext.commands.ExtensionNotFound
    :members:

.. autoexception:: nextcord.ext.commands.CommandRegistrationError
    :members:


Exception Hierarchy
~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`~.DiscordException`
        - :exc:`~.commands.CommandError`
            - :exc:`~.commands.ConversionError`
            - :exc:`~.commands.UserInputError`
                - :exc:`~.commands.MissingRequiredArgument`
                - :exc:`~.commands.TooManyArguments`
                - :exc:`~.commands.BadArgument`
                    - :exc:`~.commands.MessageNotFound`
                    - :exc:`~.commands.MemberNotFound`
                    - :exc:`~.commands.GuildNotFound`
                    - :exc:`~.commands.UserNotFound`
                    - :exc:`~.commands.ChannelNotFound`
                    - :exc:`~.commands.ChannelNotReadable`
                    - :exc:`~.commands.BadColourArgument`
                    - :exc:`~.commands.RoleNotFound`
                    - :exc:`~.commands.BadInviteArgument`
                    - :exc:`~.commands.EmojiNotFound`
                    - :exc:`~.commands.GuildStickerNotFound`
                    - :exc:`~.commands.PartialEmojiConversionFailure`
                    - :exc:`~.commands.BadBoolArgument`
                    - :exc:`~.commands.ThreadNotFound`
                    - :exc:`~.commands.ScheduledEventNotFound`
                    - :exc:`~.commands.FlagError`
                        - :exc:`~.commands.BadFlagArgument`
                        - :exc:`~.commands.MissingFlagArgument`
                        - :exc:`~.commands.TooManyFlags`
                        - :exc:`~.commands.MissingRequiredFlag`
                - :exc:`~.commands.BadUnionArgument`
                - :exc:`~.commands.BadLiteralArgument`
                - :exc:`~.commands.ArgumentParsingError`
                    - :exc:`~.commands.UnexpectedQuoteError`
                    - :exc:`~.commands.InvalidEndOfQuotedStringError`
                    - :exc:`~.commands.ExpectedClosingQuoteError`
            - :exc:`~.commands.CommandNotFound`
            - :exc:`~.commands.CheckFailure`
                - :exc:`~.commands.CheckAnyFailure`
                - :exc:`~.commands.PrivateMessageOnly`
                - :exc:`~.commands.NoPrivateMessage`
                - :exc:`~.commands.NotOwner`
                - :exc:`~.commands.MissingPermissions`
                - :exc:`~.commands.BotMissingPermissions`
                - :exc:`~.commands.MissingRole`
                - :exc:`~.commands.BotMissingRole`
                - :exc:`~.commands.MissingAnyRole`
                - :exc:`~.commands.BotMissingAnyRole`
                - :exc:`~.commands.NSFWChannelRequired`
            - :exc:`~.commands.DisabledCommand`
            - :exc:`~.commands.CommandInvokeError`
            - :exc:`~.commands.CommandOnCooldown`
            - :exc:`~.commands.MaxConcurrencyReached`
        - :exc:`~.commands.ExtensionError`
            - :exc:`~.commands.ExtensionAlreadyLoaded`
            - :exc:`~.commands.ExtensionNotLoaded`
            - :exc:`~.commands.NoEntryPointError`
            - :exc:`~.commands.InvalidSetupArguments`
            - :exc:`~.commands.ExtensionFailed`
            - :exc:`~.commands.ExtensionNotFound`
    - :exc:`~.ClientException`
        - :exc:`~.commands.CommandRegistrationError`
