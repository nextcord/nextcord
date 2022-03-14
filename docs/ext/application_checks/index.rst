.. _discord_ext_application_checks:
.. module:: nextcord.ext.application_checks

``nextcord.ext.application_checks`` - checks and hooks for application commands
===============================================================================

To help with development, this extension is here to assist in development of application commands by hooking and checking before, during, after invoke and handling errors.
It has a similar interface to :ref:`ext.commands checks <discord_ext_commands>`

Checks
------

.. autofunction:: check
    :decorator:

.. autofunction:: check_any
    :decorator:

Pre-built Checks
----------------

Role Checks
~~~~~~~~~~~

.. autofunction:: has_role
    :decorator:

.. autofunction:: has_any_role
    :decorator:

.. autofunction:: bot_has_role
    :decorator:

.. autofunction:: bot_has_any_role
    :decorator:

Permission Checks
~~~~~~~~~~~~~~~~~

.. autofunction:: has_permissions
    :decorator:

.. autofunction:: bot_has_permissions
    :decorator:

.. autofunction:: has_guild_permissions
    :decorator:

.. autofunction:: bot_has_guild_permissions
    :decorator:

Scope Checks
~~~~~~~~~~~~

.. autofunction:: dm_only
    :decorator:

.. autofunction:: guild_only
    :decorator:

Other Checks
~~~~~~~~~~~~

.. autofunction:: is_owner
    :decorator:

.. autofunction:: is_nsfw
    :decorator:

Hooks
-----

.. autofunction:: application_command_before_invoke
    :decorator:

.. autofunction:: application_command_after_invoke
    :decorator:

Events
------

.. function:: on_application_command_error(interaction, error)

    The event that is fired when an error occurs during application command invocation.

    :param interaction: The interaction that caused the error.
    :type interaction: :class:`~.Interaction`
    :param error: The error that occurred.
    :type error: :class:`Exception`

Exceptions
----------

.. autoexception:: ApplicationCheckAnyFailure
    :members:

.. autoexception:: ApplicationNoPrivateMessage
    :members:

.. autoexception:: ApplicationMissingRole
    :members:

.. autoexception:: ApplicationMissingAnyRole
    :members:

.. autoexception:: ApplicationBotMissingRole
    :members:

.. autoexception:: ApplicationBotMissingAnyRole
    :members:

.. autoexception:: ApplicationMissingPermissions
    :members:

.. autoexception:: ApplicationBotMissingPermissions
    :members:

.. autoexception:: ApplicationPrivateMessageOnly
    :members:

.. autoexception:: ApplicationNotOwner
    :members:

.. autoexception:: ApplicationNSFWChannelRequired
    :members:

.. autoexception:: ApplicationCheckForBotOnly
    :members:

Exception Hierarchy
~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`~.DiscordException`
        - :exc:`~.ApplicationCheckFailure`
            - :exc:`~.ApplicationCheckAnyFailure`
            - :exc:`~.ApplicationNoPrivateMessage`
            - :exc:`~.ApplicationMissingRole`
            - :exc:`~.ApplicationMissingAnyRole`
            - :exc:`~.ApplicationBotMissingRole`
            - :exc:`~.ApplicationBotMissingAnyRole`
            - :exc:`~.ApplicationMissingPermissions`
            - :exc:`~.ApplicationBotMissingPermissions`
            - :exc:`~.ApplicationPrivateMessageOnly`
            - :exc:`~.ApplicationNotOwner`
            - :exc:`~.ApplicationNSFWChannelRequired`
            - :exc:`~.ApplicationCheckForBotOnly`
