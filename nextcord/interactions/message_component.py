from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from ..errors import InvalidArgument
from ..message import Message
from .base import Interaction

__all__ = ("MessageComponentInteraction",)

if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.interactions import Interaction as InteractionPayload


class MessageComponentInteraction(Interaction):
    """Represents the interaction for all messsage components.

    This interaction gets triggered by a :class:`nextcord.ui.View`.

    .. container:: operations

        .. describe:: x == y

            Checks if two interactions are equal.

        .. describe:: x != y

            Checks if two interactions are not equal.

        .. describe:: hash(x)

            Returns the interaction's hash.

    Attributes
    ----------
    message: :class:`Message`
        The message the component is attached to.
    component_id: :class:`str`
        The ID of the component that triggered the interaction.
    value: :class:`str`
        The value of the component that triggered the interaction.
    """

    __slots__: Tuple[str, ...] = (
        "message",
        "component_id",
        "value",
    )

    def __init__(self, *, data: InteractionPayload, state: ConnectionState) -> None:
        super().__init__(data=data, state=state)

    def _from_data(self, data: InteractionPayload) -> None:
        super()._from_data(data=data)

        message = data["message"]  # type: ignore # should be present here - not sure why its causing issues
        self.message = self._state._get_message(
            int(message["id"])
        ) or Message(  # ---- check for and create correct message object ----
            state=self._state, channel=self.channel, data=message  # type: ignore
        )
        self.component_id = self.data["custom_id"]  # type: ignore # self.data should be present here

        try:
            self.value = self.data["values"]  # type: ignore # self.data should be present here
        except KeyError:
            self.value = None

    async def edit(self, *args, **kwargs) -> Optional[Message]:
        """|coro|

        This is a shorthand function for helping in editing messages in
        response to a component or modal submit interaction. If the
        interaction has not been responded to, :meth:`InteractionResponse.edit_message`
        is used. If the response :meth:`~InteractionResponse.is_done` then
        the message is edited via the :attr:`Interaction.message` using
        :meth:`Message.edit` instead.

        Raises
        ------
        HTTPException
            Editing the message failed.
        InvalidArgument
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``.
        TypeError
            An object not of type :class:`File` was passed to ``file`` or ``files``.
        HTTPException
            Editing the message failed.
        InvalidArgument
            :attr:`Interaction.message` was ``None``, this may occur in a :class:`Thread`
            or when the interaction is not a component or modal submit interaction.

        Returns
        -------
        Optional[:class:`Message`]
            The edited message. If the interaction has not yet been responded to,
            :meth:`InteractionResponse.edit_message` is used which returns
            a :class:`Message` or ``None`` corresponding to :attr:`Interaction.message`.
            Otherwise, the :class:`Message` is returned via :meth:`Message.edit`.
        """
        if not self.response.is_done():
            return await self.response.edit_message(*args, **kwargs)
        if self.message is not None:
            return await self.followup.edit_message(self.message.id, *args, **kwargs)
        raise InvalidArgument(
            "Interaction.message is None, this method can only be used in "
            "response to a component or modal submit interaction."
        )
