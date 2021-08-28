nextcord
========

.. image:: https://discord.com/api/guilds/336642139381301249/embed.png
   :target: https://discord.gg/ZebatWssCB
   :alt: Discordサーバーの招待
.. image:: https://img.shields.io/pypi/v/nextcord.svg
   :target: https://pypi.python.org/pypi/nextcord
   :alt: PyPIのバージョン情報
.. image:: https://img.shields.io/pypi/pyversions/nextcord.svg
   :target: https://pypi.python.org/pypi/nextcord
   :alt: PyPIのサポートしているPythonのバージョン

nextcord は機能豊富かつモダンで使いやすい、非同期処理にも対応したDiscord用のAPIラッパーです。

主な特徴
-------------

- ``async`` と ``await`` を使ったモダンなPythonらしいAPI。
- 適切なレート制限処理
- メモリと速度の両方を最適化。

インストール
-------------

**Python 3.8 以降のバージョンが必須です**

完全な音声サポートなしでライブラリをインストールする場合は次のコマンドを実行してください:

.. code:: sh

    # Linux/OS X
    python3 -m pip install -U nextcord

    # Windows
    py -3 -m pip install -U nextcord

音声サポートが必要なら、次のコマンドを実行しましょう:

.. code:: sh

    # Linux/OS X
    python3 -m pip install -U nextcord[voice]

    # Windows
    py -3 -m pip install -U nextcord[voice]


開発版をインストールしたいのならば、次の手順に従ってください:

.. code:: sh

    $ git clone https://github.com/nextcord/nextcord/
    $ cd nextcord
    $ python3 -m pip install -U .[voice]


オプションパッケージ
~~~~~~~~~~~~~~~~~~~~~~

* PyNaCl (音声サポート用)

Linuxで音声サポートを導入するには、前述のコマンドを実行する前にお気に入りのパッケージマネージャー(例えば ``apt`` や ``dnf`` など)を使って以下のパッケージをインストールする必要があります:

* libffi-dev (システムによっては ``libffi-devel``)
* python-dev (例えばPython 3.6用の ``python3.6-dev``)

簡単な例
--------------

.. code:: py

    from nextcord.ext import commands

    class MyBot(commands.Bot):
        async def on_ready(self):
            print('Logged on as', self.user)


    bot = MyBot()
    bot.run('token')

    @bot.command()
    async def ping(ctx: commands.Context):
        await ctx.send('pong')

Botの例
~~~~~~~~~~~~~

.. code:: py

    from nextcord.ext import commands

    bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'))

    @bot.command()
    async def ping(ctx):
        await ctx.send('pong')

    bot.run('token')

examplesディレクトリに更に多くのサンプルがあります。

リンク
------

- `ドキュメント <https://discordpy.readthedocs.io/ja/latest/index.html>`_
- `公式Discordサーバー <https://discord.gg/ZebatWssCB>`_
- `Discord API <https://discord.gg/discord-api>`_
