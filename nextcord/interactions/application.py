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
from ..message import Attachment
from ..types.snowflake import Snowflake
from ..webhook.async_ import WebhookMessage, async_context, handle_message_parameters
from .base import (
    Interaction,
    InteractionMessage,
    InteractionResponse,
    PartialInteractionMessage,
    _InteractionMessageState,
)

__all__ = ("ApplicationCommandInteraction", "ApplicationAutocompleteInteraction")

if TYPE_CHECKING:
    from ..application_command import (
        BaseApplicationCommand,
        SlashApplicationSubcommand,
        SlashOptionData,
    )
    from ..message import AllowedMentions
    from ..state import ConnectionState
    from ..types.interactions import (
        ApplicationAutocompleteInteraction as ApplicationAutocompletePayload,
        ApplicationCommandInteraction as ApplicationCommandPayload,
        ApplicationCommandInteractionData as InteractionData,
        ApplicationCommandInteractionDataOption as OptionsPayload,
    )
    from ..ui.modal import Modal
    from ..ui.view import View

MISSING: Any = utils.MISSING


class ApplicationCommandInteraction(Interaction):
    """Represents the interaction for all application commands.

    This interaction is a subclass of :class:`Interaction`.

    .. container:: operations

        .. describe:: x == y

            Checks if two interactions are equal.

        .. describe:: x != y

            Checks if two interactions are not equal.

        .. describe:: hash(x)

            Returns the interaction's hash.

    Attributes
    ----------
    application_command: Union[SlashApplicationSubcommand, BaseApplicationCommand]
        The application command that triggered the interaction.
    app_command_name: :class:`str`
        The name of the application command that triggered the interaction.
    app_command_id: :class:`int`
        The application command ID that triggered the interaction.
    options: List[SlashOptionData]
        The application command options that have been given a value.
    """

    __slots__: Tuple[str, ...] = (
        "application_command",
        "app_command_name",
        "app_command_id",
        "options",
    )

    def __init__(self, *, data: ApplicationCommandPayload, state: ConnectionState) -> None:
        super().__init__(data=data, state=state)

        self.application_command: Optional[
            Union[SlashApplicationSubcommand, BaseApplicationCommand]
        ] = None

    def _from_data(self, data: ApplicationCommandPayload) -> None:
        super()._from_data(data=data)

        self.data: InteractionData = data.get("data")
        self.app_command_name: str = self.data["name"]
        self.app_command_id: Snowflake = self.data["id"]

        options = self.data.get("options")
        self.options: List[SlashOptionData] = (
            self._get_application_options(options) if options else []
        )

    def _set_application_command(
        self, app_cmd: Union[SlashApplicationSubcommand, BaseApplicationCommand]
    ) -> None:
        self.application_command = app_cmd

    def _get_application_options(self, options: List[OptionsPayload]) -> List[SlashOptionData]:
        if len(options) == 0:
            # return empty list if no options exist
            return []

        # iterate through options to get inputs
        # The option data gets nested 1x for each subcommand level
        # E.x. "/parent child subcommand" has 2 subcommands -> options get nested 2x
        while "options" in options[0]:
            options = options[0]["options"]  # type: ignore - Key exists only for one type -> accounted for by while loop

            if not options:
                # return empty list if no options exist
                return []

        from ..application_command import (  # Importing here due to circular import issues
            SlashOptionData,
        )

        return [SlashOptionData(option) for option in options]

    @utils.cached_slot_property("_cs_response")
    def response(self) -> ApplicationCommandInteractionResponse:
        """:class:`ApplicationCommandInteractionResponse`: Returns an object responsible for handling responding to the interaction.

        A response can only be done once. If secondary messages need to be sent, consider using :attr:`followup`
        instead.
        """
        return ApplicationCommandInteractionResponse(self)

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
        :meth:`ApplicationCommandInteractionResponse.send_message` is used. If the response
        :meth:`~ApplicationCommandInteractionResponse.is_done` then the message is sent
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
            or :meth:`ApplicationCommandInteraction.original_message`.
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

        If the interaction response was :meth:`InteractionResponse.send_message` then this would
        return the message that was sent using that response.

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


class ApplicationCommandInteractionResponse(InteractionResponse):
    """Represents a Discord application command interaction response.

    This interaction response is a subclass of :class:`InteractionResponse`.

    This type can be accessed through :attr:`ApplicationCommandInteraction.response`.
    """

    def __init__(self, parent: ApplicationCommandInteraction) -> None:
        self._parent: ApplicationCommandInteraction = parent
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
                data = {"flags": MessageFlags.ephemeral.flag}
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
            The interaction has expired. :meth:`ApplicationCommandInteractionResponse.defer` and
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
            or :meth:`ApplicationCommandInteraction.original_message`.
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


