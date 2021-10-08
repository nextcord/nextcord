.. image:: assets/repo-banner.svg
   :alt: Nextcord

.. image:: https://discord.com/api/guilds/881118111967883295/embed.png
   :target: https://discord.gg/ZebatWssCB
   :alt: Discord server invite
.. image:: https://img.shields.io/pypi/v/nextcord.svg
   :target: https://pypi.python.org/pypi/nextcord
   :alt: PyPI version info
.. image:: 	https://img.shields.io/pypi/dm/nextcord?color=informational&label=Pypi%20downloads
   :target: https://pypi.python.org/pypi/nextcord
   :alt: PyPI version info
.. image:: https://img.shields.io/pypi/pyversions/nextcord.svg
   :target: https://pypi.python.org/pypi/nextcord
   :alt: PyPI supported Python versions
.. image:: https://img.shields.io/readthedocs/nextcord
   :target: https://nextcord.readthedocs.io/en/latest
   :alt: Nextcord documentation
   
Nextcord
--------
   
A modern, easy-to-use, feature-rich, and async-ready API wrapper for Discord written in Python.

Fork notice
--------------------------

This is a fork of discord.py, which unfortunately has been `officially discontinued <https://gist.github.com/Rapptz/4a2f62751b9600a31a0d3c78100287f1/>`_ on 28th August 2021.
Nextcord will try to replace discord.py, with **continued support and features**, to still offer former discord.py users a stable API wrapper for their bots.   

Key Features
-------------

- Modern Pythonic API using ``async`` and ``await``
- Proper rate limit handling
- Optimised in both speed and memory

Installing
----------

**Python 3.8 or higher is required**

To install the library without full voice support, you can just run the following command:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U nextcord

    # Windows
    py -3 -m pip install -U nextcord

Otherwise to get voice support you should run the following command:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U "nextcord[voice]"

    # Windows
    py -3 -m pip install -U nextcord[voice]

To install additional packages for speedup, run the following command:

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U "nextcord[speed]"

    # Windows
    py -3 -m pip install -U nextcord[speed]


To install the development version, do the following:

.. code:: sh

    $ git clone https://github.com/nextcord/nextcord/
    $ cd nextcord
    $ python3 -m pip install -U .[voice]


Optional Packages
~~~~~~~~~~~~~~~~~~

* `PyNaCl <https://pypi.org/project/PyNaCl/>`__ (for voice support)
* `aiodns <https://pypi.org/project/aiodns/>`__, `Brotli <https://pypi.org/project/Brotli/>`__, `cchardet <https://pypi.org/project/cchardet/>`__ (for aiohttp speedup)
* `orjson <https://pypi.org/project/orjson/>`__ (for json speedup)

Please note that on Linux installing voice you must install the following packages via your favourite package manager (e.g. ``apt``, ``dnf``, etc) before running the above commands:

* libffi-dev (or ``libffi-devel`` on some systems)
* python-dev (e.g. ``python3.6-dev`` for Python 3.6)


Quick Example
~~~~~~~~~~~~~

.. code:: py

    from nextcord.ext import commands


    bot = commands.Bot(command_prefix='$')

    @bot.command()
    async def ping(ctx):
        await ctx.reply('Pong!')

    bot.run('token')


You can find more examples in the examples directory.

**NOTE:** It is not advised to leave your token directly in your code, as it allows anyone with it to access your bot. If you intend to make your code public you should `store it securely <https://github.com/nextcord/nextcord/blob/master/examples/secure_token_storage.py/>`_.

Links
------

- `Documentation <https://nextcord.readthedocs.io/en/latest/>`_
- `Official Discord Server <https://discord.gg/ZebatWssCB>`_
- `Discord API <https://discord.gg/discord-api>`_
