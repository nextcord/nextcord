:orphan:

.. _quickstart:

.. currentmodule:: nextcord

Quickstart
============

This page gives a brief introduction to the library. It assumes you have the library installed,
if you don't check the :ref:`installing` portion.

A Minimal Bot
---------------

Let's make a bot that responds to a specific message and walk you through it.

It looks something like this:

.. code-block:: python3

    import nextcord

    client = nextcord.Client()

    @client.event
    async def on_ready():
        print(f'We have logged in as {client.user}')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')

    client.run('your token here')

Let's name this file ``example_bot.py``. Make sure not to name it ``nextcord`` as that'll conflict
with the library.

A lot is going on here, so let's walk you through it step by step.

1. The first line just imports the library, if this raises a `ModuleNotFoundError` or `ImportError`
   then head on over to :ref:`installing` section to properly install.
2. Next, we create an instance of a :class:`Client`. This client is our connection to Discord.
3. We then use the :meth:`Client.event` decorator to register an event. This library has many events.
   Since this library is asynchronous, we do things in a "callback" style manner.

   A callback is essentially a function that is called when something happens. In our case,
   the :func:`on_ready` event is called when the bot has finished logging in and setting things
   up and the :func:`on_message` event is called when the bot has received a message.
4. Since the :func:`on_message` event triggers for *every* message received, we have to make
   sure that we ignore messages from ourselves. We do this by checking if the :attr:`Message.author`
   is the same as the :attr:`Client.user`.
5. Afterwards, we check if the :class:`Message.content` starts with ``'$hello'``. If it does,
   then we send a message in the channel it was used in with ``'Hello!'``. This is a basic way of 
   handling commands, which can be later automated with the :doc:`./ext/commands/index` framework as shown below.
6. Finally, we run the bot with our login token. If you need help getting your token or creating a bot,
   look in the :ref:`discord-intro` section.


Now that we've made a bot, we have to *run* the bot. Luckily, this is simple since this is just a
Python script, we can run it directly.

On Windows:

.. code-block:: shell

    $ py -3 example_bot.py

On other systems:

.. code-block:: shell

    $ python3 example_bot.py

Now you can try playing around with your basic bot.

A Minimal Bot With Commands
---------------------------

Now we have a basic bot, lets use the commands framework to add a simple command.

It looks something like this:

.. code-block:: python3

    import nextcord
    from nextcord import commands

    bot = commands.Bot(command_prefix="$")
    
    @bot.event
    async def on_ready():
        print(f'We have logged in as {bot.user}')
        
    @bot.command()
    async def hello(ctx):
        await ctx.send("Hello!")
        
    bot.run("Your token here")

There is a lot going on here, so let's take it step by step.

1. Previously we saw how to import the base, now we also need to import the commands extension
   from nextcord as this is how we will define our commands on our bot.
2. Now we need to create an instance of :class:`Bot`. This is what we will use to add
   commands onto our bot. This is also has all of the features from :class:`Client` through 
   a process called inheritence.
   
   We also pass an argument called ``command_prefix``, this lets us tell our bot
   what the prefix all commands should be called with are. In our case, all commands
   will need to be prefixed with ``$``
3. We then use the same :func:`on_ready` from our minimal bot to tell us when 
   our bot has finished logging into discord and is setup.
4. By putting `@bot.command()` before a function, we are telling our but that this is a command.
   The bot will then create a command using the name of the function, in this case ``hello``.
   
   When the bot is run, this command can be called by combining the command name and the 
   command prefix we defined in :class:`Bot`. ``$hello``, by running this the bot should respond
   with ``Hello!``
   
   If you wish to name a function differently, you can provide a name in the decorator like so.
   `@bot.command(name="name")`
5. Finally, we run the bot with our login token. This is the same as the minimal bot.

:class:`Bot` also features a built-in help command. You can view this with your prefix
following by ``help``, in our case it's ``$help``. Try it out yourself.

For more information on commands within Nextcord, refer to the following documentation.

.. toctree::
  :maxdepth: 1

  ext/commands/commands.rst


Next Steps
----------

For further examples of bots created using Nextcord, click :resource:`here <examples>`.

Otherwise, try to play around with your bot and add some new features. 

Heres some fun examples:

- Make the hello command also mention the person who ran the command
    - Hint: Look in the docs for ``.mention``
- Make your bot print/send a message when someone joins your guild.
    - Hint: You will need to setup member intents, you can find more information on that here. :doc:`intro` 
- Make your bot case insensitive 
- Make a command called ``echo``, which repeats the command input.
    - Hint: ``(ctx, *, message):`` will mean everything said will be stored in the variable `message`
