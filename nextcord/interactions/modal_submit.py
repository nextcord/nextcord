from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from ..errors import InvalidArgument
from ..message import Message
from .base import Interaction

__all__ = ("ModalSubmitInteraction",)

if TYPE_CHECKING:
    from ..state import ConnectionState
    from ..types.interactions import Interaction as InteractionPayload


class ModalSubmitInteraction(Interaction):
    """Represents the interaction for all modal submits.

    This interaction gets triggered by :class:`nextcord.ui.Modal`

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
        The message the modal was called from.
    modal_id: :class:`int`
        The ID of the modal that triggered the interaction.
    """

    __slots__: Tuple[str, ...] = (
        "modal_id",
        "message",
    )

    def __init__(self, *, data: InteractionPayload, state: ConnectionState) -> None:
        super().__init__(data=data, state=state)

    def _from_data(self, data: InteractionPayload) -> None:
        super()._from_data(data=data)

        self.modal_id = self.data["custom_id"]  # type: ignore # self.data should be present here

        self.message: Optional[Message]
        try:
            message = data["message"]

            # TODO: Check for an create correct message type
            self.message = self._state._get_message(int(message["id"])) or Message(
                state=self._state, channel=self.channel, data=message  # type: ignore
            )
        except KeyError:
            self.message = None

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
