# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from . import utils
from .channel import ChannelType, PartialMessageable
from .embeds import Embed
from .enums import InteractionResponseType, InteractionType, try_enum
from .errors import ClientException, HTTPException, InteractionResponded, InvalidArgument
from .file import File
from .member import Member
from .message import Attachment, Message
from .mixins import Hashable
from .object import Object
from .permissions import Permissions
from .user import ClientUser, User
from .utils import snowflake_time
from .webhook.async_ import Webhook, WebhookMessage, async_context, handle_message_parameters

__all__ = (
    "Interaction",
    "InteractionMessage",
    "InteractionResponse",
    "PartialInteractionMessage",
)

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from .application_command import BaseApplicationCommand, SlashApplicationSubcommand
    from .channel import (
        CategoryChannel,
        ForumChannel,
        PartialMessageable,
        StageChannel,
        TextChannel,
        VoiceChannel,
    )
    from .client import Client
    from .guild import Guild
    from .message import AllowedMentions
    from .state import ConnectionState
    from .threads import Thread
    from .types.interactions import Interaction as InteractionPayload, InteractionData
    from .ui.modal import Modal
    from .ui.view import View

    InteractionChannel = Union[
        VoiceChannel,
        StageChannel,
        TextChannel,
        CategoryChannel,
        Thread,
        PartialMessageable,
        ForumChannel,
    ]

MISSING: Any = utils.MISSING


class InteractionAttached(dict):
    """Represents the attached data of an interaction.

    This is used to store information about an :class:`Interaction`. This is useful if you want to save some data from a :meth:`ApplicationCommand.application_command_before_invoke` to use later in the callback.

    Example
    ---------

    .. code-block:: python3

        async def attach_db(interaction: Interaction):
            interaction.attached.db = some_real_database()

        async def release_db(interaction: Interaction):
            interaction.attached.db.close()

        @bot.slash_command()
        @application_checks.before_invoke(attach_db)
        @application_checks.after_invoke(release_db)
        async def who(interaction: Interaction): # Output: <User> used who at <Time>
            data = interaction.attached.db.get_data(interaction.user.id)
            await interaction.response.send_message(data)
    """

    def __init__(self):
        super().__init__()
        self.__dict__ = self

    def __repr__(self):
        return f"<InteractionAttached {super().__repr__()}>"


