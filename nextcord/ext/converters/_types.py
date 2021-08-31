import nextcord
from typing import TypeVar


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
ChannelT = TypeVar('ChannelT', bound=nextcord.abc.GuildChannel)
ThreadT = TypeVar('ThreadT', bound=nextcord.Thread)