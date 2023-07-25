# SPDX-License-Identifier: MIT

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Generic, List, Optional, Tuple, TypeVar, Union

from .. import utils
from ..channel import ChannelType, PartialMessageable
from ..embeds import Embed
from ..enums import InteractionType, try_enum
from ..file import File
from ..member import Member
from ..message import Attachment, Message
from ..mixins import Hashable
from ..object import Object
from ..permissions import Permissions
from ..user import ClientUser, User
from ..utils import snowflake_time
from ..webhook.async_ import Webhook

__all__ = ("Interaction", "InteractionMessage", "InteractionResponse", "PartialInteractionMessage")

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from ..channel import CategoryChannel, ForumChannel, StageChannel, TextChannel, VoiceChannel
    from ..client import Client
    from ..guild import Guild
    from ..message import AllowedMentions
    from ..state import ConnectionState
    from ..threads import Thread
    from ..types.interactions import InteractionData, InteractionPayload
    from ..ui.view import View
    from .application import ApplicationCommandInteraction
    from .message_component import MessageComponentInteraction
    from .modal_submit import ModalSubmitInteraction

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

ClientT = TypeVar("ClientT", bound="Client")


class InteractionAttached(dict):
    """Represents the attached data of an interaction.

    This is used to store information about an :class:`Interaction`. This is useful if you want to save some data from a :meth:`ApplicationCommand.application_command_before_invoke` to use later in the callback.

    Example
    -------

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

    def __init__(self) -> None:
        super().__init__()
        self.__dict__ = self

    def __repr__(self) -> str:
        return f"<InteractionAttached {super().__repr__()}>"


class Interaction(Hashable, Generic[ClientT]):
    """The base class for all Discord interactions.

    An interaction happens when a user does an action that needs to
    be notified. Current examples are slash commands and components.

    .. container:: operations

        .. describe:: x == y

            Checks if two interactions are equal.

        .. describe:: x != y

            Checks if two interactions are not equal.

        .. describe:: hash(x)

            Returns the interaction's hash.

    Attributes
    ----------
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
    token: :class:`str`
        The token to continue the interaction. These are valid
        for 15 minutes.
    data: :class:`dict`
        The raw data for an option. See https://discord.com/developers/docs/interactions/receiving-and-responding#interaction-object-interaction-data for more information.
    attached: :class:`InteractionAttached`
        The attached data of the interaction. This is used to store any data you may need inside the interaction for convenience. This data will stay on the interaction, even after a :meth:`Interaction.application_command_before_invoke`.
    """

    __slots__: Tuple[str, ...] = (
        "id",
        "type",
        "guild_id",
        "channel_id",
        "data",
        "application_id",
        "user",
        "locale",
        "guild_locale",
        "token",
        "version",
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

    def __init__(self, *, data: InteractionPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self._session: ClientSession = state.http._HTTPClient__session  # type: ignore
        # TODO: this is so janky, accessing a hidden double attribute
        self._original_message: Optional[InteractionMessage] = None
        self.attached = InteractionAttached()
        self._from_data(data)

    def _from_data(self, data: InteractionPayload) -> None:
        self.id: int = int(data["id"])
        self.type: InteractionType = try_enum(InteractionType, data["type"])
        self.data: Optional[InteractionData] = data.get("data")
        self.token: str = data["token"]
        self.version: int = data["version"]
        self.channel_id: Optional[int] = utils.get_as_snowflake(data, "channel_id")
        self.guild_id: Optional[int] = utils.get_as_snowflake(data, "guild_id")
        self.application_id: int = int(data["application_id"])
        self.locale: Optional[str] = data.get("locale")
        self.guild_locale: Optional[str] = data.get("guild_locale")
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
    def client(self) -> ClientT:
        """:class:`Client`: The client that handled the interaction."""
        return self._state._get_client()  # type: ignore

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


class InteractionResponse:
    """Represents a Discord interaction response.

    This type can be accessed through :attr:`Interaction.response`.

    .. versionadded:: 2.0
    """

    __slots__: Tuple[str, ...] = (
        "_responded",
        "_parent",
    )

    def __init__(self, parent: Interaction) -> None:
        self._parent: Interaction = parent
        self._responded: bool = False

    def is_done(self) -> bool:
        """:class:`bool`: Indicates whether an interaction response has been done before.

        An interaction can only be responded to once.
        """
        return self._responded


class _InteractionMessageState:
    __slots__ = ("_parent", "_interaction")

    def __init__(self, interaction: Union[MessageComponentInteraction, ModalSubmitInteraction, ApplicationCommandInteraction], parent: ConnectionState) -> None:
        self._interaction: Union[MessageComponentInteraction, ModalSubmitInteraction, ApplicationCommandInteraction] = interaction
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
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just edited. If the deletion fails,
            then it is silently ignored.

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
        ----------
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

    def __init__(self, state: _InteractionMessageState) -> None:
        self._state = state

    async def fetch(self) -> InteractionMessage:
        """|coro|

        Fetches the original interaction response message associated with the interaction.

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

    def __repr__(self) -> str:
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