class Interaction(Hashable):
    """Represents a Discord interaction.

    An interaction happens when a user does an action that needs to
    be notified. Current examples are slash commands and components.

    .. container:: operations

        .. describe:: x == y

            Checks if two interactions are equal.

        .. describe:: x != y

            Checks if two interactions are not equal.

        .. describe:: hash(x)

            Returns the interaction's hash.

    .. versionadded:: 2.0

    .. versionchanged:: 2.1
        :class:`Interaction` is now hashable.

    Attributes
    -----------
    id: :class:`int`
        The interaction's ID.
    type: :class:`InteractionType`
        The interaction type.
    guild_id: Optional[:class:`int`]
        The guild ID the interaction was sent from.
    channel_id: Optional[:class:`int`]
        The channel ID the interaction was sent from.
    locale: Optional[:class:`str`]
        The users locale.
    guild_locale: Optional[:class:`str`]
        The guilds preferred locale, if invoked in a guild.
    application_id: :class:`int`
        The application ID that the interaction was for.
    user: Optional[Union[:class:`User`, :class:`Member`]]
        The user or member that sent the interaction.
    message: Optional[:class:`Message`]
        The message that sent this interaction.
    token: :class:`str`
        The token to continue the interaction. These are valid
        for 15 minutes.
    data: :class:`dict`
        The raw interaction data.
    attached: :class:`InteractionAttached`
        The attached data of the interaction. This is used to store any data you may need inside the interaction for convenience. This data will stay on the interaction, even after a :meth:`Interaction.application_command_before_invoke`.
    application_command: Optional[:class:`ApplicationCommand`]
        The application command that handled the interaction.
    """

    __slots__: Tuple[str, ...] = (
        "id",
        "type",
        "guild_id",
        "channel_id",
        "data",
        "application_id",
        "message",
        "user",
        "locale",
        "guild_locale",
        "token",
        "version",
        "application_command",
        "attached",
        "_permissions",
        "_app_permissions",
        "_state",
        "_session",
        "_original_message",
        "_cs_response",
        "_cs_followup",
        "_cs_channel",
    )

    def __init__(self, *, data: InteractionPayload, state: ConnectionState):
        self._state: ConnectionState = state
        self._session: ClientSession = state.http._HTTPClient__session  # type: ignore
        # TODO: this is so janky, accessing a hidden double attribute
        self._original_message: Optional[InteractionMessage] = None
        self.attached = InteractionAttached()
        self.application_command: Optional[
            Union[SlashApplicationSubcommand, BaseApplicationCommand]
        ] = None
        self._from_data(data)

    def _from_data(self, data: InteractionPayload):
        self.id: int = int(data["id"])
        self.type: InteractionType = try_enum(InteractionType, data["type"])
        self.data: Optional[InteractionData] = data.get("data")
        self.token: str = data["token"]
        self.version: int = data["version"]
        self.channel_id: Optional[int] = utils._get_as_snowflake(data, "channel_id")
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, "guild_id")
        self.application_id: int = int(data["application_id"])
        self.locale: Optional[str] = data.get("locale")
        self.guild_locale: Optional[str] = data.get("guild_locale")

        self.message: Optional[Message]
        try:
            message = data["message"]
            self.message = self._state._get_message(int(message["id"])) or Message(
                state=self._state, channel=self.channel, data=message  # type: ignore
            )
        except KeyError:
            self.message = None

        self.user: Optional[Union[User, Member]] = None
        self._app_permissions: int = int(data.get("app_permissions", 0))
        self._permissions: int = 0

        # TODO: there's a potential data loss here
        if self.guild_id:
            guild = self.guild or Object(id=self.guild_id)
            try:
                member = data["member"]
            except KeyError:
                pass
            else:
                cached_member = self.guild and self.guild.get_member(int(member["user"]["id"]))  # type: ignore # user key should be present here
                self.user = cached_member or Member(state=self._state, guild=guild, data=member)  # type: ignore # user key should be present here
                self._permissions = int(member.get("permissions", 0))
        else:
            try:
                user = data["user"]
                self.user = self._state.get_user(int(user["id"])) or User(
                    state=self._state, data=user
                )
            except KeyError:
                pass

    @property
    def client(self) -> Client:
        """:class:`Client`: The client that handled the interaction."""
        return self._state._get_client()

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild the interaction was sent from."""
        return self._state and self._state._get_guild(self.guild_id)

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: An aware datetime in UTC representing the creation time of the interaction."""
        return snowflake_time(self.id)

    @property
    def expires_at(self) -> datetime:
        """:class:`datetime.datetime`: An aware datetime in UTC representing the time when the interaction will expire."""
        if self.response.is_done():
            return self.created_at + timedelta(minutes=15)
        else:
            return self.created_at + timedelta(seconds=3)

    def is_expired(self) -> bool:
        """:class:`bool` A boolean whether the interaction token is invalid or not."""
        return utils.utcnow() > self.expires_at

    def _set_application_command(
        self, app_cmd: Union[SlashApplicationSubcommand, BaseApplicationCommand]
    ):
        self.application_command = app_cmd

    @utils.cached_slot_property("_cs_channel")
    def channel(self) -> Optional[InteractionChannel]:
        """Optional[Union[:class:`abc.GuildChannel`, :class:`PartialMessageable`, :class:`Thread`]]: The channel the interaction was sent from.

        Note that due to a Discord limitation, DM channels are not resolved since there is
        no data to complete them. These are :class:`PartialMessageable` instead.
        """
        guild = self.guild
        channel = guild and guild._resolve_channel(self.channel_id)
        if channel is None:
            if self.channel_id is not None:
                type = ChannelType.text if self.guild_id is not None else ChannelType.private
                return PartialMessageable(state=self._state, id=self.channel_id, type=type)
            return None
        return channel

    @property
    def permissions(self) -> Permissions:
        """:class:`Permissions`: The resolved permissions of the member in the channel, including overwrites.

        In a non-guild context where this doesn't apply, an empty permissions object is returned.
        """
        return Permissions(self._permissions)

    @property
    def app_permissions(self) -> Permissions:
        """:class:`Permissions`: The resolved permissions of the bot in the channel, including overwrites.

        In a non-guild context where this doesn't apply, an empty permissions object is returned.
        """
        return Permissions(self._app_permissions)

    @utils.cached_slot_property("_cs_response")
    def response(self) -> InteractionResponse:
        """:class:`InteractionResponse`: Returns an object responsible for handling responding to the interaction.

        A response can only be done once. If secondary messages need to be sent, consider using :attr:`followup`
        instead.
        """
        return InteractionResponse(self)

    @utils.cached_slot_property("_cs_followup")
    def followup(self) -> Webhook:
        """:class:`Webhook`: Returns the follow up webhook for follow up interactions."""
        payload = {
            "id": self.application_id,
            "type": 3,
            "token": self.token,
        }
        return Webhook.from_state(data=payload, state=self._state)

    async def original_message(self) -> InteractionMessage:
        """|coro|

        Fetches the original interaction response message associated with the interaction.

        If the interaction response was :meth:`InteractionResponse.send_message` then this would
        return the message that was sent using that response. Otherwise, this would return
        the message that triggered the interaction.

        Repeated calls to this will return a cached value.

        Raises
        -------
        HTTPException
            Fetching the original response message failed.
        ClientException
            The channel for the message could not be resolved.

        Returns
        --------
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
        ------------
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
        -------
        HTTPException
            Editing the message failed.
        Forbidden
            Edited a message that is not yours.
        InvalidArgument
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``.
        ValueError
            The length of ``embeds`` was invalid.

        Returns
        --------
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
        if view and not view.is_finished():
            self._state.store_view(view, message.id)
        return message

    async def delete_original_message(self, *, delay: Optional[float] = None) -> None:
        """|coro|

        Deletes the original interaction response message.

        This is a lower level interface to :meth:`InteractionMessage.delete` in case
        you do not want to fetch the message and save an HTTP request.

        Parameters
        -----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait before deleting the message.
            The waiting is done in the background and deletion failures are ignored.

        Raises
        -------
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

            async def inner_call(delay: float = delay):
                await asyncio.sleep(delay)
                try:
                    await delete_func
                except HTTPException:
                    pass

            asyncio.create_task(inner_call())
        else:
            await delete_func

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
        ephemeral: bool = False,
        delete_after: Optional[float] = None,
        allowed_mentions: AllowedMentions = MISSING,
    ) -> Union[PartialInteractionMessage, WebhookMessage]:
        """|coro|

        This is a shorthand function for helping in sending messages in
        response to an interaction. If the interaction has not been responded to,
        :meth:`InteractionResponse.send_message` is used. If the response
        :meth:`~InteractionResponse.is_done` then the message is sent
        via :attr:`Interaction.followup` using :class:`Webhook.send` instead.

        Raises
        --------
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
            or :meth:`Interaction.original_message`.
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
        )

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
            return await self.message.edit(*args, **kwargs)
        raise InvalidArgument(
            "Interaction.message is None, this method can only be used in "
            "response to a component or modal submit interaction."
        )


class InteractionResponse:
    """Represents a Discord interaction response.

    This type can be accessed through :attr:`Interaction.response`.

    .. versionadded:: 2.0
    """

    __slots__: Tuple[str, ...] = (
        "_responded",
        "_parent",
    )

    def __init__(self, parent: Interaction):
        self._parent: Interaction = parent
        self._responded: bool = False

    def is_done(self) -> bool:
        """:class:`bool`: Indicates whether an interaction response has been done before.

        An interaction can only be responded to once.
        """
        return self._responded

    async def defer(self, *, ephemeral: bool = False, with_message: bool = False) -> None:
        """|coro|

        Defers the interaction response.

        This is typically used when the interaction is acknowledged
        and a secondary action will be done later.

        Parameters
        -----------
        ephemeral: :class:`bool`
            Indicates whether the deferred message will eventually be ephemeral.
            This only applies for interactions of type :attr:`InteractionType.application_command` or when ``with_message`` is True
        with_message: :class:`bool`
            Indicates whether the response will be a message with thinking state (bot is thinking...).
            This is always True for interactions of type :attr:`InteractionType.application_command`.
            For interactions of type :attr:`InteractionType.component` this defaults to False.

            .. versionadded:: 2.0

        Raises
        -------
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

    async def pong(self) -> None:
        """|coro|

        Pongs the ping interaction.

        This should rarely be used.

        Raises
        -------
        HTTPException
            Ponging the interaction failed.
        InteractionResponded
            This interaction has already been responded to before.
        """
        if self._responded:
            raise InteractionResponded(self._parent)

        parent = self._parent
        if parent.type is InteractionType.ping:
            adapter = async_context.get()
            await adapter.create_interaction_response(
                parent.id,
                parent.token,
                session=parent._session,
                type=InteractionResponseType.pong.value,
            )
            self._responded = True

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
        -------
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
        ephemeral: bool = False,
        delete_after: Optional[float] = None,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
    ) -> PartialInteractionMessage:
        """|coro|

        Responds to this interaction by sending a message.

        Parameters
        -----------
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

        Raises
        -------
        HTTPException
            Sending the message failed.
        NotFound
            The interaction has expired. :meth:`InteractionResponse.defer` and
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
        --------
        :class:`PartialInteractionMessage`
            An object supporting only the :meth:`~PartialInteractionMessage.edit` and :meth:`~PartialInteractionMessage.delete`
            operations. To fetch the :class:`InteractionMessage` you may use :meth:`PartialInteractionMessage.fetch`
            or :meth:`Interaction.original_message`.
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

        if ephemeral:
            payload["flags"] = 64

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

        if view is not MISSING:
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
        -------
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
        component or modal submit interaction originated from.

        Parameters
        -----------
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
            pass ``interaction.message.attachments``.
        view: Optional[:class:`~nextcord.ui.View`]
            The updated view to update this message with. If ``None`` is passed then
            the view is removed.
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.


        Raises
        -------
        HTTPException
            Editing the message failed.
        InvalidArgument
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``.
        TypeError
            An object not of type :class:`File` was passed to ``file`` or ``files``.
        InteractionResponded
            This interaction has already been responded to before.

        Returns
        --------
        Optional[:class:`Message`]
            The message that was edited, or None if the :attr:`Interaction.message` is not found
            (this may happen if the interaction occurred in a :class:`Thread`).
        """
        if self._responded:
            raise InteractionResponded(self._parent)

        parent = self._parent
        msg = parent.message
        state = parent._state
        message_id = msg.id if msg else None

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

        if view and not view.is_finished() and message_id is not None:
            state.store_view(view, message_id)

        self._responded = True

        if delete_after is not None:
            await parent.delete_original_message(delay=delete_after)

        return state._get_message(message_id)


