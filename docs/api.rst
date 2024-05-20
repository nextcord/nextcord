.. currentmodule:: nextcord

API Reference
=============

The following section outlines the API of nextcord.

.. note::

    This module uses the Python logging module to log diagnostic and errors
    in an output-independent way.  If the logging module is not configured,
    these logs will not be output anywhere.  See :ref:`logging_setup` for
    more information on how to set up and use the logging module with
    nextcord.

Version Related Info
--------------------

There are two main ways to query version information about the library. For guarantees, check :ref:`version_guarantees`.

.. data:: version_info

    A named tuple that is similar to :obj:`py:sys.version_info`.

    Just like :obj:`py:sys.version_info` the valid values for ``releaselevel`` are
    'alpha', 'beta', 'candidate' and 'final'.

.. data:: __version__

    A string representation of the version. e.g. ``'1.0.0rc1'``. This is based
    off of :pep:`440`.

Clients
-------

Client
~~~~~~

.. attributetable:: Client

.. autoclass:: Client
    :members:
    :exclude-members: fetch_guilds, event, slash_command, user_command, message_command

    .. automethod:: Client.event()
        :decorator:

    .. automethod:: Client.slash_command
        :decorator:

    .. automethod:: Client.user_command
        :decorator:

    .. automethod:: Client.message_command
        :decorator:

    .. automethod:: Client.fetch_guilds
        :async-for:

AutoShardedClient
~~~~~~~~~~~~~~~~~

.. attributetable:: AutoShardedClient

.. autoclass:: AutoShardedClient
    :members:

Application Info
----------------

AppInfo
~~~~~~~

.. attributetable:: AppInfo

.. autoclass:: AppInfo()
    :members:

PartialAppInfo
~~~~~~~~~~~~~~

.. attributetable:: PartialAppInfo

.. autoclass:: PartialAppInfo()
    :members:

Team
~~~~

.. attributetable:: Team

.. autoclass:: Team()
    :members:

TeamMember
~~~~~~~~~~

.. attributetable:: TeamMember

.. autoclass:: TeamMember()
    :members:

Voice Related
-------------

VoiceClient
~~~~~~~~~~~

.. attributetable:: VoiceClient

.. autoclass:: VoiceClient()
    :members:
    :exclude-members: connect, on_voice_state_update, on_voice_server_update

VoiceProtocol
~~~~~~~~~~~~~

.. attributetable:: VoiceProtocol

.. autoclass:: VoiceProtocol
    :members:

AudioSource
~~~~~~~~~~~

.. attributetable:: AudioSource

.. autoclass:: AudioSource
    :members:

PCMAudio
~~~~~~~~

.. attributetable:: PCMAudio

.. autoclass:: PCMAudio
    :members:

FFmpegAudio
~~~~~~~~~~~

.. attributetable:: FFmpegAudio

.. autoclass:: FFmpegAudio
    :members:

FFmpegPCMAudio
~~~~~~~~~~~~~~

.. attributetable:: FFmpegPCMAudio

.. autoclass:: FFmpegPCMAudio
    :members:

FFmpegOpusAudio
~~~~~~~~~~~~~~~

.. attributetable:: FFmpegOpusAudio

.. autoclass:: FFmpegOpusAudio
    :members:

PCMVolumeTransformer
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PCMVolumeTransformer

.. autoclass:: PCMVolumeTransformer
    :members:

Opus Library
~~~~~~~~~~~~

.. autofunction:: nextcord.opus.load_opus

.. autofunction:: nextcord.opus.is_loaded

.. _discord-api-events:

Event Reference
---------------

This section outlines the different types of events listened by :class:`Client`.

There are two ways to register an event, the first way is through the use of
:meth:`Client.event`. The second way is through subclassing :class:`Client` and
overriding the specific events. For example: ::

    import nextcord

    class MyClient(nextcord.Client):
        async def on_message(self, message):
            if message.author == self.user:
                return

            if message.content.startswith('$hello'):
                await message.channel.send('Hello World!')


If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to print a traceback and ignoring the exception.

.. warning::

    All the events must be a |coroutine_link|_. If they aren't, then you might get unexpected
    errors. To turn a function into a coroutine, they must be ``async def``
    functions.

.. function:: on_connect()

    Called when the client has successfully connected to Discord. This is not
    the same as the client being fully prepared, see :func:`on_ready` for that.

    The warnings on :func:`on_ready` also apply.

.. function:: on_shard_connect(shard_id)

    Similar to :func:`on_connect` except used by :class:`AutoShardedClient`
    to denote when a particular shard ID has connected to Discord.

    .. versionadded:: 1.4

    :param shard_id: The shard ID that has connected.
    :type shard_id: :class:`int`

.. function:: on_disconnect()

    Called when the client has disconnected from Discord, or a connection attempt to Discord has failed.
    This could happen either through the internet being disconnected, explicit calls to close,
    or Discord terminating the connection one way or the other.

    This function can be called many times without a corresponding :func:`on_connect` call.

.. function:: on_shard_disconnect(shard_id)

    Similar to :func:`on_disconnect` except used by :class:`AutoShardedClient`
    to denote when a particular shard ID has disconnected from Discord.

    .. versionadded:: 1.4

    :param shard_id: The shard ID that has disconnected.
    :type shard_id: :class:`int`

