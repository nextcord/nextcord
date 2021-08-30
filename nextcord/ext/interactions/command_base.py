from typing import TYPE_CHECKING, Generic, TypeVar
from typing_extensions import ParamSpec
from ._types import CogT
from .context_base import ContextBase

class CommandBase:
    def __init__(self):
        """
        TODO: Implement
        """

    async def invoke(self, ctx: ContextBase) -> None:
        """
        TODO: Implement

        Args:
            ctx (ContextBase): [description]
        """

    async def dispatch_error(self, ctx: ContextBase, error: Exception) -> None:
        """
        TODO: Implement

        Args:
            ctx (Context): [description]
            error (Exception): [description]
        """