class _InteractionMessageState:
    __slots__ = ("_parent", "_interaction")

    def __init__(self, interaction: Interaction, parent: ConnectionState):
        self._interaction: Interaction = interaction
        self._parent: ConnectionState = parent

    def _get_guild(self, guild_id):
        return self._parent._get_guild(guild_id)

    def store_user(self, data):
        return self._parent.store_user(data)

    def create_user(self, data):
        return self._parent.create_user(data)

    @property
    def http(self):
        return self._parent.http

    def __getattr__(self, attr):
        return getattr(self._parent, attr)


class _InteractionMessageMixin:
    __slots__ = ()
    _state: _InteractionMessageState

    async def edit(
        self,
        content: Optional[str] = MISSING,
        embeds: List[Embed] = MISSING,
        embed: Optional[Embed] = MISSING,
        file: File = MISSING,
        files: List[File] = MISSING,
        attachments: List[Attachment] = MISSING,
        view: Optional[View] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None,
        delete_after: Optional[float] = None,
    ) -> InteractionMessage:
        """|coro|

        Edits the message.

        Parameters
        ------------
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
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just edited. If the deletion fails,
            then it is silently ignored.

        Raises
        -------
        HTTPException
            Editing the message failed.
        Forbidden
            Edited a message that is not yours.
        InvalidArgument
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``.
        ValueError
            The length of ``embeds`` was invalid.

        Returns
        ---------
        :class:`InteractionMessage`
            The newly edited message.
        """
        message = await self._state._interaction.edit_original_message(
            content=content,
            embeds=embeds,
            embed=embed,
            file=file,
            files=files,
            attachments=attachments,
            view=view,
            allowed_mentions=allowed_mentions,
        )

        if delete_after is not None:
            await self.delete(delay=delete_after)

        return message

    async def delete(self, *, delay: Optional[float] = None) -> None:
        """|coro|

        Deletes the message.

        Parameters
        -----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait before deleting the message.
            The waiting is done in the background and deletion failures are ignored.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the message.
        NotFound
            The message was deleted already.
        HTTPException
            Deleting the message failed.
        """

        await self._state._interaction.delete_original_message(delay=delay)


