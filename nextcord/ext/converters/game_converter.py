from .converter import Converter
from nextcord import Game
from nextcord.ext.abc import ContextBase

class GameConverter(Converter[Game]):
    """Converts to :class:`~Game`."""

    async def convert(self, ctx: ContextBase, argument: str) -> Game:
        return Game(name=argument)