:orphan:

.. _discord-intro:

Creating a Bot Account
======================

To work with the library and the Discord API in general, we must first create a Discord Bot account.

Creating a Bot account is a pretty straightforward process.

1. Make sure you're logged on to the `Discord website <https://discord.com>`_.
2. Navigate to the `Applications page <https://discord.com/developers/applications>`_.
3. Click on the "New Application" button.

    .. image:: /images/discord_create_app_button.png
        :alt: The new application button.

4. Give the application a name and click "Create".

    .. image:: /images/discord_create_app_form.png
        :alt: The new application form filled in.

5. Create a Bot User account by navigating to the "Bot" tab and clicking "Add Bot".

    - Click "Yes, do it!" to continue.

    .. image:: /images/discord_create_bot_user.png
        :alt: The Add Bot button.
6. Make sure that **Public Bot** is ticked if you want other users to invite your bot.

    - You should also make sure that **Require OAuth2 Code Grant** is unchecked unless you
      are developing a service that needs it. If you're unsure, then **leave it unchecked**.

    .. image:: /images/discord_bot_user_options.png
        :alt: How the Bot User options should look like for most people.

7. Get a generated token using the "Reset Token" button. You will have to confirm and enter a 2FA Code. 2FA is a requirement for making Bot Accounts.

    - **This is not the Client Secret from the General Information page.**

    .. warning::

        It should be worth noting that your bot's token is essentially your bot's
        password. You should **never** share this with anyone else. In doing so,
        someone can log in to your bot and do malicious things, such as leaving
        servers, banning all members inside a server, or mentioning everyone maliciously.

        The possibilities are endless, so **do not share this token.**

        If you have accidentally leaked your token, click the "Reset Token" button as soon
        as possible. This revokes your old token and re-generates a new one.
        Now you need to use the new token to log in.

8. After that, click the "Copy" button to copy your token.

    .. image:: /images/discord_bot_copy_token.png
        :alt: The revealed token and the new "Copy" button.

And that's it. You now have a bot account and you can log in with that token.

.. _discord_invite_bot:

Inviting Your Bot
-----------------

So you've made a Bot User but it's not actually in any server.

If you want to invite your bot, you must create an invite URL for it.

1. Make sure you're logged in to the `Discord website <https://discord.com>`_.
2. Navigate to the `Application page <https://discord.com/developers/applications>`_
3. Click on your bot's page.
4. Go to the "OAuth2" tab.

    .. image:: /images/discord_oauth2.png
        :alt: How the OAuth2 page should look like.

5. Tick the "bot" checkbox under "scopes". If you make use of Application Commands (Slash, Message and User Commands), also tick the "applications.commands" scope.

    .. image:: /images/discord_oauth2_scope.png
        :alt: The scopes checkbox with "bot" and "applications.commands" ticked.

6. Tick the permissions that your bot requires to function under "Bot Permissions".

    - Please be aware of the consequences of requiring your bot to have the "Administrator" permission.

    - Bot owners must have 2FA enabled for certain actions and permissions when added in servers that have Server-Wide 2FA enabled. Check the `2FA support page <https://support.discord.com/hc/en-us/articles/219576828-Setting-up-Two-Factor-Authentication>`_ for more information.

    .. image:: /images/discord_oauth2_perms.png
        :alt: The permission checkboxes with some permissions checked.

7. Now the resulting URL can be used to add your bot to a server. Copy and paste the URL into your browser, choose a server to invite the bot to, and click "Authorize".


.. note::

    The person adding the bot needs the "Manage Server" permission to do so.

If you want to generate this URL dynamically at run-time inside your bot and using the
:class:`nextcord.Permissions` interface, you can use :func:`nextcord.utils.oauth_url`.
