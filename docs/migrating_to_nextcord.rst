.. currentmodule:: nextcord

.. _migrating_nextcord:

Migrating to nextcord
======================

Due to the `original discord.py repository <https://github.com/Rapptz/discord.py>`_ becoming read-only, we decided
that it would be necessary to fork it and keep on developing further. We also wanted to change the name and voted on
nextcord in order to properly register it at pypi.

Porting from discord.py
-------------------------

In order to port a bot using discord.py to nextcord, follow these steps:

1. Install nextcord: 

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U nextcord

    # Windows
    py -3 -m pip install -U nextcord

2. Uninstall discord.py:

..code:: sh

    # Linux/macOS
    python3 -m pip uninstall discord

    # Windows
    py -3 -m pip uninstall discord

3. Update the following import statements:

* ``import discord`` -> ``import nextcord as discord``
* ``from discord.ext`` -> ``from nextcord.ext``

Note: Step 3 is not entirely necessary and your code should still work, but is highly recommended.

For more information on migrations, view the rest of the migration documentation:

.. toctree::
  :maxdepth: 1

  migrating
  migrating_2