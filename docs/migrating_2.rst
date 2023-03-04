.. currentmodule:: nextcord

.. _migrating_2_0:

Migrating to v2.0
=================

Changing to v2.0 represents different breaking changes we needed to make. We did not only needed to fork the
original discord.py repository but adapt changes in the Discord API in order of supporting its latest features,
to work with threads, buttons and commands.

Overview
--------

- Methods and attributes that returned :class:`TextChannel`, etc can now return :class:`Thread`.
- Python 3.8 or newer is required.
- Attributes that returned :class:`Asset` are renamed, e.g. attributes ending with ``_url`` (i.e. ``avatar_url``) are changed to :Attr:`avatar.url`. :attr:`User.avatar` returns None in case the default avatar is used.
- :func:`on_presence_update` replaces :func:`on_member_update` for updates to :attr:`Member.status` and :attr:`Member.activities`.
- datetime is now timezone-aware.
- Sticker changes: ``StickerType`` has been renamed to :class:`StickerFormatType`, and the type of :attr:`Message.stickers` is changed. ``Sticker.preview_image``, ``Sticker.image`` and ``Sticker.tags`` are removed.
- Webhooks are changed significantly: ``WebhookAdapter`` is removed, and synchronous requests using requests is now inside :class:`SyncWebhook`.
- edit method no longer updates cache and instead returns modified instance.
- User accounts (userbots) are no longer supported.
- Client.logout is removed; use :meth:`Client.close` instead.
- ``on_private_channel_create/delete`` events are removed.
- User.permissions_in is removed; use :meth:`abc.GuildChannel.permissions_in` instead.
- :attr:`Message.type` for replies are now :attr:`MessageType.reply`.
- ``Reaction.custom_emoji`` property is changed to :attr:`Reaction.is_custom_emoji` method.
- ``missing_perms`` attributes and arguments are renamed to ``missing_permissions``.
- Many method arguments now reject ``None``.
- Many arguments are now specified as positional-only or keyword-only; e.g. :func:`oauth_url` now takes keyword-only arguments, and methods starting with ``get_`` or ``fetch_`` take positional-only arguments.
- You must explicitly enable the :attr:`~Intents.message_content` intent to receive message :attr:`~Message.content`, :attr:`~Message.embeds`, :attr:`~Message.attachments`, and :attr:`~Message.components` in most messages.
- :meth:`Guild.bans` is no longer a coroutine and returns an :class:`~nextcord.AsyncIterator` instead of a :class:`list`.
- ``StoreChannel`` is removed as it is deprecated by Discord, see `here <https://support.discord.com/hc/en-us/articles/4688647258007-Self-serve-Game-Selling-Deprecation>`__ for more info.
- ``ChannelType.store`` is removed.
- ``AppInfo.summary``, ``AppInfo.guild_id``, ``AppInfo.primary_sku_id`` and ``AppInfo.slug`` are removed.
- ``PartialAppInfo.summary`` is removed.
- :meth:`abc.Messageable.pins` has been extracted out from :class:`abc.Messageable` and moved to :class:`PinsMixin`
- :class:`VoiceChannel` now inherits from :class:`Messageable`

Changes
-------

Webhook changes
^^^^^^^^^^^^^^^
:class:`Webhook` was overhauled.

:class:`Webhook` and :class:`WebhookMessage` are now always asynchronous. For synchronous use (requests), use :class:`SyncWebhook` and :class:`SyncWebhookMessage`.
``WebhookAdapter``, ``AsyncWebhookAdapter``, and ``RequestsWebhookAdapter`` are removed, since they are unnecessary.
adapter arguments of :meth:`Webhook.partial` and :meth:`Webhook.from_url` are removed. Sessions are now passed directly to partial/from_url.

.. code-block:: python3

    webhook = nextcord.SyncWebhook.from_url(
            f"https://discord.com/api/webhooks/{id}/{token}"
        )
    webhook.send("Hello from nextcord!")
    async with aiohttp.ClientSession() as session:
        webhook = nextcord.Webhook.partial(
                id,
                token,
                session=session
            )
        await webhook.send("Hello from nextcord!")


