.. currentmodule:: nextcord

.. _migrating_nextcord:

Migrating to nextcord
=====================

Due to the `original discord.py repository <https://github.com/Rapptz/discord.py>`_ becoming read-only, we decided
that it would be necessary to fork it and keep on developing further. We also wanted to change the name and voted on
nextcord in order to properly register it at pypi.

Porting from discord.py
-----------------------

In order to port a bot using discord.py to nextcord, follow these steps:

1. Uninstall discord.py:

    .. code:: sh

        # Linux/macOS
        python3 -m pip uninstall discord.py

        # Windows
        py -3 -m pip uninstall discord.py

2. Install nextcord:

    .. code:: sh

        # Linux/macOS
        python3 -m pip install -U nextcord

        # Windows
        py -3 -m pip install -U nextcord

3. Update the following import statements:

    * ``import discord`` -> ``import nextcord``
    * ``from discord.ext`` -> ``from nextcord.ext``

4. For all places in your code that used ``discord`` (embeds, colors, etc), change them to use ``nextcord``.

    Note: Steps 3 and 4 are not entirely necessary and your code should still work, but is highly recommended.

    For more information on migrations, view the rest of the migration documentation:

.. toctree::
    :maxdepth: 1

    migrating
    migrating_2
