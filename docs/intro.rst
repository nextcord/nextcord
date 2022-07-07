:orphan:

.. currentmodule:: nextcord

.. _intro:

Introduction
============

This is the documentation for nextcord, a library for Python to aid
in creating applications that utilise the Discord API.

Prerequisites
-------------

nextcord works with Python 3.8 or higher. Support for earlier versions of Python
is not provided. Python 2.7 or lower is not supported. Python 3.7 or lower is not supported.


.. _installing:

Installing
----------

You can get the library directly from PyPI: ::

    python3 -m pip install -U nextcord

If you are using Windows and have not installed Python to PATH, then the following should be used instead: ::

    py -3 -m pip install -U nextcord


To get voice support, you should use ``nextcord[voice]`` instead of ``nextcord``, e.g. ::

    python3 -m pip install -U nextcord[voice]

On Linux environments, installing voice requires getting the following dependencies:

- `libffi <https://github.com/libffi/libffi>`_
- `libnacl <https://github.com/saltstack/libnacl>`_
- `python3-dev <https://packages.debian.org/python3-dev>`_

For a Debian-based system, the following command will get these dependencies:

.. code-block:: shell

    $ apt install libffi-dev libnacl-dev python3-dev

Remember to check your permissions!

Virtual Environments
~~~~~~~~~~~~~~~~~~~~

Sometimes you want to keep libraries from polluting system installs or use a different version of
libraries than the ones installed on the system. You might also not have permission to install libraries system-wide.
For this purpose, the standard library as of Python 3.3 comes with a concept called "Virtual Environment"s to
help maintain these separate versions.

A more in-depth tutorial is found on :doc:`py:tutorial/venv`.

However, for the quick and dirty:

1. Go to your project's working directory:

    .. code-block:: shell

        $ cd your-bot-source
        $ python3 -m venv bot-env

2. Activate the virtual environment:

    .. code-block:: shell

        $ source bot-env/bin/activate

    On Windows you activate it with:

    .. code-block:: shell

        $ bot-env\Scripts\activate.bat

3. Use pip like usual:

    .. code-block:: shell

        $ pip install -U nextcord

Congratulations. You now have a virtual environment all set up.

Basic Concepts
--------------

nextcord revolves around the concept of :ref:`events <discord-api-events>`.
An event is something you listen to and then respond to. For example, when a message
happens, you will receive an event about it that you can respond to.

A quick example to showcase how events work:

.. code-block:: python3

    from nextcord.ext import commands

    # the prefix is not used in this example
    bot = commands.Bot(command_prefix='$')

    @bot.event
    async def on_message(message):
        print(f'Message from {message.author}: {message.content}')

    bot.run('token')