Asset changes
^^^^^^^^^^^^^
Assets have been changed.

- Asset-related attributes that previously returned hash strings (e.g. :attr:`User.avatar`) now returns :class:`Asset`. :attr:`Asset.key` returns the hash from now on.
- ``Class.x_url`` and ``Class.x_url_as`` are removed. :meth:`Asset.replace` or :meth:`Asset.with_x` methods can be used to get specific asset sizes or types.
- :Attr:`Emoji.url` and :Attr:`PartialEmoji.url` are now :class:`str`. :meth:`Emoji.save` and :meth:`Emoji.read` are added to save or read emojis.
- ``Emoji.url_as`` and ``PartialEmoji.url_as`` are removed.
- Some :class:`AuditLogDiff` attributes now return :class:`Asset` instead of :class:`str`: ``splash``, ``icon``, ``avatar```
- :attr:`User.avatar` returns ``None`` if the avatar is not set and is instead the default avatar; use :attr:`User.display_avatar` for pre-2.0 behavior.

.. code-block:: python3

    avatar_url = user.display_avatar.url # previously str(avatar_url)
    avatar_128x128_url = user.display_avatar.with_size(128).url # previously str(avatar_url_as(size=128))
    avatar_128x128_png_url = user.display_avatar.replace(size=128, static_format="png").url
    # previously str(avatar_url_as(size=128, static_format="png"))
    # The code above can also be written as:
    avatar_128x128_png_url = user.display_avatar.with_size(128).with_static_format("png").url

    avatar_bytes = await user.display_avatar.read() # previously avatar_url.read

    # Emoji and Sticker are special case:
    emoji_url = emoji.url # previously str(emoji.url)
    emoji_32x32_url = emoji.with_size(32).url # previously str(emoji.url_as(size=32))
    emoji_32x32_png_url = emoji.replace(size=32, static_format="png").url
    # previously str(url_as(size=128, static_format="png"))

    emoji_bytes = await emoji.read() # previously emoji.url.read
    # Same applies to Sticker and PartialEmoji.

Python Version Change
^^^^^^^^^^^^^^^^^^^^^

In order to make development easier,
the library had to remove support for Python versions lower than 3.8,
which essentially means that **support for Python 3.7, 3.6 and 3.5
is dropped**. We recommend updating to Python version 3.9.

Use of timezone-aware time
^^^^^^^^^^^^^^^^^^^^^^^^^^
TL;DR: :func:`utils.utcnow` becomes now(:attr:`datetime.timezone.utc`). If you are constructing datetime yourself, pass ``tzinfo=datetime.timezone.utc``.

.. code-block:: python3

    embed = discord.Embed(
        title = "Pi Day 2021 in UTC",
        timestamp = datetime(2021, 3, 14, 15, 9, 2, tzinfo=timezone.utc)
    )

Note that newly-added :func:`nextcord.utils.utcnow()` can be used as an alias of ``datetime.datetime.now(datetime.timezone.utc)``.

Embed.__bool__ change
^^^^^^^^^^^^^^^^^^^^^
:class:`Embed` that has a value is always considered truthy. Previously it only considered text fields.

Duplicate registration of cogs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:meth:`commands.Bot.add_cog <ext.commands.Bot.add_cog>` now raises when a cog with the same name is already registered. override argument can be used to bring back the 1.x behavior.

Message.type for replies
^^^^^^^^^^^^^^^^^^^^^^^^
:attr:`Message.type` now returns :attr:`MessageType.reply` for replies, instead of default.

Command.clean_params
^^^^^^^^^^^^^^^^^^^^
:attr:`commands.Command.clean_params <ext.commands.Command.clean_params>` is now a :class:`dict`, not :class:`collections.OrderedDict`.

DMChannel.recipient
^^^^^^^^^^^^^^^^^^^
:attr:`DMChannel.recipient` is now optional, and will return ``None`` in many cases.

permissions_for positional only argument
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:func:`abc.GuildChannel.permissions_for` method's first argument is now positional only.

Colour.blurple
^^^^^^^^^^^^^^
:meth:`Colour.blurple` is renamed to :meth:`Colour.og_blurple`, and :meth:`Colour.blurple` now returns the different color.

oauth_url taking keyword only arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:meth:`utils.oauth_url`'s ``permissions``, ``guild``, ``redirect_uri``, and ``scopes`` arguments are now keyword only.

StageChannel changes
^^^^^^^^^^^^^^^^^^^^
Due to the introduction of :class:`StageInstance` representing the current session of a :class:`StageChannel`,

:meth:`StageChannel.edit` can no longer edit topic. Use :meth:`StageInstance.edit` instead.
:meth:`StageChannel.clone` no longer clones its topic.

Message.channel
^^^^^^^^^^^^^^^
:attr:`Message.channel` can now return :class:`Thread`.

Guild methods taking positional only arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:meth:`Guild.get_channel`, :meth:`Guild.get_role`, :meth:`Guild.get_member_named`, :meth:`Guild.fetch_member`, and :meth:`Guild.fetch_emoji` methods' first arguments are now positional only.

Guild.create_text_channel topic argument
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:meth:`Guild.create_text_channel`'s ``topic`` argument no longer accepts ``None``.

Reaction.custom_emoji
^^^^^^^^^^^^^^^^^^^^^
``Reaction.custom_emoji`` is now a method called :attr:`Reaction.is_custom_emoji` for consistency.

Reaction.users arguments keyword only
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Arguments of :attr:`Reaction.users` are now keyword only.

IntegrationAccount.id
^^^^^^^^^^^^^^^^^^^^^
:attr:`IntegrationAccount.id` is now :class:`str`, instead of :class:`int`, due to Discord changes.

BadInviteArgument new required argument
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:exc:`commands.BadInviteArgument <ext.commands.BadInviteArgument>` now requires one argument, ``argument``.

missing_perms
^^^^^^^^^^^^^
``missing_perms`` arguments and attributes of :exc:`commands.MissingPermissions <ext.commands.MissingPermissions>` and :exc:`commands.BotMissingPermissions <ext.commands.BotMissingPermissions>` are renamed to ``missing_permissions``.

Guild.vanity_invite
^^^^^^^^^^^^^^^^^^^
:attr:`Guild.vanity_invite` can now return None.

abc.Messageable.fetch_message positional only
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Its first argument is now positional only.

get_partial_message positional only
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Its first argument is now positional only.

Template.edit name argument
^^^^^^^^^^^^^^^^^^^^^^^^^^^
:meth:`Template.edit`'s name argument no longer accepts ``None``.

Member.edit roles argument
^^^^^^^^^^^^^^^^^^^^^^^^^^
:meth:`Member.edit`'s roles argument no longer accepts ``None``.

CommandOnCooldown new required argument
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:exc:`commands.CommandOnCooldown <ext.commands.CommandOnCooldown>` now requires an additional argument, type.

fetch_channel
^^^^^^^^^^^^^
:meth:`Client.fetch_channel` and :meth:`Guild.fetch_channel` can now return :class:`Thread`.

on_member_update and on_presence_update separation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:func:`on_member_update` event is no longer dispatched for status/activity changes. Use :func:`on_presence_update` instead.

Message.stickers
^^^^^^^^^^^^^^^^
:attr:`Message.stickers` is now ``List[StickerItem]`` instead of ``List[Sticker].`` While :class:`StickerItem` supports some operations of previous :class:`Sticker`, ``description`` and ``pack_id`` attributes do not exist. :class:`Sticker` can be fetched via :meth:`StickerItem.fetch` method.

AuditLogDiff.type
^^^^^^^^^^^^^^^^^
:attr:`AuditLogDiff.type` is now ``Union[ChannelType, StickerType]``, instead of :class:`ChannelType`.

ChannelNotReadable.argument
^^^^^^^^^^^^^^^^^^^^^^^^^^^
:attr:`commands.ChannelNotReadable.argument <ext.commands.ChannelNotReadable.argument>` can now return :class:`Thread`.

NSFWChannelRequired.channel
^^^^^^^^^^^^^^^^^^^^^^^^^^^
:attr:`commands.NSFWChannelRequired.channel <ext.commands.NSFWChannelRequired.channel>` can now return :class:`Thread`.

Bot.add_listener and Bot.remove_listener
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:meth:`commands.Bot.add_listener <ext.commands.Bot.add_listener>` and :meth:`commands.Bot.remove_listener <ext.commands.Bot.remove_listener>`'s ``name`` arguments no longer accept ``None``.

Context attributes
^^^^^^^^^^^^^^^^^^
The following :class:`Context` attributes can now be ``None``: ``prefix``, ``command``, ``invoked_with``, ``invoked_subcommand``. Note that while the documentation change suggests potentially breaking change, the code indicates that this was always the case.

Command.help
^^^^^^^^^^^^
:attr:`commands.Command.help <ext.commands.Command.help>` can now be ``None``.

Client.get_channel
^^^^^^^^^^^^^^^^^^
:meth:`Client.get_channel` can now return :class:`Thread`.

Client methods taking positional only arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:meth:`Client.get_guild`, :meth:`Client.get_user`, and :meth:`Client.get_emoji` methods' first arguments are now positional only.

edit method behavior
^^^^^^^^^^^^^^^^^^^^
edit methods of most classes no longer update the cache in-place, and instead returns the modified object.

on_socket_raw_receive behavior
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:func:`on_socket_raw_receive` is no longer dispatched for incomplete data, and the value passed is always decompressed and decoded to :class:`str`. Previously, when received a multi-part zlib-compressed binary message, :func:`on_socket_raw_receive` was dispatched on all messages with the compressed, encoded bytes.

Guild.get_member taking positional only argument
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:meth:`Guild.get_member` method's first argument is now positional only.

Intents.message_content must be enabled to receive message content
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In order to receive message content in most messages, you must have :attr:`Intents.message_content` enabled.

You can do this by using :meth:`Intents.all` or by setting :attr:`~Intents.message_content` to ``True``:

.. code-block:: python3

    intents = nextcord.Intents.default()
    intents.message_content = True

For more information go to the :ref:`message content intent documentation <need_message_content_intent>`.

Guild.bans now returns an AsyncIterator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:meth:`Guild.bans` returns an :class:`~nextcord.AsyncIterator` instead of a :class:`list`.

.. code-block:: python3

    # before
    bans = await guild.bans()

    # now
    bans = await guild.bans().flatten()  # get a list of the first 1000 bans
    bans = await guild.bans(limit=None).flatten()  # get a list of all bans

Removals
--------

User account support
^^^^^^^^^^^^^^^^^^^^
User account ("userbot") is no longer supported. Thus, these features that were only applicable to them are removed:

- bot argument of ``Client.start/run``
- afk argument of :func:`Client.change_presence`
- Classes: ``Profile``, ``Relationship``, ``CallMessage``, ``GroupCall``
- ``RelationshipType``, ``HypeSquadHouse``, ``PremiumType``, ``UserContentFilter``, ``FriendFlags``, ``Theme``
- ``GroupChannel.add_recipients``, ``remove_recipients``, edit (NOTE: :class:`GroupChannel` itself still remains)
- ``Guild.ack``
- ``Client.fetch_user_profile``
- ``Message.call`` and ``ack``
- ``ClientUser.email``, ``premium``, ``premium_type``, ``get_relationship``, ``relationships``, ``friends``, ``blocked``, ``create_group``, ``edit_settings``
- :func:`ClientUser.edit`'s ``password``, ``new_password``, ``email``, ``house arguments``
- ``User.relationship``, ``mutual_friends``, ``is_friend``, ``is_blocked``, ``block``, ``unblock``, ``remove_friend``, ``send_friend_request``, ``profile``
- Events: ``on_relationship_add`` and ``on_relationship_update``

This means that detection of Nitro is no longer possible.

Client.logout
^^^^^^^^^^^^^
This method was an alias of :func:`Client.close`, which remains.

ExtensionNotFound.original
^^^^^^^^^^^^^^^^^^^^^^^^^^
This always returned ``None`` for compatibility.

MemberCacheFlags.online
^^^^^^^^^^^^^^^^^^^^^^^
Due to Discord changes, this cache flag is no longer available. :class:`MemberCacheFlags`'s online argument is removed for similar reasons.

Client.request_offline_members
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Deprecated since 1.5.

on_private_channel_create/delete
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
These events will no longer be dispatched due to Discord changes.

User.permissions_in, Member.permissions_in
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Use :func:`abc.GuildChannel.permissions_for` instead.

guild_subscriptions argument
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``guild_subscriptions`` argument of :class:`Client` is replaced with intents system.

fetch_offline_members argument
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This argument of :class:`Client` was an alias of chunk_guilds_at_startup since 1.5.

HelpCommand.clean_prefix
^^^^^^^^^^^^^^^^^^^^^^^^
This was moved to :attr:`commandsContext.clean_prefix`.

Sticker.preview_image
^^^^^^^^^^^^^^^^^^^^^
This was removed as Discord no longer provides the data.

self_bot argument
^^^^^^^^^^^^^^^^^
:class:`Bot`'s ``self_bot`` argument was removed, since userbots are no longer supported.

VerificationLevel attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``VerificationLevel.table_flip`` (alias of high) was removed. ``extreme``, ``very_high``, and ``double_table_flip`` attributes were removed and replaced with ``highest``.

StickerType
^^^^^^^^^^^
:class:`StickerType`, an enum of sticker formats, is renamed to :class:`StickerFormatType`. Old name is used for a new enum with different purpose (checking if the sticker is guild sticker or Nitro sticker).

Sticker.image
^^^^^^^^^^^^^
``Sticker.image`` is removed. Its URL can be accessed via :attr:`Sticker.url`, just like new :class:`Emoji`.

Sticker.tags
^^^^^^^^^^^^
Due to the introduction of :class:`GuildSticker`, ``Sticker.tags`` is removed from the parent class :class:`Sticker` and moved to :attr:`StandardSticker.tags`.

MessageType.application_command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This was renamed to :attr:`MessageType.chat_input_command` due to Discord adding context menu commands.

StoreChannel has been removed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``StoreChannel`` has been removed as it has been deprecated by Discord, see `here <https://support-dev.discord.com/hc/en-us/articles/4414590563479>`__ for more info.

Meta Change
-----------

- Performance of the library has improved significantly (all times with 1 process and 1 AutoShardedBot):

+-------------------------------+----------------------------------+----------------------------------+
|             Testsetup         |          boot up before          |            boot up now           |
+-------------------------------+----------------------------------+----------------------------------+
| 735 guilds (with chunking)    | 57s/1.7 GiB RAM                  | 42s/1.4 GiB RAM                  |
+-------------------------------+----------------------------------+----------------------------------+
| 27k guilds (with chunking)    | 477s/8 GiB RAM                   | 303s/7.2 GiB                     |
+-------------------------------+----------------------------------+----------------------------------+
| 48k guilds (without chunking) | 109s                             | 67s                              |
+-------------------------------+----------------------------------+----------------------------------+
| 106k guilds (without chunking)| 3300s                            | 3090s                            |
+-------------------------------+----------------------------------+----------------------------------+

- The public API should be completely type-hinted
- Almost all ``edit`` methods now return their updated counterpart rather than doing an in-place edit