.. function:: on_http_ratelimit(limit, remaining, reset_after, bucket, scope)

    Called when a HTTP request in progress either exhausts its bucket or gets a 429 response.
    For more information on how a ratelimit bucket is defined, check out the [Discord API Docs](https://discord.dev/topics/rate-limits).

    If the 429 response is a global ratelimit, then use :func:`on_global_http_ratelimit` instead.

    .. versionadded:: 2.4

    :param limit: The amount of requests that have been made under the bucket that the request correlates to.
    :type limit: :class:`int`
    :param remaining: The amount of remaining requests that can be made under the bucket that the request correlates to.
    :type remaining: :class:`int`
    :param reset_after: The amount of time we have to wait before making another request under the same bucket.
    :type reset_after: :class:`float`
    :param bucket: The hash correlating to the bucket of the request from Discord. This hash denotes the rate limit being encountered.
    :type bucket: :class:`str`
    :param scope: If we get a 429, the scope of the 429 response. This value can either be "user" (rate limit relating to the user) or "shared" (rate limit relating to a resource).
    :type scope: Optional[:class:`str`]

.. function:: on_global_http_ratelimit(retry_after)

    Called when a HTTP request in progress gets a 429 response and the scope is global.

    If the 429 response is a non-global ratelimit or you want to track when the bucket expires,
    then use :func:`on_http_ratelimit` instead.

    .. versionadded:: 2.4

    :param retry_after: The amount of time we have to wait before making another request.
    :type retry_after: :class:`float`

.. function:: on_ready()

    Called when the client is done preparing the data received from Discord. Usually after login is successful
    and the :attr:`Client.guilds` and co. are filled up.

    .. warning::

        This function is not guaranteed to be the first event called.
        Likewise, this function is **not** guaranteed to only be called
        once. This library implements reconnection logic and thus will
        end up calling this event whenever a RESUME request fails.

.. function:: on_shard_ready(shard_id)

    Similar to :func:`on_ready` except used by :class:`AutoShardedClient`
    to denote when a particular shard ID has become ready.

    :param shard_id: The shard ID that is ready.
    :type shard_id: :class:`int`

.. function:: on_resumed()

    Called when the client has resumed a session.

.. function:: on_shard_resumed(shard_id)

    Similar to :func:`on_resumed` except used by :class:`AutoShardedClient`
    to denote when a particular shard ID has resumed a session.

    .. versionadded:: 1.4

    :param shard_id: The shard ID that has resumed.
    :type shard_id: :class:`int`

.. function:: on_error(event, *args, **kwargs)

    Usually when an event raises an uncaught exception, a traceback is
    printed to stderr and the exception is ignored. If you want to
    change this behaviour and handle the exception for whatever reason
    yourself, this event can be overridden. Which, when done, will
    suppress the default action of printing the traceback.

    The information of the exception raised and the exception itself can
    be retrieved with a standard call to :func:`sys.exc_info`.

    If you want exception to propagate out of the :class:`Client` class
    you can define an ``on_error`` handler consisting of a single empty
    :ref:`raise statement <py:raise>`. Exceptions raised by ``on_error`` will not be
    handled in any way by :class:`Client`.

    .. note::

        ``on_error`` will only be dispatched to :meth:`Client.event`.

        It will not be received by :meth:`Client.wait_for`, or, if used,
        :ref:`ext_commands_api_bot` listeners such as
        :meth:`~ext.commands.Bot.listen` or :meth:`~ext.commands.Cog.listener`.

    :param event: The name of the event that raised the exception.
    :type event: :class:`str`

    :param args: The positional arguments for the event that raised the
        exception.
    :param kwargs: The keyword arguments for the event that raised the
        exception.

.. function:: on_close()

    Called when the client is exiting the event loop and shutting down.

.. function:: on_socket_event_type(event_type)

    Called whenever a websocket event is received from the WebSocket.

    This is mainly useful for logging how many events you are receiving
    from the Discord gateway.

    .. versionadded:: 2.0

    :param event_type: The event type from Discord that is received, e.g. ``'READY'``.
    :type event_type: :class:`str`

.. function:: on_socket_raw_receive(msg)

    Called whenever a message is completely received from the WebSocket, before
    it's processed and parsed. This event is always dispatched when a
    complete message is received and the passed data is not parsed in any way.

    This is only really useful for grabbing the WebSocket stream and
    debugging purposes.

    This requires setting the ``enable_debug_events`` setting in the :class:`Client`.

    .. note::

        This is only for the messages received from the client
        WebSocket. The voice WebSocket will not trigger this event.

    :param msg: The message passed in from the WebSocket library.
    :type msg: :class:`str`

.. function:: on_socket_raw_send(payload)

    Called whenever a send operation is done on the WebSocket before the
    message is sent. The passed parameter is the message that is being
    sent to the WebSocket.

    This is only really useful for grabbing the WebSocket stream and
    debugging purposes.

    This requires setting the ``enable_debug_events`` setting in the :class:`Client`.

    .. note::

        This is only for the messages sent from the client
        WebSocket. The voice WebSocket will not trigger this event.

    :param payload: The message that is about to be passed on to the
                    WebSocket library. It can be :class:`bytes` to denote a binary
                    message or :class:`str` to denote a regular text message.

.. function:: on_typing(channel, user, when)

    Called when someone begins typing a message.

    The ``channel`` parameter can be a :class:`abc.Messageable` instance.
    Which could either be :class:`TextChannel`, :class:`GroupChannel`, or
    :class:`DMChannel`.

    If the ``channel`` is a :class:`TextChannel` then the ``user`` parameter
    is a :class:`Member`, otherwise it is a :class:`User`.

    This requires :attr:`Intents.typing` to be enabled.

    :param channel: The location where the typing originated from.
    :type channel: :class:`abc.Messageable`
    :param user: The user that started typing.
    :type user: Union[:class:`User`, :class:`Member`]
    :param when: When the typing started as an aware datetime in UTC.
    :type when: :class:`datetime.datetime`

.. function:: on_raw_typing(payload)

    Called when someone begins typing a message. Unlike :func:`on_typing`, this is
    called regardless if the user can be found in the bot's cache or not.

    If the typing event is occuring in a guild,
    the member that started typing can be accessed via :attr:`RawTypingEvent.member`

    This requires :attr:`Intents.typing` to be enabled.

    :param payload: The raw typing payload.
    :type payload: :class:`RawTypingEvent`

.. function:: on_message(message)

    Called when a :class:`Message` is created and sent.

    This requires :attr:`Intents.messages` to be enabled.

    .. warning::

        Your bot's own messages and private messages are sent through this
        event. This can lead cases of 'recursion' depending on how your bot was
        programmed. If you want the bot to not reply to itself, consider
        checking the user IDs. Note that :class:`~ext.commands.Bot` does not
        have this problem.

    :param message: The current message.
    :type message: :class:`Message`

.. function:: on_message_delete(message)

    Called when a message is deleted. If the message is not found in the
    internal message cache, then this event will not be called.
    Messages might not be in cache if the message is too old
    or the client is participating in high traffic guilds.

    If this occurs increase the :class:`max_messages <Client>` parameter
    or use the :func:`on_raw_message_delete` event instead.

    This requires :attr:`Intents.messages` to be enabled.

    :param message: The deleted message.
    :type message: :class:`Message`

.. function:: on_bulk_message_delete(messages)

    Called when messages are bulk deleted. If none of the messages deleted
    are found in the internal message cache, then this event will not be called.
    If individual messages were not found in the internal message cache,
    this event will still be called, but the messages not found will not be included in
    the messages list. Messages might not be in cache if the message is too old
    or the client is participating in high traffic guilds.

    If this occurs increase the :class:`max_messages <Client>` parameter
    or use the :func:`on_raw_bulk_message_delete` event instead.

    This requires :attr:`Intents.messages` to be enabled.

    :param messages: The messages that have been deleted.
    :type messages: List[:class:`Message`]

.. function:: on_raw_message_delete(payload)

    Called when a message is deleted. Unlike :func:`on_message_delete`, this is
    called regardless of the message being in the internal message cache or not.

    If the message is found in the message cache,
    it can be accessed via :attr:`RawMessageDeleteEvent.cached_message`

    This requires :attr:`Intents.messages` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawMessageDeleteEvent`

.. function:: on_raw_bulk_message_delete(payload)

    Called when a bulk delete is triggered. Unlike :func:`on_bulk_message_delete`, this is
    called regardless of the messages being in the internal message cache or not.

    If the messages are found in the message cache,
    they can be accessed via :attr:`RawBulkMessageDeleteEvent.cached_messages`

    This requires :attr:`Intents.messages` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawBulkMessageDeleteEvent`

.. function:: on_message_edit(before, after)

    Called when a :class:`Message` receives an update event. If the message is not found
    in the internal message cache, then these events will not be called.
    Messages might not be in cache if the message is too old
    or the client is participating in high traffic guilds.

    If this occurs increase the :class:`max_messages <Client>` parameter
    or use the :func:`on_raw_message_edit` event instead.

    The following non-exhaustive cases trigger this event:

    - A message has been pinned or unpinned.
    - The message content has been changed.
    - The message has received an embed.

        - For performance reasons, the embed server does not do this in a "consistent" manner.

    - The message's embeds were suppressed or unsuppressed.
    - A call message has received an update to its participants or ending time.

    This requires :attr:`Intents.messages` to be enabled.

    :param before: The previous version of the message.
    :type before: :class:`Message`
    :param after: The current version of the message.
    :type after: :class:`Message`

.. function:: on_raw_message_edit(payload)

    Called when a message is edited. Unlike :func:`on_message_edit`, this is called
    regardless of the state of the internal message cache.

    If the message is found in the message cache,
    it can be accessed via :attr:`RawMessageUpdateEvent.cached_message`. The cached message represents
    the message before it has been edited. For example, if the content of a message is modified and
    triggers the :func:`on_raw_message_edit` coroutine, the :attr:`RawMessageUpdateEvent.cached_message`
    will return a :class:`Message` object that represents the message before the content was modified.

    Due to the inherently raw nature of this event, the data parameter coincides with
    the raw data given by the `gateway <https://discord.com/developers/docs/topics/gateway#message-update>`_.

    Since the data payload can be partial, care must be taken when accessing stuff in the dictionary.
    One example of a common case of partial data is when the ``'content'`` key is inaccessible. This
    denotes an "embed" only edit, which is an edit in which only the embeds are updated by the Discord
    embed server.

    This requires :attr:`Intents.messages` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawMessageUpdateEvent`

.. function:: on_reaction_add(reaction, user)

    Called when a message has a reaction added to it. Similar to :func:`on_message_edit`,
    if the message is not found in the internal message cache, then this
    event will not be called. Consider using :func:`on_raw_reaction_add` instead.

    .. note::

        To get the :class:`Message` being reacted, access it via :attr:`Reaction.message`.

    This requires :attr:`Intents.reactions` to be enabled.

    .. note::

        This doesn't require :attr:`Intents.members` within a guild context,
        but due to Discord not providing updated user information in a direct message
        it's required for direct messages to receive this event.
        Consider using :func:`on_raw_reaction_add` if you need this and do not otherwise want
        to enable the members intent.

    :param reaction: The current state of the reaction.
    :type reaction: :class:`Reaction`
    :param user: The user who added the reaction.
    :type user: Union[:class:`Member`, :class:`User`]

.. function:: on_raw_reaction_add(payload)

    Called when a message has a reaction added. Unlike :func:`on_reaction_add`, this is
    called regardless of the state of the internal message cache.

    This requires :attr:`Intents.reactions` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawReactionActionEvent`

.. function:: on_reaction_remove(reaction, user)

    Called when a message has a reaction removed from it. Similar to on_message_edit,
    if the message is not found in the internal message cache, then this event
    will not be called.

    .. note::

        To get the message being reacted, access it via :attr:`Reaction.message`.

    This requires both :attr:`Intents.reactions` and :attr:`Intents.members` to be enabled.

    .. note::

        Consider using :func:`on_raw_reaction_remove` if you need this and do not want
        to enable the members intent.

    :param reaction: The current state of the reaction.
    :type reaction: :class:`Reaction`
    :param user: The user who added the reaction.
    :type user: Union[:class:`Member`, :class:`User`]

.. function:: on_raw_reaction_remove(payload)

    Called when a message has a reaction removed. Unlike :func:`on_reaction_remove`, this is
    called regardless of the state of the internal message cache.

    This requires :attr:`Intents.reactions` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawReactionActionEvent`

.. function:: on_reaction_clear(message, reactions)

    Called when a message has all its reactions removed from it. Similar to :func:`on_message_edit`,
    if the message is not found in the internal message cache, then this event
    will not be called. Consider using :func:`on_raw_reaction_clear` instead.

    This requires :attr:`Intents.reactions` to be enabled.

    :param message: The message that had its reactions cleared.
    :type message: :class:`Message`
    :param reactions: The reactions that were removed.
    :type reactions: List[:class:`Reaction`]

.. function:: on_raw_reaction_clear(payload)

    Called when a message has all its reactions removed. Unlike :func:`on_reaction_clear`,
    this is called regardless of the state of the internal message cache.

    This requires :attr:`Intents.reactions` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawReactionClearEvent`

.. function:: on_reaction_clear_emoji(reaction)

    Called when a message has a specific reaction removed from it. Similar to :func:`on_message_edit`,
    if the message is not found in the internal message cache, then this event
    will not be called. Consider using :func:`on_raw_reaction_clear_emoji` instead.

    This requires :attr:`Intents.reactions` to be enabled.

    .. versionadded:: 1.3

    :param reaction: The reaction that got cleared.
    :type reaction: :class:`Reaction`

.. function:: on_raw_reaction_clear_emoji(payload)

    Called when a message has a specific reaction removed from it. Unlike :func:`on_reaction_clear_emoji` this is called
    regardless of the state of the internal message cache.

    This requires :attr:`Intents.reactions` to be enabled.

    .. versionadded:: 1.3

    :param payload: The raw event payload data.
    :type payload: :class:`RawReactionClearEmojiEvent`

.. function:: on_interaction(interaction)

    Called when an interaction happened.

    This currently happens due to slash command invocations or components being used.

    .. warning::

        This is a low level function that is not generally meant to be used.
        If you are working with components, consider using the callbacks associated
        with the :class:`~nextcord.ui.View` instead as it provides a nicer user experience.

    .. versionadded:: 2.0

    :param interaction: The interaction data.
    :type interaction: :class:`Interaction`

.. function:: on_private_channel_update(before, after)

    Called whenever a private group DM is updated. e.g. changed name or topic.

    This requires :attr:`Intents.messages` to be enabled.

    :param before: The updated group channel's old info.
    :type before: :class:`GroupChannel`
    :param after: The updated group channel's new info.
    :type after: :class:`GroupChannel`

.. function:: on_private_channel_pins_update(channel, last_pin)

    Called whenever a message is pinned or unpinned from a private channel.

    :param channel: The private channel that had its pins updated.
    :type channel: :class:`abc.PrivateChannel`
    :param last_pin: The latest message that was pinned as an aware datetime in UTC. Could be ``None``.
    :type last_pin: Optional[:class:`datetime.datetime`]

.. function:: on_guild_channel_delete(channel)
              on_guild_channel_create(channel)

    Called whenever a guild channel is deleted or created.

    Note that you can get the guild from :attr:`~abc.GuildChannel.guild`.

    This requires :attr:`Intents.guilds` to be enabled.

    :param channel: The guild channel that got created or deleted.
    :type channel: :class:`abc.GuildChannel`

.. function:: on_guild_channel_update(before, after)

    Called whenever a guild channel is updated. e.g. changed name, topic, permissions.

    This requires :attr:`Intents.guilds` to be enabled.

    :param before: The updated guild channel's old info.
    :type before: :class:`abc.GuildChannel`
    :param after: The updated guild channel's new info.
    :type after: :class:`abc.GuildChannel`

.. function:: on_guild_channel_pins_update(channel, last_pin)

    Called whenever a message is pinned or unpinned from a guild channel.

    This requires :attr:`Intents.guilds` to be enabled.

    :param channel: The guild channel that had its pins updated.
    :type channel: Union[:class:`~TextChannel`, :class:`Thread`]
    :param last_pin: The latest message that was pinned as an aware datetime in UTC. Could be ``None``.
    :type last_pin: Optional[:class:`datetime.datetime`]

.. function:: on_thread_create(thread)

    Called when a thread is created.

    .. versionadded:: 2.4

    :param thread: The thread that got created.
    :type thread: :class:`Thread`

.. function:: on_thread_join(thread)

    Called whenever a thread is joined or created.

    Note that you can get the guild from :attr:`Thread.guild`.

    This requires :attr:`Intents.guilds` to be enabled.

    .. note::

        This event is also called when a thread is created. To differentiate,
        use :func:`on_thread_create` instead. This is done to avoid a breaking change
        in v2.

    .. versionadded:: 2.0

    :param thread: The thread that got joined.
    :type thread: :class:`Thread`

.. function:: on_thread_remove(thread)

    Called whenever a thread is removed. This is different from a thread being deleted.

    Note that you can get the guild from :attr:`Thread.guild`.

    This requires :attr:`Intents.guilds` to be enabled.

    .. warning::

        Due to technical limitations, this event might not be called
        as soon as one expects. Since the library tracks thread membership
        locally, the API only sends updated thread membership status upon being
        synced by joining a thread.

    .. versionadded:: 2.0

    :param thread: The thread that got removed.
    :type thread: :class:`Thread`

.. function:: on_thread_delete(thread)

    Called whenever a thread is deleted.

    Note that you can get the guild from :attr:`Thread.guild`.

    This requires :attr:`Intents.guilds` to be enabled.

    .. versionadded:: 2.0

    :param thread: The thread that got deleted.
    :type thread: :class:`Thread`

.. function:: on_thread_member_join(member)
              on_thread_member_remove(member)

    Called when a :class:`ThreadMember` leaves or joins a :class:`Thread`.

    You can get the thread a member belongs in by accessing :attr:`ThreadMember.thread`.

    This requires :attr:`Intents.members` to be enabled.

    .. versionadded:: 2.0

    :param member: The member who joined or left.
    :type member: :class:`ThreadMember`

.. function:: on_thread_update(before, after)

    Called whenever a thread is updated.

    This requires :attr:`Intents.guilds` to be enabled.

    .. versionadded:: 2.0

    :param before: The updated thread's old info.
    :type before: :class:`Thread`
    :param after: The updated thread's new info.
    :type after: :class:`Thread`

.. function:: on_guild_integrations_update(guild)

    Called whenever an integration is created, modified, or removed from a guild.

    This requires :attr:`Intents.integrations` to be enabled.

    .. versionadded:: 1.4

    :param guild: The guild that had its integrations updated.
    :type guild: :class:`Guild`

.. function:: on_integration_create(integration)

    Called when an integration is created.

    This requires :attr:`Intents.integrations` to be enabled.

    .. versionadded:: 2.0

    :param integration: The integration that was created.
    :type integration: :class:`Integration`

.. function:: on_integration_update(integration)

    Called when an integration is updated.

    This requires :attr:`Intents.integrations` to be enabled.

    .. versionadded:: 2.0

    :param integration: The integration that was created.
    :type integration: :class:`Integration`

.. function:: on_raw_integration_delete(payload)

    Called when an integration is deleted.

    This requires :attr:`Intents.integrations` to be enabled.

    .. versionadded:: 2.0

    :param payload: The raw event payload data.
    :type payload: :class:`RawIntegrationDeleteEvent`

.. function:: on_webhooks_update(channel)

    Called whenever a webhook is created, modified, or removed from a guild channel.

    This requires :attr:`Intents.webhooks` to be enabled.

    :param channel: The channel that had its webhooks updated.
    :type channel: :class:`TextChannel`

.. function:: on_member_join(member)
              on_member_remove(member)

    Called when a :class:`Member` leaves or joins a :class:`Guild`.

    This requires :attr:`Intents.members` to be enabled.

    :param member: The member who joined or left.
    :type member: :class:`Member`

.. function:: on_raw_member_remove(payload)

    Called when a :class:`Member` leaves a :class:`Guild`. Unlike :func:`on_member_remove` this is called
    regardless of the state of the internal message cache.

    This requires :attr:`Intents.members` to be enabled.

    .. versionadded:: 2.0

    :param payload: The raw event payload data.
    :type payload: :class:`RawMemberRemoveEvent`

.. function:: on_member_update(before, after)

    Called when a :class:`Member` updates their profile.

    This is called when one or more of the following things change:

    - nickname
    - roles
    - pending
    - flags

    This requires :attr:`Intents.members` to be enabled.

    :param before: The updated member's old info.
    :type before: :class:`Member`
    :param after: The updated member's updated info.
    :type after: :class:`Member`

.. function:: on_presence_update(before, after)

    Called when a :class:`Member` updates their presence.

    This is called when one or more of the following things change:

    - status
    - activity

    This requires :attr:`Intents.presences` and :attr:`Intents.members` to be enabled.

    .. versionadded:: 2.0

    :param before: The updated member's old info.
    :type before: :class:`Member`
    :param after: The updated member's updated info.
    :type after: :class:`Member`

.. function:: on_user_update(before, after)

    Called when a :class:`User` updates their profile.

    This is called when one or more of the following things change:

    - avatar
    - username
    - discriminator

    This requires :attr:`Intents.members` to be enabled.

    :param before: The updated user's old info.
    :type before: :class:`User`
    :param after: The updated user's updated info.
    :type after: :class:`User`

.. function:: on_guild_join(guild)

    Called when a :class:`Guild` is either created by the :class:`Client` or when the
    :class:`Client` joins a guild.

    This requires :attr:`Intents.guilds` to be enabled.

    :param guild: The guild that was joined.
    :type guild: :class:`Guild`

.. function:: on_guild_remove(guild)

    Called when a :class:`Guild` is removed from the :class:`Client`.

    This happens through, but not limited to, these circumstances:

    - The client got banned.
    - The client got kicked.
    - The client left the guild.
    - The client or the guild owner deleted the guild.

    For this event to be invoked, the :class:`Client` must have
    been part of the guild to begin with. (i.e. it is part of :attr:`Client.guilds`)

    This requires :attr:`Intents.guilds` to be enabled.

    :param guild: The guild that got removed.
    :type guild: :class:`Guild`

.. function:: on_guild_update(before, after)

    Called when a :class:`Guild` updates, for example:

    - Changed name
    - Changed AFK channel
    - Changed AFK timeout
    - etc

    This requires :attr:`Intents.guilds` to be enabled.

    :param before: The guild prior to being updated.
    :type before: :class:`Guild`
    :param after: The guild after being updated.
    :type after: :class:`Guild`

.. function:: on_guild_role_create(role)
              on_guild_role_delete(role)

    Called when a :class:`Guild` creates or deletes a new :class:`Role`.

    To get the guild it belongs to, use :attr:`Role.guild`.

    This requires :attr:`Intents.guilds` to be enabled.

    :param role: The role that was created or deleted.
    :type role: :class:`Role`

.. function:: on_guild_role_update(before, after)

    Called when a :class:`Role` is changed guild-wide.

    This requires :attr:`Intents.guilds` to be enabled.

    :param before: The updated role's old info.
    :type before: :class:`Role`
    :param after: The updated role's updated info.
    :type after: :class:`Role`

.. function:: on_guild_emojis_update(guild, before, after)

    Called when a :class:`Guild` adds or removes :class:`Emoji`.

    This requires :attr:`Intents.emojis_and_stickers` to be enabled.

    :param guild: The guild who got their emojis updated.
    :type guild: :class:`Guild`
    :param before: A list of emojis before the update.
    :type before: Sequence[:class:`Emoji`]
    :param after: A list of emojis after the update.
    :type after: Sequence[:class:`Emoji`]

.. function:: on_guild_stickers_update(guild, before, after)

    Called when a :class:`Guild` updates its stickers.

    This requires :attr:`Intents.emojis_and_stickers` to be enabled.

    .. versionadded:: 2.0

    :param guild: The guild who got their stickers updated.
    :type guild: :class:`Guild`
    :param before: A list of stickers before the update.
    :type before: Sequence[:class:`GuildSticker`]
    :param after: A list of stickers after the update.
    :type after: Sequence[:class:`GuildSticker`]

.. function:: on_guild_available(guild)
              on_guild_unavailable(guild)

    Called when a guild becomes available or unavailable. The guild must have
    existed in the :attr:`Client.guilds` cache.

    This requires :attr:`Intents.guilds` to be enabled.

    :param guild: The :class:`Guild` that has changed availability.

.. function:: on_voice_state_update(member, before, after)

    Called when a :class:`Member` changes their :class:`VoiceState`.

    The following, but not limited to, examples illustrate when this event is called:

    - A member joins a voice or stage channel.
    - A member leaves a voice or stage channel.
    - A member is muted or deafened by their own accord.
    - A member is muted or deafened by a guild administrator.

    This requires :attr:`Intents.voice_states` to be enabled.

    :param member: The member whose voice states changed.
    :type member: :class:`Member`
    :param before: The voice state prior to the changes.
    :type before: :class:`VoiceState`
    :param after: The voice state after the changes.
    :type after: :class:`VoiceState`

.. function:: on_stage_instance_create(stage_instance)
              on_stage_instance_delete(stage_instance)

    Called when a :class:`StageInstance` is created or deleted for a :class:`StageChannel`.

    .. versionadded:: 2.0

    :param stage_instance: The stage instance that was created or deleted.
    :type stage_instance: :class:`StageInstance`

.. function:: on_stage_instance_update(before, after)

    Called when a :class:`StageInstance` is updated.

    The following, but not limited to, examples illustrate when this event is called:

    - The topic is changed.
    - The privacy level is changed.

    .. versionadded:: 2.0

    :param before: The stage instance before the update.
    :type before: :class:`StageInstance`
    :param after: The stage instance after the update.
    :type after: :class:`StageInstance`

.. function:: on_member_ban(guild, user)

    Called when user gets banned from a :class:`Guild`.

    This requires :attr:`Intents.bans` to be enabled.

    :param guild: The guild the user got banned from.
    :type guild: :class:`Guild`
    :param user: The user that got banned.
                 Can be either :class:`User` or :class:`Member` depending if
                 the user was in the guild or not at the time of removal.
    :type user: Union[:class:`User`, :class:`Member`]

.. function:: on_member_unban(guild, user)

    Called when a :class:`User` gets unbanned from a :class:`Guild`.

    This requires :attr:`Intents.bans` to be enabled.

    :param guild: The guild the user got unbanned from.
    :type guild: :class:`Guild`
    :param user: The user that got unbanned.
    :type user: :class:`User`

.. function:: on_invite_create(invite)

    Called when an :class:`Invite` is created.
    You must have the :attr:`~Permissions.manage_channels` permission to receive this.

    .. versionadded:: 1.3

    .. note::

        There is a rare possibility that the :attr:`Invite.guild` and :attr:`Invite.channel`
        attributes will be of :class:`Object` rather than the respective models.

    This requires :attr:`Intents.invites` to be enabled.

    :param invite: The invite that was created.
    :type invite: :class:`Invite`

.. function:: on_invite_delete(invite)

    Called when an :class:`Invite` is deleted.
    You must have the :attr:`~Permissions.manage_channels` permission to receive this.

    .. versionadded:: 1.3

    .. note::

        There is a rare possibility that the :attr:`Invite.guild` and :attr:`Invite.channel`
        attributes will be of :class:`Object` rather than the respective models.

        Outside of those two attributes, the only other attribute guaranteed to be
        filled by the Discord gateway for this event is :attr:`Invite.code`.

    This requires :attr:`Intents.invites` to be enabled.

    :param invite: The invite that was deleted.
    :type invite: :class:`Invite`

.. function:: on_group_join(channel, user)
              on_group_remove(channel, user)

    Called when someone joins or leaves a :class:`GroupChannel`.

    :param channel: The group that the user joined or left.
    :type channel: :class:`GroupChannel`
    :param user: The user that joined or left.
    :type user: :class:`User`

.. function:: on_guild_scheduled_event_create(event)

    Called when a :class:`ScheduledEvent` is created.

    :param event: The event that was created.
    :type event: :class:`ScheduledEvent`

.. function:: on_guild_scheduled_event_update(before, after)

    Called when a :class:`ScheduledEvent` is updated.

    :param before: The event before it was updated.
    :type before: :class:`ScheduledEvent`
    :param after: The event after it was updated.
    :type after: :class:`ScheduledEvent`

.. function:: on_guild_scheduled_event_delete(event)

    Called when a :class:`ScheduledEvent` is deleted.

    :param event: The event that was deleted.
    :type event: :class:`ScheduledEvent`

.. function:: on_guild_scheduled_event_user_add(event, user)
              on_guild_scheduled_event_user_remove(event, user)

    Called when a :class:`ScheduledEventUser` is interested in a
    :class:`ScheduledEvent`.

    :param event: The event that the user is interested in.
    :type event: :class:`ScheduledEvent`
    :param user: The user that interested.
    :type user: :class:`ScheduledEventUser`

.. function:: on_auto_moderation_rule_create(rule)

    Called when an :class:`AutoModerationRule` is created.

    .. versionadded:: 2.1

    :param rule: The rule that was created.
    :type rule: :class:`AutoModerationRule`

.. function:: on_auto_moderation_rule_update(rule)

    Called when an :class:`AutoModerationRule` is edited.

    .. versionadded:: 2.1

    :param rule: The newly edited rule.
    :type rule: :class:`AutoModerationRule`

.. function:: on_auto_moderation_rule_delete(rule)

    Called when a :class:`AutoModerationRule` is deleted.

    .. versionadded:: 2.1

    :param rule: The deleted rule.
    :type rule: :class:`AutoModerationRule`

.. function:: on_auto_moderation_action_execution(execution)

    Called when an :class:`AutoModerationAction` is executed.

    .. versionadded:: 2.1

    :param execution: The object containing the execution information.
    :type execution: :class:`AutoModerationActionExecution`

.. function:: on_guild_audit_log_entry_create(entry)

    Called when an :class:`AuditLogEntry` is created.

    .. versionadded:: 2.4

    :param entry: The entry that was created.
    :type entry: :class:`AuditLogEntry`

.. _discord-api-utils:

Utility Functions
-----------------

.. autofunction:: nextcord.utils.find

.. autofunction:: nextcord.utils.get

.. autofunction:: nextcord.utils.snowflake_time

.. autofunction:: nextcord.utils.oauth_url

.. autofunction:: nextcord.utils.remove_markdown

.. autofunction:: nextcord.utils.escape_markdown

.. autofunction:: nextcord.utils.escape_mentions

.. autofunction:: nextcord.utils.parse_raw_mentions

.. autofunction:: nextcord.utils.parse_raw_role_mentions

.. autofunction:: nextcord.utils.parse_raw_channel_mentions

.. autofunction:: nextcord.utils.resolve_invite

.. autofunction:: nextcord.utils.resolve_template

.. autofunction:: nextcord.utils.sleep_until

.. autofunction:: nextcord.utils.utcnow

.. autofunction:: nextcord.utils.format_dt

.. autofunction:: nextcord.utils.as_chunks

.. _discord-api-enums:

Enumerations
------------

The API provides some enumerations for certain types of strings to avoid the API
from being stringly typed in case the strings change in the future.

All enumerations are subclasses of an internal class which mimics the behaviour
of :class:`enum.Enum`.

.. autoclass:: ChannelType
    :members:

.. autoclass:: MessageType
    :members:

.. autoclass:: VoiceRegion
    :members:

.. autoclass:: VerificationLevel
    :members:

.. autoclass:: ContentFilter
    :members:

.. autoclass:: Status
    :members:

.. autoclass:: DefaultAvatar
    :members:

.. autoclass:: NotificationLevel
    :members:

.. autoclass:: AuditLogActionCategory
    :members:

.. autoclass:: UserFlags
    :members:

.. autoclass:: ActivityType
    :members:

.. autoclass:: TeamMembershipState
    :members:

.. autoclass:: WebhookType
    :members:

.. autoclass:: ExpireBehaviour
    :members:

.. autoclass:: StickerType
    :members:

.. autoclass:: StickerFormatType
    :members:

.. autoclass:: InviteTarget
    :members:

.. autoclass:: InteractionType
    :members:

.. autoclass:: InteractionResponseType
    :members:

.. autoclass:: Locale
    :members:

.. autoclass:: VideoQualityMode
    :members:

.. autoclass:: ComponentType
    :members:

.. autoclass:: ButtonStyle
    :members:

.. autoclass:: TextInputStyle
    :members:

.. autoclass:: StagePrivacyLevel
    :members:

.. autoclass:: NSFWLevel
    :members:

.. autoclass:: ScheduledEventEntityType
    :members:

.. autoclass:: ScheduledEventPrivacyLevel
    :members:

.. autoclass:: ScheduledEventStatus
    :members:

.. autoclass:: AutoModerationEventType
    :members:

.. autoclass:: AutoModerationTriggerType
    :members:

.. autoclass:: KeywordPresetType
    :members:

.. autoclass:: AutoModerationActionType
    :members:

.. autoclass:: SortOrderType
    :members:

.. autoclass:: RoleConnectionMetadataType
    :members:
    :undoc-members:

.. autoclass:: ForumLayoutType
    :members:

.. autoclass:: AuditLogAction
    :members:

Async Iterator
--------------

Some API functions return an "async iterator". An async iterator is something that is
capable of being used in an :ref:`async for statement <py:async for>`.

These async iterators can be used as follows: ::

    async for elem in channel.history():
        # do stuff with elem here

Certain utilities make working with async iterators easier, detailed below.

.. class:: AsyncIterator

    Represents the "AsyncIterator" concept. Note that no such class exists,
    it is purely abstract.

    .. container:: operations

        .. describe:: async for x in y

            Iterates over the contents of the async iterator.


    .. method:: next()
        :async:

        |coro|

        Advances the iterator by one, if possible. If no more items are found
        then this raises :exc:`NoMoreItems`.

    .. method:: get(**attrs)
        :async:

        |coro|

        Similar to :func:`utils.get` except run over the async iterator.

        Getting the last message by a user named 'Dave' or ``None``: ::

            msg = await channel.history().get(author__name='Dave')

    .. method:: find(predicate)
        :async:

        |coro|

        Similar to :func:`utils.find` except run over the async iterator.

        Unlike :func:`utils.find`\, the predicate provided can be a
        |coroutine_link|_.

        Getting the last audit log with a reason or ``None``: ::

            def predicate(event):
                return event.reason is not None

            event = await guild.audit_logs().find(predicate)

        :param predicate: The predicate to use. Could be a |coroutine_link|_.
        :return: The first element that returns ``True`` for the predicate or ``None``.

    .. method:: flatten()
        :async:

        |coro|

        Flattens the async iterator into a :class:`list` with all the elements.

        :return: A list of every element in the async iterator.
        :rtype: list

    .. method:: chunk(max_size)

        Collects items into chunks of up to a given maximum size.
        Another :class:`AsyncIterator` is returned which collects items into
        :class:`list`\s of a given size. The maximum chunk size must be a positive integer.

        .. versionadded:: 1.6

        Collecting groups of users: ::

            async for leader, *users in reaction.users().chunk(3):
                ...

        .. warning::

            The last chunk collected may not be as large as ``max_size``.

        :param max_size: The size of individual chunks.
        :rtype: :class:`AsyncIterator`

    .. method:: map(func)

        This is similar to the built-in :func:`map <py:map>` function. Another
        :class:`AsyncIterator` is returned that executes the function on
        every element it is iterating over. This function can either be a
        regular function or a |coroutine_link|_.

        Creating a content iterator: ::

            def transform(message):
                return message.content

            async for content in channel.history().map(transform):
                message_length = len(content)

        :param func: The function to call on every element. Could be a |coroutine_link|_.
        :rtype: :class:`AsyncIterator`

    .. method:: filter(predicate)

        This is similar to the built-in :func:`filter <py:filter>` function. Another
        :class:`AsyncIterator` is returned that filters over the original
        async iterator. This predicate can be a regular function or a |coroutine_link|_.

        Getting messages by non-bot accounts: ::

            def predicate(message):
                return not message.author.bot

            async for elem in channel.history().filter(predicate):
                ...

        :param predicate: The predicate to call on every element. Could be a |coroutine_link|_.
        :rtype: :class:`AsyncIterator`

.. _discord-api-audit-logs:

Audit Log Data
--------------

Working with :meth:`Guild.audit_logs` is a complicated process with a lot of machinery
involved. The library attempts to make it easy to use and friendly. To accomplish
this goal, it must make use of a couple of data classes that aid in this goal.

AuditLogEntry
~~~~~~~~~~~~~

.. attributetable:: AuditLogEntry

.. autoclass:: AuditLogEntry
    :members:

AuditLogChanges
~~~~~~~~~~~~~~~

.. attributetable:: AuditLogChanges

.. class:: AuditLogChanges

    An audit log change set.

    .. attribute:: before

        The old value. The attribute has the type of :class:`AuditLogDiff`.

        Depending on the :class:`AuditLogActionCategory` retrieved by
        :attr:`~AuditLogEntry.category`\, the data retrieved by this
        attribute differs:

        +----------------------------------------+---------------------------------------------------+
        |                Category                |                    Description                    |
        +----------------------------------------+---------------------------------------------------+
        | :attr:`~AuditLogActionCategory.create` | All attributes are set to ``None``.               |
        +----------------------------------------+---------------------------------------------------+
        | :attr:`~AuditLogActionCategory.delete` | All attributes are set the value before deletion. |
        +----------------------------------------+---------------------------------------------------+
        | :attr:`~AuditLogActionCategory.update` | All attributes are set the value before updating. |
        +----------------------------------------+---------------------------------------------------+
        | ``None``                               | No attributes are set.                            |
        +----------------------------------------+---------------------------------------------------+

    .. attribute:: after

        The new value. The attribute has the type of :class:`AuditLogDiff`.

        Depending on the :class:`AuditLogActionCategory` retrieved by
        :attr:`~AuditLogEntry.category`\, the data retrieved by this
        attribute differs:

        +----------------------------------------+--------------------------------------------------+
        |                Category                |                   Description                    |
        +----------------------------------------+--------------------------------------------------+
        | :attr:`~AuditLogActionCategory.create` | All attributes are set to the created value      |
        +----------------------------------------+--------------------------------------------------+
        | :attr:`~AuditLogActionCategory.delete` | All attributes are set to ``None``               |
        +----------------------------------------+--------------------------------------------------+
        | :attr:`~AuditLogActionCategory.update` | All attributes are set the value after updating. |
        +----------------------------------------+--------------------------------------------------+
        | ``None``                               | No attributes are set.                           |
        +----------------------------------------+--------------------------------------------------+

AuditLogDiff
~~~~~~~~~~~~

.. attributetable:: AuditLogDiff

.. class:: AuditLogDiff

    Represents an audit log "change" object. A change object has dynamic
    attributes that depend on the type of action being done. Certain actions
    map to certain attributes being set.

    Note that accessing an attribute that does not match the specified action
    will lead to an attribute error.

    To get a list of attributes that have been set, you can iterate over
    them. To see a list of all possible attributes that could be set based
    on the action being done, check the documentation for :class:`AuditLogAction`,
    otherwise check the documentation below for all attributes that are possible.

    .. container:: operations

        .. describe:: iter(diff)

            Returns an iterator over (attribute, value) tuple of this diff.

    .. attribute:: name

        A name of something.

        :type: :class:`str`

    .. attribute:: icon

        A guild's icon. See also :attr:`Guild.icon`.

        :type: :class:`Asset`

    .. attribute:: splash

        The guild's invite splash. See also :attr:`Guild.splash`.

        :type: :class:`Asset`

    .. attribute:: discovery_splash

        The guild's discovery splash. See also :attr:`Guild.discovery_splash`.

        :type: :class:`Asset`

    .. attribute:: banner

        The guild's banner. See also :attr:`Guild.banner`.

        :type: :class:`Asset`

    .. attribute:: owner

        The guild's owner. See also :attr:`Guild.owner`

        :type: Union[:class:`Member`, :class:`User`]

    .. attribute:: region

        The guild's voice region. See also :attr:`Guild.region`.

        :type: :class:`VoiceRegion`

    .. attribute:: afk_channel

        The guild's AFK channel.

        If this could not be found, then it falls back to a :class:`Object`
        with the ID being set.

        See :attr:`Guild.afk_channel`.

        :type: Union[:class:`VoiceChannel`, :class:`Object`]

    .. attribute:: system_channel

        The guild's system channel.

        If this could not be found, then it falls back to a :class:`Object`
        with the ID being set.

        See :attr:`Guild.system_channel`.

        :type: Union[:class:`TextChannel`, :class:`Object`]


    .. attribute:: rules_channel

        The guild's rules channel.

        If this could not be found then it falls back to a :class:`Object`
        with the ID being set.

        See :attr:`Guild.rules_channel`.

        :type: Union[:class:`TextChannel`, :class:`Object`]


    .. attribute:: public_updates_channel

        The guild's public updates channel.

        If this could not be found then it falls back to a :class:`Object`
        with the ID being set.

        See :attr:`Guild.public_updates_channel`.

        :type: Union[:class:`TextChannel`, :class:`Object`]

    .. attribute:: afk_timeout

        The guild's AFK timeout. See :attr:`Guild.afk_timeout`.

        :type: :class:`int`

    .. attribute:: mfa_level

        The guild's MFA level. See :attr:`Guild.mfa_level`.

        :type: :class:`int`

    .. attribute:: widget_enabled

        The guild's widget has been enabled or disabled.

        :type: :class:`bool`

    .. attribute:: widget_channel

        The widget's channel.

        If this could not be found then it falls back to a :class:`Object`
        with the ID being set.

        :type: Union[:class:`TextChannel`, :class:`Object`]

    .. attribute:: verification_level

        The guild's verification level.

        See also :attr:`Guild.verification_level`.

        :type: :class:`VerificationLevel`

    .. attribute:: default_notifications

        The guild's default notification level.

        See also :attr:`Guild.default_notifications`.

        :type: :class:`NotificationLevel`

    .. attribute:: explicit_content_filter

        The guild's content filter.

        See also :attr:`Guild.explicit_content_filter`.

        :type: :class:`ContentFilter`

    .. attribute:: default_message_notifications

        The guild's default message notification setting.

        :type: :class:`int`

    .. attribute:: vanity_url_code

        The guild's vanity URL.

        See also :meth:`Guild.vanity_invite` and :meth:`Guild.edit`.

        :type: :class:`str`

    .. attribute:: position

        The position of a :class:`Role` or :class:`abc.GuildChannel`.

        :type: :class:`int`

    .. attribute:: type

        The type of channel or sticker.

        :type: Union[:class:`ChannelType`, :class:`StickerType`]

    .. attribute:: topic

        The topic of a :class:`TextChannel` or :class:`StageChannel`.

        See also :attr:`TextChannel.topic` or :attr:`StageChannel.topic`.

        :type: :class:`str`

    .. attribute:: bitrate

        The bitrate of a :class:`VoiceChannel`.

        See also :attr:`VoiceChannel.bitrate`.

        :type: :class:`int`

    .. attribute:: overwrites

        A list of permission overwrite tuples that represents a target and a
        :class:`PermissionOverwrite` for said target.

        The first element is the object being targeted, which can either
        be a :class:`Member` or :class:`User` or :class:`Role`. If this object
        is not found then it is a :class:`Object` with an ID being filled and
        a ``type`` attribute set to either ``'role'`` or ``'member'`` to help
        decide what type of ID it is.

        :type: List[Tuple[target, :class:`PermissionOverwrite`]]

    .. attribute:: privacy_level

        The privacy level of the stage instance.

        :type: :class:`StagePrivacyLevel`

    .. attribute:: roles

        A list of roles being added or removed from a member.

        If a role is not found then it is a :class:`Object` with the ID and name being
        filled in.

        :type: List[Union[:class:`Role`, :class:`Object`]]

    .. attribute:: nick

        The nickname of a member.

        See also :attr:`Member.nick`

        :type: Optional[:class:`str`]

    .. attribute:: deaf

        Whether the member is being server deafened.

        See also :attr:`VoiceState.deaf`.

        :type: :class:`bool`

    .. attribute:: mute

        Whether the member is being server muted.

        See also :attr:`VoiceState.mute`.

        :type: :class:`bool`

    .. attribute:: permissions

        The permissions of a role.

        See also :attr:`Role.permissions`.

        :type: :class:`Permissions`

    .. attribute:: colour
                   color

        The colour of a role.

        See also :attr:`Role.colour`

        :type: :class:`Colour`

    .. attribute:: hoist

        Whether the role is being hoisted or not.

        See also :attr:`Role.hoist`

        :type: :class:`bool`

    .. attribute:: mentionable

        Whether the role is mentionable or not.

        See also :attr:`Role.mentionable`

        :type: :class:`bool`

    .. attribute:: code

        The invite's code.

        See also :attr:`Invite.code`

        :type: :class:`str`

    .. attribute:: channel

        A guild channel.

        If the channel is not found then it is a :class:`Object` with the ID
        being set. In some cases the channel name is also set.

        :type: Union[:class:`abc.GuildChannel`, :class:`Object`]

    .. attribute:: inviter

        The user who created the invite.

        See also :attr:`Invite.inviter`.

        :type: Optional[:class:`User`]

    .. attribute:: max_uses

        The invite's max uses.

        See also :attr:`Invite.max_uses`.

        :type: :class:`int`

    .. attribute:: uses

        The invite's current uses.

        See also :attr:`Invite.uses`.

        :type: :class:`int`

    .. attribute:: max_age

        The invite's max age in seconds.

        See also :attr:`Invite.max_age`.

        :type: :class:`int`

    .. attribute:: temporary

        If the invite is a temporary invite.

        See also :attr:`Invite.temporary`.

        :type: :class:`bool`

    .. attribute:: allow
                   deny

        The permissions being allowed or denied.

        :type: :class:`Permissions`

    .. attribute:: id

        The ID of the object being changed.

        :type: :class:`int`

    .. attribute:: avatar

        The avatar of a member.

        See also :attr:`User.avatar`.

        :type: :class:`Asset`

    .. attribute:: slowmode_delay

        The number of seconds members have to wait before
        sending another message in the channel.

        See also :attr:`TextChannel.slowmode_delay`.

        :type: :class:`int`

    .. attribute:: rtc_region

        The region for the voice channel’s voice communication.
        A value of ``None`` indicates automatic voice region detection.

        See also :attr:`VoiceChannel.rtc_region`.

        :type: :class:`VoiceRegion`

    .. attribute:: video_quality_mode

        The camera video quality for the voice channel's participants.

        See also :attr:`VoiceChannel.video_quality_mode`.

        :type: :class:`VideoQualityMode`

    .. attribute:: format_type

        The format type of a sticker being changed.

        See also :attr:`GuildSticker.format`

        :type: :class:`StickerFormatType`

    .. attribute:: emoji

        The name of the emoji that represents a sticker being changed.

        See also :attr:`GuildSticker.emoji`

        :type: :class:`str`

    .. attribute:: description

        The description of a sticker being changed.

        See also :attr:`GuildSticker.description`

        :type: :class:`str`

    .. attribute:: available

        The availability of a sticker being changed.

        See also :attr:`GuildSticker.available`

        :type: :class:`bool`

    .. attribute:: archived

        The thread is now archived.

        :type: :class:`bool`

    .. attribute:: locked

        The thread is being locked or unlocked.

        :type: :class:`bool`

    .. attribute:: auto_archive_duration

        The thread's auto archive duration being changed.

        See also :attr:`Thread.auto_archive_duration`

        :type: :class:`int`

    .. attribute:: default_auto_archive_duration

        The default auto archive duration for newly created threads being changed.

        :type: :class:`int`

    .. attribute:: enabled

        Whether something was enabled or disabled.

        :type: :class:`bool`

    .. attribute:: trigger_type

        The trigger type of an auto moderation rule being changed.

        :type: :class:`AutoModerationTriggerType`

    .. attribute:: event_type

        The event type of an auto moderation rule being changed.

        :type: :class:`AutoModerationEventType`

    .. attribute:: actions

        The list of actions being changed.

        :type: List[:class:`AutoModerationAction`]

    .. attribute:: trigger_metadata

        The trigger metadata of an auto moderation rule being changed.

        :type: :class:`AutoModTriggerMetadata`

    .. attribute:: exempt_roles

        The list of roles that are exempt from an auto moderation rule being changed.

        If a role is not found then it is an :class:`Object` with the ID set.

        :type: List[Union[:class:`Role`, :class:`Object`]]

    .. attribute:: exempt_channels

        The list of channels that are exempt from an auto moderation rule being changed.

        If a channel is not found then it is an :class:`Object` with the ID set.

        :type: List[Union[:class:`abc.GuildChannel`, :class:`Object`]]

.. this is currently missing the following keys: reason and application_id
   I'm not sure how to about porting these

Webhook Support
---------------

nextcord offers support for creating, editing, and executing webhooks through the :class:`Webhook` class.

Webhook
~~~~~~~

.. attributetable:: Webhook

.. autoclass:: Webhook()
    :members:
    :inherited-members:

WebhookMessage
~~~~~~~~~~~~~~

.. attributetable:: WebhookMessage

.. autoclass:: WebhookMessage()
    :members:

SyncWebhook
~~~~~~~~~~~

.. attributetable:: SyncWebhook

.. autoclass:: SyncWebhook()
    :members:
    :inherited-members:

SyncWebhookMessage
~~~~~~~~~~~~~~~~~~

.. attributetable:: SyncWebhookMessage

.. autoclass:: SyncWebhookMessage()
    :members:

.. _discord_api_abcs:

Abstract Base Classes
---------------------

An :term:`abstract base class` (also known as an ``abc``) is a class that models can inherit
to get their behaviour. **Abstract base classes should not be instantiated**.
They are mainly there for usage with :func:`isinstance` and :func:`issubclass`\.

This library has a module related to abstract base classes, in which all the ABCs are subclasses of
:class:`typing.Protocol`.

Snowflake
~~~~~~~~~

.. attributetable:: nextcord.abc.Snowflake

.. autoclass:: nextcord.abc.Snowflake()
    :members:

User
~~~~

.. attributetable:: nextcord.abc.User

.. autoclass:: nextcord.abc.User()
    :members:

PrivateChannel
~~~~~~~~~~~~~~

.. attributetable:: nextcord.abc.PrivateChannel

.. autoclass:: nextcord.abc.PrivateChannel()
    :members:

GuildChannel
~~~~~~~~~~~~

.. attributetable:: nextcord.abc.GuildChannel

.. autoclass:: nextcord.abc.GuildChannel()
    :members:

Messageable
~~~~~~~~~~~

.. attributetable:: nextcord.abc.Messageable

.. autoclass:: nextcord.abc.Messageable()
    :members:
    :exclude-members: history, typing

    .. automethod:: nextcord.abc.Messageable.history
        :async-for:

    .. automethod:: nextcord.abc.Messageable.typing
        :async-with:

Connectable
~~~~~~~~~~~

.. attributetable:: nextcord.abc.Connectable

.. autoclass:: nextcord.abc.Connectable()

.. _discord_api_models:

Discord Models
--------------

Models are classes that are received from Discord and are not meant to be created by
the user of the library.

.. danger::

    The classes listed below are **not intended to be created by users** and are also
    **read-only**.

    For example, this means that you should not make your own :class:`User` instances
    nor should you modify the :class:`User` instance yourself.

    If you want to get one of these model classes instances they'd have to be through
    the cache, and a common way of doing so is through the :func:`utils.find` function
    or attributes of model classes that you receive from the events specified in the
    :ref:`discord-api-events`.

.. note::

    Nearly all classes here have :ref:`py:slots` defined which means that it is
    impossible to have dynamic attributes to the data classes.


ClientUser
~~~~~~~~~~

.. attributetable:: ClientUser

.. autoclass:: ClientUser()
    :members:
    :inherited-members:

User
~~~~

.. attributetable:: User

.. autoclass:: User()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

Attachment
~~~~~~~~~~

.. attributetable:: Attachment

.. autoclass:: Attachment()
    :members:

Asset
~~~~~

.. attributetable:: Asset

.. autoclass:: Asset()
    :members:
    :inherited-members:

Message
~~~~~~~

.. attributetable:: Message

.. autoclass:: Message()
    :members:


DeletedReferencedMessage
~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: DeletedReferencedMessage

.. autoclass:: DeletedReferencedMessage()
    :members:


Reaction
~~~~~~~~

.. attributetable:: Reaction

.. autoclass:: Reaction()
    :members:
    :exclude-members: users

    .. automethod:: users
        :async-for:

Guild
~~~~~

.. attributetable:: Guild

.. autoclass:: Guild()
    :members:
    :exclude-members: fetch_members, audit_logs

    .. automethod:: fetch_members
        :async-for:

    .. automethod:: audit_logs
        :async-for:

.. class:: BanEntry

    A namedtuple which represents a ban returned from :meth:`~Guild.bans`.

    .. attribute:: reason

        The reason this user was banned.

        :type: Optional[:class:`str`]
    .. attribute:: user

        The :class:`User` that was banned.

        :type: :class:`User`

GuildPreview
~~~~~~~~~~~~

.. autoclass:: GuildPreview()
    :members:

Integration
~~~~~~~~~~~

.. autoclass:: Integration()
    :members:

.. autoclass:: IntegrationAccount()
    :members:

.. autoclass:: BotIntegration()
    :members:

.. autoclass:: IntegrationApplication()
    :members:

.. autoclass:: StreamIntegration()
    :members:

Interaction
~~~~~~~~~~~

.. attributetable:: Interaction

.. autoclass:: Interaction()
    :members:

InteractionResponse
~~~~~~~~~~~~~~~~~~~

.. attributetable:: InteractionResponse

.. autoclass:: InteractionResponse()
    :members:

InteractionMessage
~~~~~~~~~~~~~~~~~~

.. attributetable:: InteractionMessage

.. autoclass:: InteractionMessage()
    :members:
    :inherited-members:

PartialInteractionMessage
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialInteractionMessage

.. autoclass:: PartialInteractionMessage()
    :members:
    :inherited-members:

MessageInteraction
~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageInteraction

.. autoclass:: MessageInteraction()
    :members:

Member
~~~~~~

.. attributetable:: Member

.. autoclass:: Member()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

Spotify
~~~~~~~

.. attributetable:: Spotify

.. autoclass:: Spotify()
    :members:

VoiceState
~~~~~~~~~~

.. attributetable:: VoiceState

.. autoclass:: VoiceState()
    :members:

Emoji
~~~~~

.. attributetable:: Emoji

.. autoclass:: Emoji()
    :members:
    :inherited-members:

PartialEmoji
~~~~~~~~~~~~

.. attributetable:: PartialEmoji

.. autoclass:: PartialEmoji()
    :members:
    :inherited-members:

Role
~~~~

.. attributetable:: Role

.. autoclass:: Role()
    :members:

RoleTags
~~~~~~~~

.. attributetable:: RoleTags

.. autoclass:: RoleTags()
    :members:

PartialMessageable
~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialMessageable

.. autoclass:: PartialMessageable()
    :members:
    :inherited-members:

TextChannel
~~~~~~~~~~~

.. attributetable:: TextChannel

.. autoclass:: TextChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

Thread
~~~~~~

.. attributetable:: Thread

.. autoclass:: Thread()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

ThreadMember
~~~~~~~~~~~~

.. attributetable:: ThreadMember

.. autoclass:: ThreadMember()
    :members:

VoiceChannel
~~~~~~~~~~~~

.. attributetable:: VoiceChannel

.. autoclass:: VoiceChannel()
    :members:
    :inherited-members:

StageChannel
~~~~~~~~~~~~

.. attributetable:: StageChannel

.. autoclass:: StageChannel()
    :members:
    :inherited-members:


StageInstance
~~~~~~~~~~~~~

.. attributetable:: StageInstance

.. autoclass:: StageInstance()
    :members:

CategoryChannel
~~~~~~~~~~~~~~~

.. attributetable:: CategoryChannel

.. autoclass:: CategoryChannel()
    :members:
    :inherited-members:

DMChannel
~~~~~~~~~

.. attributetable:: DMChannel

.. autoclass:: DMChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

GroupChannel
~~~~~~~~~~~~

.. attributetable:: GroupChannel

.. autoclass:: GroupChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

ForumChannel
~~~~~~~~~~~~

.. attributetable:: ForumChannel

.. autoclass:: ForumChannel()
    :members:
    :inherited-members:

PartialInviteGuild
~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialInviteGuild

.. autoclass:: PartialInviteGuild()
    :members:

PartialInviteChannel
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialInviteChannel

.. autoclass:: PartialInviteChannel()
    :members:

Invite
~~~~~~

.. attributetable:: Invite

.. autoclass:: Invite()
    :members:

Template
~~~~~~~~

.. attributetable:: Template

.. autoclass:: Template()
    :members:

WidgetChannel
~~~~~~~~~~~~~

.. attributetable:: WidgetChannel

.. autoclass:: WidgetChannel()
    :members:

WidgetMember
~~~~~~~~~~~~

.. attributetable:: WidgetMember

.. autoclass:: WidgetMember()
    :members:
    :inherited-members:

Widget
~~~~~~

.. attributetable:: Widget

.. autoclass:: Widget()
    :members:

StickerPack
~~~~~~~~~~~

.. attributetable:: StickerPack

.. autoclass:: StickerPack()
    :members:

StickerItem
~~~~~~~~~~~

.. attributetable:: StickerItem

.. autoclass:: StickerItem()
    :members:

Sticker
~~~~~~~

.. attributetable:: Sticker

.. autoclass:: Sticker()
    :members:

StandardSticker
~~~~~~~~~~~~~~~

.. attributetable:: StandardSticker

.. autoclass:: StandardSticker()
    :members:

GuildSticker
~~~~~~~~~~~~

.. attributetable:: GuildSticker

.. autoclass:: GuildSticker()
    :members:

RawTypingEvent
~~~~~~~~~~~~~~

.. attributetable:: RawTypingEvent

.. autoclass:: RawTypingEvent()
    :members:

RawMessageDeleteEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawMessageDeleteEvent

.. autoclass:: RawMessageDeleteEvent()
    :members:

RawBulkMessageDeleteEvent
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawBulkMessageDeleteEvent

.. autoclass:: RawBulkMessageDeleteEvent()
    :members:

RawMessageUpdateEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawMessageUpdateEvent

.. autoclass:: RawMessageUpdateEvent()
    :members:

RawReactionActionEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawReactionActionEvent

.. autoclass:: RawReactionActionEvent()
    :members:

RawReactionClearEvent
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawReactionClearEvent

.. autoclass:: RawReactionClearEvent()
    :members:

RawReactionClearEmojiEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawReactionClearEmojiEvent

.. autoclass:: RawReactionClearEmojiEvent()
    :members:

RawIntegrationDeleteEvent
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawIntegrationDeleteEvent

.. autoclass:: RawIntegrationDeleteEvent()
    :members:

PartialWebhookGuild
~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialWebhookGuild

.. autoclass:: PartialWebhookGuild()
    :members:

PartialWebhookChannel
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialWebhookChannel

.. autoclass:: PartialWebhookChannel()
    :members:

ScheduledEvent
~~~~~~~~~~~~~~

.. attributetable:: ScheduledEvent

.. autoclass:: ScheduledEvent()
    :members:

.. attributetable:: ScheduledEventUser

.. autoclass:: ScheduledEventUser()
    :members:

.. autoclass:: EntityMetadata

AutoModerationRule
~~~~~~~~~~~~~~~~~~

.. attributetable:: AutoModerationRule

.. autoclass:: AutoModerationRule()
    :members:

AutoModerationActionExecution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: AutoModerationActionExecution

.. autoclass:: AutoModerationActionExecution()
    :members:

.. _discord_api_data:

Data Classes
------------

Some classes are just there to be data containers, this lists them.

Unlike :ref:`models <discord_api_models>` you are allowed to create
most of these yourself, even if they can also be used to hold attributes.

Nearly all classes here have :ref:`py:slots` defined which means that it is
impossible to have dynamic attributes to the data classes.

The only exception to this rule is :class:`Object`, which is made with
dynamic attributes in mind.


Object
~~~~~~

.. attributetable:: Object

.. autoclass:: Object
    :members:

Embed
~~~~~

.. attributetable:: Embed

.. autoclass:: Embed
    :members:

AllowedMentions
~~~~~~~~~~~~~~~

.. attributetable:: AllowedMentions

.. autoclass:: AllowedMentions
    :members:

MessageReference
~~~~~~~~~~~~~~~~

.. attributetable:: MessageReference

.. autoclass:: MessageReference
    :members:

PartialMessage
~~~~~~~~~~~~~~

.. attributetable:: PartialMessage

.. autoclass:: PartialMessage
    :members:

SelectOption
~~~~~~~~~~~~

.. attributetable:: SelectOption

.. autoclass:: SelectOption
    :members:

Intents
~~~~~~~

.. attributetable:: Intents

.. autoclass:: Intents
    :members:

MemberCacheFlags
~~~~~~~~~~~~~~~~

.. attributetable:: MemberCacheFlags

.. autoclass:: MemberCacheFlags
    :members:

ApplicationFlags
~~~~~~~~~~~~~~~~

.. attributetable:: ApplicationFlags

.. autoclass:: ApplicationFlags
    :members:

RoleFlags
~~~~~~~~~

.. attributetable:: RoleFlags

.. autoclass:: RoleFlags
    :members:

File
~~~~

.. attributetable:: File

.. autoclass:: File
    :members:

Colour
~~~~~~

.. attributetable:: Colour

.. autoclass:: Colour
    :members:

BaseActivity
~~~~~~~~~~~~

.. attributetable:: BaseActivity

.. autoclass:: BaseActivity
    :members:

Activity
~~~~~~~~

.. attributetable:: Activity

.. autoclass:: Activity
    :members:

Game
~~~~

.. attributetable:: Game

.. autoclass:: Game
    :members:

Streaming
~~~~~~~~~

.. attributetable:: Streaming

.. autoclass:: Streaming
    :members:

CustomActivity
~~~~~~~~~~~~~~

.. attributetable:: CustomActivity

.. autoclass:: CustomActivity
    :members:

Permissions
~~~~~~~~~~~

.. attributetable:: Permissions

.. autoclass:: Permissions
    :members:

PermissionOverwrite
~~~~~~~~~~~~~~~~~~~

.. attributetable:: PermissionOverwrite

.. autoclass:: PermissionOverwrite
    :members:

ShardInfo
~~~~~~~~~

.. attributetable:: ShardInfo

.. autoclass:: ShardInfo()
    :members:

SystemChannelFlags
~~~~~~~~~~~~~~~~~~

.. attributetable:: SystemChannelFlags

.. autoclass:: SystemChannelFlags()
    :members:

MessageFlags
~~~~~~~~~~~~

.. attributetable:: MessageFlags

.. autoclass:: MessageFlags()
    :members:

PublicUserFlags
~~~~~~~~~~~~~~~

.. attributetable:: PublicUserFlags

.. autoclass:: PublicUserFlags()
    :members:

MemberFlags
~~~~~~~~~~~

.. attributetable:: MemberFlags

.. autoclass:: MemberFlags()
    :members:

ChannelFlags
~~~~~~~~~~~~

.. attributetable:: ChannelFlags

.. autoclass:: ChannelFlags()
    :members:

AutoModerationTriggerMetadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: AutoModerationTriggerMetadata

.. autoclass:: AutoModerationTriggerMetadata
    :members:

AutoModerationActionMetadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: AutoModerationActionMetadata

.. autoclass:: AutoModerationActionMetadata
    :members:

AutoModerationAction
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: AutoModerationAction

.. autoclass:: AutoModerationAction
    :members:

ForumTag
~~~~~~~~

.. attributetable:: ForumTag

.. autoclass:: ForumTag
    :members:

RoleConnectionMetadata
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RoleConnectionMetadata

.. autoclass:: RoleConnectionMetadata
    :members:


.. _discord_ui_kit:

Bot UI Kit
----------

The library has helpers to help create component-based UIs.

View
~~~~

.. attributetable:: nextcord.ui.View

.. autoclass:: nextcord.ui.View
    :members:

Modal
~~~~~

.. attributetable:: nextcord.ui.Modal

.. autoclass:: nextcord.ui.Modal
    :members:

Item
~~~~

.. attributetable:: nextcord.ui.Item

.. autoclass:: nextcord.ui.Item
    :members:

Button
~~~~~~

.. attributetable:: nextcord.ui.Button

.. autoclass:: nextcord.ui.Button
    :members:
    :inherited-members:

.. autofunction:: nextcord.ui.button

TextInput
~~~~~~~~~

.. attributetable:: nextcord.ui.TextInput

.. autoclass:: nextcord.ui.TextInput
    :members:
    :inherited-members:

StringSelect
~~~~~~~~~~~~

.. attributetable:: nextcord.ui.StringSelect

.. autoclass:: nextcord.ui.StringSelect
    :members:
    :inherited-members:

.. autofunction:: nextcord.ui.string_select

.. autoclass:: nextcord.ui.Select

.. autofunction:: nextcord.ui.select

UserSelect
~~~~~~~~~~

.. attributetable:: nextcord.ui.UserSelect

.. autoclass:: nextcord.ui.UserSelect
    :members:
    :inherited-members:

.. autofunction:: nextcord.ui.user_select

.. autoclass:: nextcord.ui.UserSelectValues
    :members:

RoleSelect
~~~~~~~~~~

.. attributetable:: nextcord.ui.RoleSelect

.. autoclass:: nextcord.ui.RoleSelect
    :members:
    :inherited-members:

.. autofunction:: nextcord.ui.role_select

.. autoclass:: nextcord.ui.RoleSelectValues
    :members:

MentionableSelect
~~~~~~~~~~~~~~~~~

.. attributetable:: nextcord.ui.MentionableSelect

.. autoclass:: nextcord.ui.MentionableSelect
    :members:
    :inherited-members:

.. autofunction:: nextcord.ui.mentionable_select

.. autoclass:: nextcord.ui.MentionableSelectValues
    :members:

ChannelSelect
~~~~~~~~~~~~~

.. attributetable:: nextcord.ui.ChannelSelect

.. autoclass:: nextcord.ui.ChannelSelect
    :members:
    :inherited-members:

.. autofunction:: nextcord.ui.channel_select

.. autoclass:: nextcord.ui.ChannelSelectValues
    :members:

Application Commands
--------------------

The library has helpers to easily create and manipulate application commands.

Base Commands
~~~~~~~~~~~~~

.. attributetable:: BaseApplicationCommand

.. autoclass:: BaseApplicationCommand
    :members:
    :inherited-members:

.. attributetable:: BaseCommandOption

.. autoclass:: BaseCommandOption
    :members:

Slash Commands
~~~~~~~~~~~~~~

.. attributetable:: SlashApplicationCommand

.. autoclass:: SlashApplicationCommand
    :members:
    :inherited-members:

.. attributetable:: SlashApplicationSubcommand

.. autoclass:: SlashApplicationSubcommand
    :members:
    :inherited-members:

Slash Options
~~~~~~~~~~~~~

.. list-table:: Accepted Default Option Types/Annotations
    :widths: 25 25 50
    :header-rows: 1

    * - Typehint
      - Discord Type
      - Notes
    * - <blank>
      - String
      - When no typehint is given, it defaults to string.
    * - :class:`str`
      - String
      -
    * - :class:`int`
      - Integer
      - Any integer between -2^53 and 2^53
    * - :class:`float`
      - Number
      - Any double between -2^53 and 2^53
    * - :class:`bool`
      - Boolean
      -
    * - :class:`User`
      - User
      -
    * - :class:`Member`
      - User
      - Identical to typehinting with :class:`User`
    * - :class:`abc.GuildChannel`
      - Channel
      - Includes all channel types + categories. Use :class:`SlashOption` to configure which channel types to allow.
    * - :class:`CategoryChannel`
      - Channel
      - Restricts the accepted channel types to Guild Category channels.
    * - :class:`DMChannel`
      - Channel
      - Restricts the accepted channel types to DM channels.
    * - :class:`ForumChannel`
      - Channel
      - Restricts the accepted channel types to Forum Channels.
    * - :class:`GroupChannel`
      - Channel
      - Restricts the accepted channel types to Group DM channels.
    * - :class:`StageChannel`
      - Channel
      - Restricts the accepted channel types to Stage Voice channels.
    * - :class:`TextChannel`
      - Channel
      - Restricts the accepted channel types to Text and News channels.
    * - :class:`VoiceChannel`
      - Channel
      - Restricts the accepted channel types to Voice channels.
    * - :class:`Thread`
      - Channel
      - Restricts the accepted "channel" types to News, Public, and Private threads.
    * - :class:`Role`
      - Role
      -
    * - :class:`Mentionable`
      - Mentionable
      - Includes Users and Roles.
    * - :class:`Attachment`
      - Attachment
      -

.. list-table:: Advanced Annotations
    :widths: 25 75
    :header-rows: 1

    * - Typing Annotation
      - Notes
    * - :data:`~typing.Optional` [<type>]
      - Makes the slash option not required with the type of the given <type>.
    * - :data:`~typing.Literal` [<choice1>, <choice2>, ...]
      - Makes the slash option into a choice of the given type. All choices have to be the same data type.
    * - :data:`~typing.Union` [<type1>, <type2>, ...]
      - Allows compatible annotations to be typehinted together. Channel types in a union will allow the slash option
        to be any of them.
    * - :data:`~typing.Annotated` [<type1>, <type2>, ..., <typeN>]
      - Makes your IDE see <type1> as the expected type, but Nextcord will attempt to use <typeN> as the option type.
        If <typeN> isn't a valid option type, Nextcord will work backwards towards <type2> until it finds a type that
        can be used as a valid option type.
    * - :class:`Range` [[type1 | ``...``], <type2 | ``...``>]
      - Makes a range of values set in :attr:`SlashOption.min_value` and :attr:`SlashOption.max_value`.
        If ``type1`` is not set or is an ellipsis, ``min_value`` is ``None``.
        If ``type2`` is an ellipsis (``...``), ``max_value`` is ``None``.
    * - :class:`String` [[type1 | ``...``], <type2 | ``...``>]
      - Makes a range of string length set in :attr:`SlashOption.min_length` and :attr:`SlashOption.max_length`.
        If ``type1`` is not set or is an ellipsis, ``min_length`` is ``None``.
        If ``type2`` is an ellipsis (``...``), ``max_length`` is ``None``.

.. attributetable:: SlashOption

.. autoclass:: SlashOption
    :members:
    :inherited-members:
    :exclude-members: verify

.. attributetable:: SlashCommandOption

.. autoclass:: SlashCommandOption
    :members:
    :inherited-members:
    :exclude-members: option_types

.. autoclass:: Range()

.. autoclass:: String()

User Commands
~~~~~~~~~~~~~

.. attributetable:: UserApplicationCommand

.. autoclass:: UserApplicationCommand
    :members:
    :inherited-members:

Message Commands
~~~~~~~~~~~~~~~~

.. attributetable:: MessageApplicationCommand

.. autoclass:: MessageApplicationCommand
    :members:
    :inherited-members:

Command Helpers
~~~~~~~~~~~~~~~

.. attributetable:: CallbackWrapper

.. autoclass:: CallbackWrapper
    :members:

.. attributetable:: OptionConverter

.. autoclass:: OptionConverter
    :members:

.. attributetable:: Mentionable

.. autoclass:: Mentionable
    :members:

Decorators
~~~~~~~~~~

.. autoclass:: message_command

.. autoclass:: slash_command

.. autoclass:: user_command

Cogs
~~~~

.. autoclass:: ClientCog
    :members:

Warnings
--------

.. autoclass:: MissingApplicationCommandParametersWarning


Exceptions
----------

The following exceptions are thrown by the library.

.. autoexception:: DiscordException

.. autoexception:: ClientException

.. autoexception:: LoginFailure

.. autoexception:: NoMoreItems

.. autoexception:: HTTPException
    :members:

.. autoexception:: Forbidden

.. autoexception:: NotFound

.. autoexception:: DiscordServerError

.. autoexception:: InvalidData

.. autoexception:: InvalidArgument

.. autoexception:: GatewayNotFound

.. autoexception:: ConnectionClosed

.. autoexception:: PrivilegedIntentsRequired

.. autoexception:: InteractionResponded

.. autoexception:: nextcord.opus.OpusError

.. autoexception:: nextcord.opus.OpusNotLoaded

.. autoexception:: HTTPInternalCancelled

.. autoexception:: HTTPInternalRatelimitLocked

.. autoexception:: ApplicationError

.. autoexception:: ApplicationInvokeError

.. autoexception:: ApplicationCheckFailure

.. autoexception:: ApplicationCommandOptionMissing

Exception Hierarchy
~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`Exception`
        - :exc:`DiscordException`
            - :exc:`ClientException`
                - :exc:`InvaildCommandType`
                - :exc:`InvalidData`
                - :exc:`InvalidArgument`
                - :exc:`LoginFailure`
                - :exc:`ConnectionClosed`
                - :exc:`PrivilegedIntentsRequired`
                - :exc:`InteractionResponded`
            - :exc:`NoMoreItems`
            - :exc:`GatewayNotFound`
            - :exc:`HTTPException`
                - :exc:`Unauthorized`
                - :exc:`Forbidden`
                - :exc:`NotFound`
                - :exc:`DiscordServerError`
            - :exc:`HTTPInternalCancelled`
                - :exc:`HTTPInternalRatelimitLocked`
        - :exc:`ApplicationError`
            - :exc:`ApplicationInvokeError`
            - :exc:`ApplicationCheckFailure`
            - :exc:`ApplicationCommandOptionMissing`