class PartialInteractionMessage(_InteractionMessageMixin):
    """Represents the original interaction response message when only the
    application state and interaction token are available.

    This allows you to edit or delete the message associated with
    the interaction response. This object is returned when responding to
    an interaction with :meth:`InteractionResponse.send_message`.

    This does not support most attributes and methods of :class:`nextcord.Message`.
    The :meth:`~PartialInteractionMessage.fetch` method can be used to
    retrieve the full :class:`InteractionMessage` object.

    .. container:: operations

        .. describe:: x == y

            Checks if two partial interaction messages are equal.

        .. describe:: x != y

            Checks if two partial interaction messages are not equal.

        .. describe:: hash(x)

            Returns the partial interaction message's hash.

    .. versionadded:: 2.0

    .. versionchanged:: 2.1
        :class:`PartialInteractionMessage` is now hashable by :attr:`Interaction.id`.

    .. note::
        The hash of a :class:`PartialInteractionMessage` is the same as the hash of the
        :class:`Interaction` that it is associated with but not that of the full :class:`InteractionMessage`.
    """

    def __init__(self, state: _InteractionMessageState):
        self._state = state

    async def fetch(self) -> InteractionMessage:
        """|coro|

        Fetches the original interaction response message associated with the interaction.

        Repeated calls to this will return a cached value.

        Raises
        -------
        HTTPException
            Fetching the original response message failed.
        ClientException
            The channel for the message could not be resolved.

        Returns
        --------
        InteractionMessage
            The original interaction response message.
        """
        return await self._state._interaction.original_message()

    @property
    def author(self) -> Optional[Union[Member, ClientUser]]:
        """Optional[Union[:class:`Member`, :class:`ClientUser`]]: The client that responded to the interaction.

        If the interaction was in a guild, this is a :class:`Member` representing the client.
        Otherwise, this is a :class:`ClientUser`.
        """
        return self.guild.me if self.guild else self._state._interaction.client.user

    @property
    def channel(self) -> Optional[InteractionChannel]:
        """Optional[Union[:class:`abc.GuildChannel`, :class:`PartialMessageable`, :class:`Thread`]]: The channel the interaction was sent from.

        Note that due to a Discord limitation, DM channels are not resolved since there is
        no data to complete them. These are :class:`PartialMessageable` instead.
        """
        return self._state._interaction.channel

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild the interaction was sent from."""
        return self._state._interaction.guild

    def __repr__(self):
        return f"<{self.__class__.__name__} author={self.author!r} channel={self.channel!r} guild={self.guild!r}>"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, PartialInteractionMessage)
            and self._state._interaction == other._state._interaction
        )

    def __ne__(self, other: object) -> bool:
        if isinstance(other, PartialInteractionMessage):
            return self._state._interaction != other._state._interaction
        return True

    def __hash__(self) -> int:
        return hash(self._state._interaction)


class InteractionMessage(_InteractionMessageMixin, Message):
    """Represents the original interaction response message.

    To retrieve this object see :meth:`PartialInteractionMessage.fetch`
    or :meth:`Interaction.original_message`.

    This inherits from :class:`nextcord.Message` with changes to
    :meth:`edit` and :meth:`delete` to work with the interaction response.

    .. versionadded:: 2.0
    """

    pass
