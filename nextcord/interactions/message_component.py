# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from .. import utils
from ..embeds import Embed
from ..enums import InteractionResponseType, InteractionType
from ..errors import ClientException, HTTPException, InteractionResponded, InvalidArgument
from ..file import File
from ..flags import MessageFlags
from ..message import Attachment, Message
from ..webhook.async_ import WebhookMessage, async_context, handle_message_parameters
from .base import (
    MISSING,
    Interaction,
    InteractionMessage,
    InteractionResponse,
    PartialInteractionMessage,
    _InteractionMessageState,
)

__all__ = ("MessageComponentInteraction",)

if TYPE_CHECKING:
    from ..message import AllowedMentions
    from ..state import ConnectionState
    from ..types.interactions import MessageComponentInteraction as MessageComponentPayload
    from ..ui.modal import Modal
    from ..ui.view import View
    from .modal_submit import ModalSubmitInteraction


class MessageComponentInteraction(Interaction):
    """Represents the interaction for all messsage components.

    This interaction is a subclass of :class:`Interaction`.

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

    def __init__(self, *, data: MessageComponentPayload, state: ConnectionState) -> None:
        super().__init__(data=data, state=state)

    def _from_data(self, data: MessageComponentPayload) -> None:
        super()._from_data(data=data)

        message = data["message"]
        self.message = self._state._get_message(int(message["id"])) or Message(
            state=self._state, channel=self.channel, data=message  # type: ignore
        )
        self.component_id = self.data["custom_id"]  # type: ignore # self.data should be present here

        try:
            self.value = self.data["values"]  # type: ignore # self.data should be present here
        except KeyError:
            self.value = None

    @utils.cached_slot_property("_cs_response")
    def response(self) -> MessageComponentInteractionResponse:
        """:class:`MessageComponentInteractionResponse`: Returns an object responsible for handling responding to the interaction.

        A response can only be done once. If secondary messages need to be sent, consider using :attr:`followup`
        instead.
        """
        return MessageComponentInteractionResponse(self)

    async def edit(self, *args, **kwargs) -> Optional[Message]:
        """|coro|

        This is a shorthand function for helping in editing messages in
        response to a component interaction. If the
        interaction has not been responded to, :meth:`MessageComponentInteractionResponse.edit_message`
        is used. If the response :meth:`~InteractionResponse.is_done` then
        the message is edited via the :attr:`MessageComponentInteraction.message` using
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

        Returns
        -------
        Optional[:class:`Message`]
            The edited message. If the interaction has not yet been responded to,
            :meth:`MessageComponentInteractionResponse.edit_message` is used which returns
            a :class:`Message` or ``None`` corresponding to :attr:`MessageComponentInteraction.message`.
            Otherwise, the :class:`Message` is returned via :meth:`Message.edit`.
        """
        if not self.response.is_done():
            return await self.response.edit_message(*args, **kwargs)
        else:
            return await self.followup.edit_message(self.message.id, *args, **kwargs)

    async def send(
        self,
        content: Optional[str] = None,
        *,
        embed: Embed = MISSING,
        embeds: List[Embed] = MISSING,
        file: File = MISSING,
        files: List[File] = MISSING,
        view: View = MISSING,
        tts: bool = False,
        delete_after: Optional[float] = None,
        allowed_mentions: AllowedMentions = MISSING,
        flags: Optional[MessageFlags] = None,
        ephemeral: Optional[bool] = None,
        suppress_embeds: Optional[bool] = None,
    ) -> Union[PartialInteractionMessage, WebhookMessage]:
        """|coro|

        This is a shorthand function for helping in sending messages in
        response to an interaction. If the interaction has not been responded to,
        :meth:`MessageComponentInteractionResponse.send_message` is used. If the response
        :meth:`~InteractionResponse.is_done` then the message is sent
        via :attr:`Interaction.followup` using :class:`Webhook.send` instead.

        Raises
        ------
        HTTPException
            Sending the message failed.
        NotFound
            The interaction has expired or the interaction has been responded to
            but the followup webhook is expired.
        Forbidden
            The authorization token for the webhook is incorrect.
        InvalidArgument
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``.
        ValueError
            The length of ``embeds`` was invalid.

        Returns
        -------
        Union[:class:`PartialInteractionMessage`, :class:`WebhookMessage`]
            If the interaction has not been responded to, returns a :class:`PartialInteractionMessage`
            supporting only the :meth:`~PartialInteractionMessage.edit` and :meth:`~PartialInteractionMessage.delete`
            operations. To fetch the :class:`InteractionMessage` you may use :meth:`~PartialInteractionMessage.fetch`
            or :meth:`MessageComponentInteraction.original_message`.
            If the interaction has been responded to, returns the :class:`WebhookMessage`.
        """

        if not self.response.is_done():
            return await self.response.send_message(
                content=content,
                embed=embed,
                embeds=embeds,
                file=file,
                files=files,
                view=view,
                tts=tts,
                ephemeral=ephemeral,
                delete_after=delete_after,
                allowed_mentions=allowed_mentions,
                flags=flags,
                suppress_embeds=suppress_embeds,
            )
        return await self.followup.send(
            content=content,  # type: ignore
            embed=embed,
            embeds=embeds,
            file=file,
            files=files,
            view=view,
            tts=tts,
            ephemeral=ephemeral,
            delete_after=delete_after,
            allowed_mentions=allowed_mentions,
            flags=flags,
            suppress_embeds=suppress_embeds,
        )

    async def delete_original_message(self, *, delay: Optional[float] = None) -> None:
        """|coro|

        Deletes the original interaction response message.

        This is a lower level interface to :meth:`InteractionMessage.delete` in case
        you do not want to fetch the message and save an HTTP request.

        Parameters
        ----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait before deleting the message.
            The waiting is done in the background and deletion failures are ignored.

        Raises
        ------
        HTTPException
            Deleting the message failed.
        Forbidden
            Deleted a message that is not yours.
        """
        adapter = async_context.get()
        delete_func = adapter.delete_original_interaction_response(
            self.application_id,
            self.token,
            session=self._session,
        )

        if delay is not None:

            async def inner_call(delay: float = delay) -> None:
                await asyncio.sleep(delay)
                try:
                    await delete_func
                except HTTPException:
                    pass

            asyncio.create_task(inner_call())
        else:
            await delete_func

    async def edit_original_message(
        self,
        *,
        content: Optional[str] = MISSING,
        embeds: List[Embed] = MISSING,
        embed: Optional[Embed] = MISSING,
        file: File = MISSING,
        files: List[File] = MISSING,
        attachments: List[Attachment] = MISSING,
        view: Optional[View] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None,
    ) -> InteractionMessage:
        """|coro|

        Edits the original interaction response message.

        This is a lower level interface to :meth:`InteractionMessage.edit` in case
        you do not want to fetch the message and save an HTTP request.

        This method is also the only way to edit the original message if
        the message sent was ephemeral.

        Parameters
        ----------
        content: Optional[:class:`str`]
            The content to edit the message with or ``None`` to clear it.
        embeds: List[:class:`Embed`]
            A list of embeds to edit the message with.
        embed: Optional[:class:`Embed`]
            The embed to edit the message with. ``None`` suppresses the embeds.
            This should not be mixed with the ``embeds`` parameter.
        file: :class:`File`
            The file to upload. This cannot be mixed with ``files`` parameter.
        files: List[:class:`File`]
            A list of files to send with the content. This cannot be mixed with the
            ``file`` parameter.
        attachments: List[:class:`Attachment`]
            A list of attachments to keep in the message. To keep existing attachments,
            you must fetch the message with :meth:`original_message` and pass
            ``message.attachments`` to this parameter.
        allowed_mentions: :class:`AllowedMentions`
            Controls the mentions being processed in this message.
            See :meth:`.abc.Messageable.send` for more information.
        view: Optional[:class:`~nextcord.ui.View`]
            The updated view to update this message with. If ``None`` is passed then
            the view is removed.

        Raises
        ------
        HTTPException
            Editing the message failed.
        Forbidden
            Edited a message that is not yours.
        InvalidArgument
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``.
        ValueError
            The length of ``embeds`` was invalid.

        Returns
        -------
        :class:`InteractionMessage`
            The newly edited message.
        """

        previous_mentions: Optional[AllowedMentions] = self._state.allowed_mentions
        params = handle_message_parameters(
            content=content,
            file=file,
            files=files,
            attachments=attachments,
            embed=embed,
            embeds=embeds,
            view=view,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_mentions,
        )
        adapter = async_context.get()
        data = await adapter.edit_original_interaction_response(
            self.application_id,
            self.token,
            session=self._session,
            payload=params.payload,
            multipart=params.multipart,
            files=params.files,
        )

        # The message channel types should always match
        message = InteractionMessage(state=self._state, channel=self.channel, data=data)  # type: ignore
        if view and not view.is_finished() and view.prevent_update:
            self._state.store_view(view, message.id)
        return message

    async def original_message(self) -> InteractionMessage:
        """|coro|

        Fetches the original interaction response message associated with the interaction.

        If the interaction response was :meth:`MessageComponentInteractionResponse.send_message` then this would
        return the message that was sent using that response. Otherwise, this would return
        the message that triggered the interaction.

        Repeated calls to this will return a cached value.

        Raises
        ------
        HTTPException
            Fetching the original response message failed.
        ClientException
            The channel for the message could not be resolved.

        Returns
        -------
        InteractionMessage
            The original interaction response message.
        """

        if self._original_message is not None:
            return self._original_message

        # TODO: fix later to not raise?
        channel = self.channel
        if channel is None:
            raise ClientException("Channel for message could not be resolved")

        adapter = async_context.get()
        data = await adapter.get_original_interaction_response(
            application_id=self.application_id,
            token=self.token,
            session=self._session,
        )
        state = _InteractionMessageState(self, self._state)
        message = InteractionMessage(state=state, channel=channel, data=data)  # type: ignore
        self._original_message = message
        return message


class MessageComponentInteractionResponse(InteractionResponse):
    """Represents a Discord interaction response.

    This interaction response is a subclass of :class:`InteractionResponse`.

    This type can be accessed through :attr:`Interaction.response`.
    """

    __slots__: Tuple[str, ...] = (
        "_responded",
        "_parent",
    )

    def __init__(self, parent: MessageComponentInteraction) -> None:
        self._parent: MessageComponentInteraction = parent
        self._responded: bool = False

    async def defer(self, *, ephemeral: bool = False, with_message: bool = False) -> None:
        """|coro|

        Defers the interaction response.

        This is typically used when the interaction is acknowledged
        and a secondary action will be done later.

        Parameters
        ----------
        ephemeral: :class:`bool`
            Indicates whether the deferred message will eventually be ephemeral.
            This only applies for interactions of type :attr:`InteractionType.application_command` or when ``with_message`` is True
        with_message: :class:`bool`
            Indicates whether the response will be a message with thinking state (bot is thinking...).
            This is always True for interactions of type :attr:`InteractionType.application_command`.
            For interactions of type :attr:`InteractionType.component` this defaults to False.

            .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Deferring the interaction failed.
        InteractionResponded
            This interaction has already been responded to before.
        """
        if self._responded:
            raise InteractionResponded(self._parent)

        defer_type: int = 0
        data: Optional[Dict[str, Any]] = None
        parent = self._parent
        if parent.type is InteractionType.application_command or with_message:
            defer_type = InteractionResponseType.deferred_channel_message.value
            if ephemeral:
                data = {"flags": 64}
        elif (
            parent.type is InteractionType.component or parent.type is InteractionType.modal_submit
        ):
            defer_type = InteractionResponseType.deferred_message_update.value

        if defer_type:
            adapter = async_context.get()
            await adapter.create_interaction_response(
                parent.id, parent.token, session=parent._session, type=defer_type, data=data
            )
            self._responded = True

    async def send_message(
        self,
        content: Optional[Any] = None,
        *,
        embed: Embed = MISSING,
        embeds: List[Embed] = MISSING,
        file: File = MISSING,
        files: List[File] = MISSING,
        view: View = MISSING,
        tts: bool = False,
        delete_after: Optional[float] = None,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        flags: Optional[MessageFlags] = None,
        ephemeral: Optional[bool] = None,
        suppress_embeds: Optional[bool] = None,
    ) -> PartialInteractionMessage:
        """|coro|

        Responds to this interaction by sending a message.

        .. versionchanged:: 2.4

            ``ephemeral`` can now accept ``None`` to indicate that
            ``flags`` should be used.

        Parameters
        ----------
        content: Optional[:class:`str`]
            The content of the message to send.
        embeds: List[:class:`Embed`]
            A list of embeds to send with the content. Maximum of 10. This cannot
            be mixed with the ``embed`` parameter.
        embed: :class:`Embed`
            The rich embed for the content to send. This cannot be mixed with
            ``embeds`` parameter.
        file: :class:`File`
            The file to upload.
        files: List[:class:`File`]
            A list of files to upload. Maximum of 10. This cannot be mixed with
            the ``file`` parameter.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        view: :class:`nextcord.ui.View`
            The view to send with the message.
        ephemeral: :class:`bool`
            Indicates if the message should only be visible to the user who started the interaction.
            If a view is sent with an ephemeral message and it has no timeout set then the timeout
            is set to 15 minutes.
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: :class:`AllowedMentions`
            Controls the mentions being processed in this message.
            See :meth:`.abc.Messageable.send` for more information.
        flags: Optional[:class:`~nextcord.MessageFlags`]
            The message flags being set for this message.
            Currently only :class:`~nextcord.MessageFlags.suppress_embeds` is able to be set.

            .. versionadded:: 2.4
        suppress_embeds: Optional[:class:`bool`]
            Whether to suppress embeds on this message.

            .. versionadded:: 2.4

        Raises
        ------
        HTTPException
            Sending the message failed.
        NotFound
            The interaction has expired. :meth:`MessageComponentInteractionResponse.defer` and
            :attr:`Interaction.followup` should be used if the interaction will take
            a while to respond.
        InvalidArgument
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``.
        TypeError
            An object not of type :class:`File` was passed to ``file`` or ``files``.
        ValueError
            The length of ``embeds`` was invalid.
        InteractionResponded
            This interaction has already been responded to before.

        Returns
        -------
        :class:`PartialInteractionMessage`
            An object supporting only the :meth:`~PartialInteractionMessage.edit` and :meth:`~PartialInteractionMessage.delete`
            operations. To fetch the :class:`InteractionMessage` you may use :meth:`PartialInteractionMessage.fetch`
            or :meth:`MessageComponentInteraction.original_message`.
        """
        if self._responded:
            raise InteractionResponded(self._parent)

        payload: Dict[str, Any] = {
            "tts": tts,
        }

        if embed is not MISSING and embeds is not MISSING:
            raise InvalidArgument("Cannot mix embed and embeds keyword arguments")

        if embed is not MISSING:
            embeds = [embed]

        if embeds:
            payload["embeds"] = [e.to_dict() for e in embeds]

        if file is not MISSING and files is not MISSING:
            raise InvalidArgument("Cannot mix file and files keyword arguments")

        if file is not MISSING:
            files = [file]

        if files and not all(isinstance(f, File) for f in files):
            raise TypeError("Files parameter must be a list of type File")

        if content is not None:
            payload["content"] = str(content)

        if flags is None:
            flags = MessageFlags()
        if suppress_embeds is not None:
            flags.suppress_embeds = suppress_embeds
        if ephemeral is not None:
            flags.ephemeral = ephemeral

        if flags.value != 0:
            payload["flags"] = flags.value

        if view is not MISSING:
            payload["components"] = view.to_components()

        if allowed_mentions is MISSING or allowed_mentions is None:
            if self._parent._state.allowed_mentions is not None:
                payload["allowed_mentions"] = self._parent._state.allowed_mentions.to_dict()
        else:
            if self._parent._state.allowed_mentions is not None:
                payload["allowed_mentions"] = self._parent._state.allowed_mentions.merge(
                    allowed_mentions
                ).to_dict()
            else:
                payload["allowed_mentions"] = allowed_mentions.to_dict()

        parent = self._parent
        adapter = async_context.get()
        try:
            await adapter.create_interaction_response(
                parent.id,
                parent.token,
                session=parent._session,
                type=InteractionResponseType.channel_message.value,
                data=payload,
                files=files,
            )
        finally:
            if files:
                for file in files:
                    file.close()

        if view is not MISSING and view.prevent_update:
            if ephemeral and view.timeout is None:
                view.timeout = 15 * 60.0

            self._parent._state.store_view(view)

        self._responded = True

        if delete_after is not None:
            await self._parent.delete_original_message(delay=delete_after)

        state = _InteractionMessageState(self._parent, self._parent._state)
        return PartialInteractionMessage(state)

    async def send_modal(self, modal: Modal) -> None:
        """|coro|

        Respond to this interaction by sending a modal.

        Parameters
        ----------
        modal: :class:`nextcord.ui.Modal`
            The modal to be sent in response to the interaction and which will
            be displayed on the user's screen.

        Raises
        ------
        HTTPException
            Sending the modal failed.
        InteractionResponded
            This interaction has already been responded to before.
        """
        if self._responded:
            raise InteractionResponded(self._parent)

        parent = self._parent
        adapter = async_context.get()
        await adapter.create_interaction_response(
            parent.id,
            parent.token,
            session=parent._session,
            type=InteractionResponseType.modal.value,
            data=modal.to_dict(),
        )

        self._responded = True

        self._parent._state.store_modal(modal, self._parent.user.id)  # type: ignore

    async def edit_message(
        self,
        *,
        content: Optional[Any] = MISSING,
        embed: Optional[Embed] = MISSING,
        embeds: List[Embed] = MISSING,
        file: File = MISSING,
        files: List[File] = MISSING,
        attachments: List[Attachment] = MISSING,
        view: Optional[View] = MISSING,
        delete_after: Optional[float] = None,
    ) -> Optional[Message]:
        """|coro|

        Responds to this interaction by editing the message that the
        component interaction originated from.

        Parameters
        ----------
        content: Optional[:class:`str`]
            The new content to replace the message with. ``None`` removes the content.
        embeds: List[:class:`Embed`]
            A list of embeds to edit the message with.
        embed: Optional[:class:`Embed`]
            The embed to edit the message with. ``None`` suppresses the embeds.
            This should not be mixed with the ``embeds`` parameter.
        file: :class:`File`
            The file to upload.
        files: List[:class:`File`]
            A list of files to upload. Maximum of 10. This cannot be mixed with
            the ``file`` parameter.
        attachments: List[:class:`Attachment`]
            A list of attachments to keep in the message. To keep all existing attachments,
            pass ``MessageComponentInteraction.message.attachments``.
        view: Optional[:class:`~nextcord.ui.View`]
            The updated view to update this message with. If ``None`` is passed then
            the view is removed.
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.


        Raises
        ------
        HTTPException
            Editing the message failed.
        InvalidArgument
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``.
        TypeError
            An object not of type :class:`File` was passed to ``file`` or ``files``.
        InteractionResponded
            This interaction has already been responded to before.

        Returns
        -------
        Optional[:class:`Message`]
            The message that was edited, or None if the :attr:`MessageComponentInteraction.message` is not found
            (this may happen if the interaction occurred in a :class:`Thread`).
        """
        if self._responded:
            raise InteractionResponded(self._parent)

        parent = self._parent
        state = parent._state

        if isinstance(parent, (MessageComponentInteraction, ModalSubmitInteraction)):
            msg = (
                parent.message
                if isinstance(parent, (MessageComponentInteraction, ModalSubmitInteraction))
                else None
            )
            message_id = msg.id if msg else None
        else:
            msg = None
            message_id = None

        payload = {}
        if content is not MISSING:
            if content is None:
                payload["content"] = None
            else:
                payload["content"] = str(content)

        if embed is not MISSING and embeds is not MISSING:
            raise InvalidArgument("Cannot mix both embed and embeds keyword arguments")

        if embed is not MISSING:
            if embed is None:
                embeds = []
            else:
                embeds = [embed]

        if embeds is not MISSING:
            payload["embeds"] = [e.to_dict() for e in embeds]

        if file is not MISSING and files is not MISSING:
            raise InvalidArgument("Cannot mix file and files keyword arguments")

        if file is not MISSING:
            files = [file]

        if files and not all(isinstance(f, File) for f in files):
            raise TypeError("Files parameter must be a list of type File")

        if attachments is not MISSING:
            payload["attachments"] = [a.to_dict() for a in attachments]

        if view is not MISSING:
            if message_id is not None:
                state.prevent_view_updates_for(message_id)
            if view is None:
                payload["components"] = []
            else:
                payload["components"] = view.to_components()

        adapter = async_context.get()
        try:
            await adapter.create_interaction_response(
                parent.id,
                parent.token,
                session=parent._session,
                type=InteractionResponseType.message_update.value,
                data=payload,
                files=files,
            )
        finally:
            if files:
                for file in files:
                    file.close()

        if view and not view.is_finished() and message_id is not None and view.prevent_update:
            state.store_view(view, message_id)

        self._responded = True

        if delete_after is not None:
            await parent.delete_original_message(delay=delete_after)

        return state._get_message(message_id)
