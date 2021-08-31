from abc import abstractmethod
from nextcord.ext.abc import ContextBase
import re
from .converter import Converter
from ._types import T_co


_ID_REGEX = re.compile(r'([0-9]{15,20})$')

class IDConverter(Converter[T_co]):
    @staticmethod
    def _get_id_match(argument):
        return _ID_REGEX.match(argument)

    @abstractmethod
    async def convert_from_id(self, ctx: ContextBase, id: int) -> T_co:
        """The base class of converters that can convert from a given id to some object.

        Classes that derive from this should override the :meth:`~.IDConverter.convert_from_id`
        method to do its conversion logic. This method must be a :ref:`coroutine <coroutine>`.
        """
        pass