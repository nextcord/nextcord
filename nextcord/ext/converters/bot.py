from nextcord.ext.commands.bot import BotBase, Bot, AutoShardedBot
from .core import ConvertersGroupMixin


class ConvertersBotBase(BotBase, ConvertersGroupMixin):
    ...

class ConvertersBot(Bot, ConvertersBotBase):
    ...

class AutoShardedConvertersBot(AutoShardedBot, ConvertersBotBase):
    ...
