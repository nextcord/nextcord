.. currentmodule:: nextcord

.. _migrating_2_0:

Migrating to v2.0
======================

Changing to v2.0 represents different breaking changes we needed to make. We did not only needed to fork the
original discord.py repository but adapt changes in the Discord API in order of supporting its latest features,
to work with threads, buttons and commands.


Python Version Change
-----------------------

In order to make development easier,
the library had to remove support for Python versions lower than 3.8,
which essentially means that **support for Python 3.7, 3.6 and 3.5
is dropped**. We recommend updating to Python version 3.9.

Meta Change
-----------------------

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

- The public API should be completly typehinted
- Almost all ``edit`` methods now return their updated counterpart rather than doing an in-place edit.