class ApplicationAutocompleteInteraction(Interaction):
    """Represents the interaction for Autocompletes.

    This interaction is a subclass of :class:`Interaction`.

    .. container:: operations

        .. describe:: x == y

            Checks if two interactions are equal.

        .. describe:: x != y

            Checks if two interactions are not equal.

        .. describe:: hash(x)

            Returns the interaction's hash.

    Attributes
    ----------
    application_command: Union[SlashApplicationSubcommand, BaseApplicationCommand]
        The application command that triggered the interaction.
    app_command_name: :class:`str`
        The name of the application command that triggered the interaction.
    app_command_id: :class:`int`
        The application command ID that triggered the interaction.
    focused_option: :class:`SlashOptionData`
        The option the autocomplete is for.
    options: List[SlashOptionData]
        The application command options that have been given a value.
    """

    __slots__: Tuple[str, ...] = (
        "application_command",
        "app_command_name",
        "app_command_id",
        "options",
    )

    def __init__(self, *, data: ApplicationAutocompletePayload, state: ConnectionState) -> None:
        super().__init__(data=data, state=state)

        self.application_command: Optional[
            Union[SlashApplicationSubcommand, BaseApplicationCommand]
        ] = None

    def _from_data(self, data: ApplicationCommandPayload) -> None:
        super()._from_data(data=data)
        self.data: InteractionData = data.get("data")

        self.app_command_name: str = self.data["name"]
        self.app_command_id: Snowflake = self.data["id"]

        options = self.data.get("options")
        self.options: List[SlashOptionData] = (
            self._get_application_options(options) if options else []
        )

    def _set_application_command(
        self, app_cmd: Union[SlashApplicationSubcommand, BaseApplicationCommand]
    ) -> None:
        self.application_command = app_cmd

    def _get_application_options(self, options: List[OptionsPayload]) -> List[SlashOptionData]:
        if len(options) == 0:
            # return empty list if no options exist
            return []

        # iterate through options to get inputs
        # The option data gets nested 1x for each subcommand level
        # E.x. "/parent child subcommand" has 2 subcommands -> options get nested 2x
        while "options" in options[0]:
            options = options[0]["options"]  # type: ignore - Key exists only for one type -> accounted for by while loop

            if not options:
                # return empty list if no options exist
                return []

        from ..application_command import (  # Importing here due to circular import issues
            SlashOptionData,
        )

        return [SlashOptionData(option) for option in options]

    @property
    def focused_option(self) -> Optional[SlashOptionData]:
        """The application command option the autocomplete was called for."""
        return next((option for option in self.options if option.focused), None)

    @utils.cached_slot_property("_cs_response")
    def response(self) -> ApplicationAutocompleteInteractionResponse:
        """:class:`ApplicationAutocompleteInteractionResponse`: Returns an object responsible for handling responding to the interaction.

        A response can only be done once. If secondary messages need to be sent, consider using :attr:`followup`
        instead.
        """
        return ApplicationAutocompleteInteractionResponse(self)


class ApplicationAutocompleteInteractionResponse(InteractionResponse):
    """Represents a Discord application autocomplete interaction response.

    This interaction response is a subclass of :class:`InteractionResponse`.

    This type can be accessed through :attr:`Interaction.response`.
    """

    def __init__(self, parent: ApplicationAutocompleteInteraction) -> None:
        self._parent: ApplicationAutocompleteInteraction = parent
        self._responded: bool = False

    async def send_autocomplete(self, choices: Union[dict, list]) -> None:
        """|coro|

        Responds to this interaction by sending an autocomplete payload.

        Parameters
        ----------
        choices: Union[:class:`dict`, :class:`list`]
            The choices to send the user.
            If a :class:`dict` is given, each key-value pair is turned into a name-value pair. Name is what Discord
            shows the user, value is what Discord sends to the bot.
            If something not a :class:`dict`, such as a :class:`list`, is given, each value is turned into a duplicate
            name-value pair, where the display name and the value Discord sends back are the same.

        Raises
        ------
        HTTPException
            Sending the message failed.
        InteractionResponded
            This interaction has already been responded to before.
        """
        if self._responded:
            raise InteractionResponded(self._parent)
        if not isinstance(choices, dict):
            choice_list = [{"name": choice, "value": choice} for choice in choices]
        else:
            choice_list = [{"name": key, "value": value} for key, value in choices.items()]

        payload = {"choices": choice_list}

        adapter = async_context.get()
        await adapter.create_interaction_response(
            self._parent.id,
            self._parent.token,
            session=self._parent._session,
            type=InteractionResponseType.application_command_autocomplete_result.value,
            data=payload,
        )
        self._responded = True
