# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional, Type, TypeVar

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self

    from .abc import Messageable

    TypingT = TypeVar("TypingT", bound="Typing")

__all__ = ("Typing",)


def _typing_done_callback(fut: asyncio.Future) -> None:
    # just retrieve any exception and call it a day
    try:
        fut.exception()
    except (asyncio.CancelledError, Exception):
        pass


class Typing:
    def __init__(self, messageable: Messageable) -> None:
        self.loop: asyncio.AbstractEventLoop = messageable._state.loop
        self.messageable: Messageable = messageable

    async def do_typing(self) -> None:
        try:
            channel = self._channel
        except AttributeError:
            channel = await self.messageable._get_channel()

        typing = channel._state.http.send_typing

        while True:
            await typing(channel.id)
            await asyncio.sleep(5)

    def __enter__(self) -> Self:
        self.task: asyncio.Task = self.loop.create_task(self.do_typing())
        self.task.add_done_callback(_typing_done_callback)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.task.cancel()

    async def __aenter__(self) -> Self:
        self._channel = channel = await self.messageable._get_channel()
        await channel._state.http.send_typing(channel.id)
        return self.__enter__()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.task.cancel()
