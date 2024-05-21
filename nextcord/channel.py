# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
import datetime
import time
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from . import abc, ui, utils
from .asset import Asset
from .emoji import Emoji
from .enums import (
    ChannelType,
    ForumLayoutType,
    SortOrderType,
    StagePrivacyLevel,
    VideoQualityMode,
    VoiceRegion,
    try_enum,
)
from .errors import ClientException, InvalidArgument
from .file import File
from .flags import ChannelFlags, MessageFlags
from .iterators import ArchivedThreadIterator
from .mentions import AllowedMentions
from .mixins import Hashable, PinsMixin
from .object import Object
from .partial_emoji import PartialEmoji
from .permissions import PermissionOverwrite, Permissions
from .stage_instance import StageInstance
from .threads import Thread
from .utils import MISSING

__all__ = (
    "TextChannel",
    "VoiceChannel",
    "StageChannel",
    "DMChannel",
    "CategoryChannel",
    "GroupChannel",
    "PartialMessageable",
    "ForumChannel",
    "ForumTag",
)

if TYPE_CHECKING:
    from typing_extensions import Self

    from .abc import Snowflake, SnowflakeTime
    from .embeds import Embed
    from .guild import Guild, GuildChannel as GuildChannelType
    from .member import Member, VoiceState
    from .message import Attachment, Message, PartialMessage
    from .role import Role
    from .state import ConnectionState
    from .sticker import GuildSticker, StickerItem
    from .types.channel import (
        CategoryChannel as CategoryChannelPayload,
        DMChannel as DMChannelPayload,
        ForumChannel as ForumChannelPayload,
        ForumTag as ForumTagPayload,
        GroupDMChannel as GroupChannelPayload,
        StageChannel as StageChannelPayload,
        TextChannel as TextChannelPayload,
        VoiceChannel as VoiceChannelPayload,
    )
    from .types.snowflake import SnowflakeList
    from .types.threads import ThreadArchiveDuration
    from .user import BaseUser, ClientUser, User
    from .webhook import Webhook


async def _single_delete_strategy(messages: Iterable[Message]) -> None:
    for m in messages:
        await m.delete()


class TextChannel(abc.Messageable, abc.GuildChannel, Hashable, PinsMixin):
    """Represents a Discord guild text channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    ----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    topic: Optional[:class:`str`]
        The channel's topic. ``None`` if it doesn't exist.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this channel. A value of ``0`` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    flags: :class:`ChannelFlags`
        Extra features of the channel.

        ..versionadded:: 2.1
    nsfw: :class:`bool`
        If the channel is marked as "not safe for work".

        .. note::

            To check if the channel or the guild of that channel are marked as NSFW, consider :meth:`is_nsfw` instead.
    default_auto_archive_duration: :class:`int`
        The default auto archive duration in minutes for threads created in this channel.

        .. versionadded:: 2.0
    default_thread_slowmode_delay: :class:`int`
        The default amount of seconds a user has to wait
        before creating another thread in this channel.
        This is set on every new thread in this channel.

        .. versionadded:: 2.4
    """

    __slots__ = (
        "name",
        "id",
        "guild",
        "topic",
        "_state",
        "nsfw",
        "category_id",
        "position",
        "slowmode_delay",
        "_overwrites",
        "_type",
        "last_message_id",
        "default_auto_archive_duration",
        "flags",
        "default_thread_slowmode_delay",
    )

    def __init__(self, *, state: ConnectionState, guild: Guild, data: TextChannelPayload) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data["id"])
        self._type: int = data["type"]
        self._update(guild, data)

    def __repr__(self) -> str:
        attrs = [
            ("id", self.id),
            ("name", self.name),
            ("position", self.position),
            ("nsfw", self.nsfw),
            ("news", self.is_news()),
            ("category_id", self.category_id),
        ]
        joined = " ".join("%s=%r" % t for t in attrs)
        return f"<{self.__class__.__name__} {joined}>"

    def _update(self, guild: Guild, data: TextChannelPayload) -> None:
        self.guild: Guild = guild
        self.name: str = data["name"]
        self.category_id: Optional[int] = utils.get_as_snowflake(data, "parent_id")
        self.topic: Optional[str] = data.get("topic")
        self.position: int = data["position"]
        self.nsfw: bool = data.get("nsfw", False)
        # Does this need coercion into `int`? No idea yet.
        self.slowmode_delay: int = data.get("rate_limit_per_user", 0)
        self.default_auto_archive_duration: ThreadArchiveDuration = data.get(
            "default_auto_archive_duration", 1440
        )
        self.flags: ChannelFlags = ChannelFlags._from_value(data.get("flags", 0))
        self._type: int = data.get("type", self._type)
        self.last_message_id: Optional[int] = utils.get_as_snowflake(data, "last_message_id")
        self.default_thread_slowmode_delay: int = data.get("default_thread_slowmode_delay", 0)
        self._fill_overwrites(data)

    async def _get_channel(self):
        return self

    @property
    def type(self) -> ChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return try_enum(ChannelType, self._type)

    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.text.value

    @utils.copy_doc(abc.GuildChannel.permissions_for)
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        base = super().permissions_for(obj)

        # text channels do not have voice related permissions
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base

    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: Returns all members that can see this channel."""
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]

    @property
    def threads(self) -> List[Thread]:
        """List[:class:`Thread`]: Returns all the threads that you can see.

        .. versionadded:: 2.0
        """
        return [thread for thread in self.guild._threads.values() if thread.parent_id == self.id]

    def is_nsfw(self) -> bool:
        """:class:`bool`: Checks if the channel is NSFW."""
        return self.nsfw

    def is_news(self) -> bool:
        """:class:`bool`: Checks if the channel is a news channel."""
        return self._type == ChannelType.news.value

    @property
    def last_message(self) -> Optional[Message]:
        """Fetches the last message from this channel in cache.

        The message might not be valid or point to an existing message.

        .. admonition:: Reliable Fetching
            :class: helpful

            For a slightly more reliable method of fetching the
            last message, consider using either :meth:`history`
            or :meth:`fetch_message` with the :attr:`last_message_id`
            attribute.

        Returns
        -------
        Optional[:class:`Message`]
            The last message in this channel or ``None`` if not found.
        """
        return self._state._get_message(self.last_message_id) if self.last_message_id else None

    @overload
    async def edit(
        self,
        *,
        reason: Optional[str] = ...,
        name: str = ...,
        topic: str = ...,
        position: int = ...,
        nsfw: bool = ...,
        sync_permissions: bool = ...,
        category: Optional[CategoryChannel] = ...,
        slowmode_delay: int = ...,
        default_auto_archive_duration: ThreadArchiveDuration = ...,
        type: ChannelType = ...,
        overwrites: Mapping[Union[Role, Member, Snowflake], PermissionOverwrite] = ...,
        flags: ChannelFlags = ...,
        default_thread_slowmode_delay: int = ...,
    ) -> Optional[TextChannel]:
        ...

    @overload
    async def edit(self) -> Optional[TextChannel]:
        ...

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        .. versionchanged:: 1.3
            The ``overwrites`` keyword-only parameter was added.

        .. versionchanged:: 1.4
            The ``type`` keyword-only parameter was added.

        .. versionchanged:: 2.0
            Edits are no longer in-place, the newly edited channel is returned instead.

        Parameters
        ----------
        name: :class:`str`
            The new channel name.
        topic: :class:`str`
            The new channel's topic.
        position: :class:`int`
            The new channel's position.
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing
            category. Defaults to ``False``.
        category: Optional[:class:`CategoryChannel`]
            The new category for this channel. Can be ``None`` to remove the
            category.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
            A value of ``0`` disables slowmode. The maximum value possible is ``21600``.
        type: :class:`ChannelType`
            Change the type of this text channel. Currently, only conversion between
            :attr:`ChannelType.text` and :attr:`ChannelType.news` is supported. This
            is only available to guilds that contain ``NEWS`` in :attr:`Guild.features`.
        reason: Optional[:class:`str`]
            The reason for editing this channel. Shows up on the audit log.
        overwrites: :class:`Mapping`
            A :class:`Mapping` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply to the channel.
        default_auto_archive_duration: :class:`int`
            The new default auto archive duration in minutes for threads created in this channel.
            Must be one of ``60``, ``1440``, ``4320``, or ``10080``.
        default_thread_slowmode_delay: :class:`int`
            The new default rate limit per user for threads created in this channel.
            This sets a new default but does not change the rate limits of existing threads.

            .. versionadded:: 2.4

        Raises
        ------
        InvalidArgument
            If position is less than 0 or greater than the number of channels, or if
            the permission overwrite information is not in proper form.
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.

        Returns
        -------
        Optional[:class:`.TextChannel`]
            The newly edited text channel. If the edit was only positional
            then ``None`` is returned instead.
        """

        payload = await self._edit(options, reason=reason)
        if payload is not None:
            # the payload will always be the proper channel payload
            return self.__class__(state=self._state, guild=self.guild, data=payload)  # type: ignore
        return None

    @utils.copy_doc(abc.GuildChannel.clone)
    async def clone(
        self, *, name: Optional[str] = None, reason: Optional[str] = None
    ) -> TextChannel:
        return await self._clone_impl(
            {"topic": self.topic, "nsfw": self.nsfw, "rate_limit_per_user": self.slowmode_delay},
            name=name,
            reason=reason,
        )

    async def delete_messages(self, messages: Iterable[Snowflake]) -> None:
        """|coro|

        Deletes a list of messages. This is similar to :meth:`Message.delete`
        except it bulk deletes multiple messages.

        As a special case, if the number of messages is 0, then nothing
        is done. If the number of messages is 1 then single message
        delete is done. If it's more than two, then bulk delete is used.

        You cannot bulk delete more than 100 messages or messages that
        are older than 14 days old.

        You must have the :attr:`~Permissions.manage_messages` permission to
        use this.

        Parameters
        ----------
        messages: Iterable[:class:`abc.Snowflake`]
            An iterable of messages denoting which ones to bulk delete.

        Raises
        ------
        ClientException
            The number of messages to delete was more than 100.
        Forbidden
            You do not have proper permissions to delete the messages.
        NotFound
            If single delete, then the message was already deleted.
        HTTPException
            Deleting the messages failed.
        """
        if not isinstance(messages, (list, tuple)):
            messages = list(messages)

        if len(messages) == 0:
            return  # do nothing

        if len(messages) == 1:
            message_id: int = messages[0].id
            await self._state.http.delete_message(self.id, message_id)
            return

        if len(messages) > 100:
            raise ClientException("Can only bulk delete messages up to 100 messages")

        message_ids: SnowflakeList = [m.id for m in messages]
        await self._state.http.delete_messages(self.id, message_ids)

    async def purge(
        self,
        *,
        limit: Optional[int] = 100,
        check: Callable[[Message], bool] = MISSING,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        around: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = False,
        bulk: bool = True,
    ) -> List[Message]:
        """|coro|

        Purges a list of messages that meet the criteria given by the predicate
        ``check``. If a ``check`` is not provided then all messages are deleted
        without discrimination.

        You must have the :attr:`~Permissions.manage_messages` permission to
        delete messages even if they are your own.
        The :attr:`~Permissions.read_message_history` permission is
        also needed to retrieve message history.

        Examples
        --------

        Deleting bot's messages ::

            def is_me(m):
                return m.author == client.user

            deleted = await channel.purge(limit=100, check=is_me)
            await channel.send(f'Deleted {len(deleted)} message(s)')

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of messages to search through. This is not the number
            of messages that will be deleted, though it can be.
        check: Callable[[:class:`Message`], :class:`bool`]
            The function used to check if a message should be deleted.
            It must take a :class:`Message` as its sole parameter.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``before`` in :meth:`history`.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``after`` in :meth:`history`.
        around: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``around`` in :meth:`history`.
        oldest_first: Optional[:class:`bool`]
            Same as ``oldest_first`` in :meth:`history`.
        bulk: :class:`bool`
            If ``True``, use bulk delete. Setting this to ``False`` is useful for mass-deleting
            a bot's own messages without :attr:`Permissions.manage_messages`. When ``True``, will
            fall back to single delete if messages are older than two weeks.

        Raises
        ------
        Forbidden
            You do not have proper permissions to do the actions required.
        HTTPException
            Purging the messages failed.

        Returns
        -------
        List[:class:`.Message`]
            The list of messages that were deleted.
        """

        if check is MISSING:
            check = lambda _: True

        iterator = self.history(
            limit=limit, before=before, after=after, oldest_first=oldest_first, around=around
        )
        ret: List[Message] = []
        count = 0

        minimum_time = int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
        strategy = self.delete_messages if bulk else _single_delete_strategy

        async for message in iterator:
            if count == 100:
                to_delete = ret[-100:]
                await strategy(to_delete)
                count = 0
                await asyncio.sleep(1)

            if not check(message):
                continue

            if message.id < minimum_time:
                # older than 14 days old
                if count == 1:
                    await ret[-1].delete()
                elif count >= 2:
                    to_delete = ret[-count:]
                    await strategy(to_delete)

                count = 0
                strategy = _single_delete_strategy

            count += 1
            ret.append(message)

        # Some messages remaining to poll
        if count >= 2:
            # more than 2 messages -> bulk delete
            to_delete = ret[-count:]
            await strategy(to_delete)
        elif count == 1:
            # delete a single message
            await ret[-1].delete()

        return ret

    async def webhooks(self) -> List[Webhook]:
        """|coro|

        Gets the list of webhooks from this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        Raises
        ------
        Forbidden
            You don't have permissions to get the webhooks.

        Returns
        -------
        List[:class:`Webhook`]
            The webhooks for this channel.
        """

        from .webhook import Webhook

        data = await self._state.http.channel_webhooks(self.id)
        return [Webhook.from_state(d, state=self._state) for d in data]

    async def create_webhook(
        self,
        *,
        name: str,
        avatar: Optional[Union[bytes, Asset, Attachment, File]] = None,
        reason: Optional[str] = None,
    ) -> Webhook:
        """|coro|

        Creates a webhook for this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        .. versionchanged:: 1.1
            Added the ``reason`` keyword-only parameter.

        .. versionchanged:: 2.1
            The ``avatar`` parameter now accepts :class:`File`, :class:`Attachment`, and :class:`Asset`.

        Parameters
        ----------
        name: :class:`str`
            The webhook's name.
        avatar: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`,
            or :class:`Asset` representing the webhook's default avatar.
            This operates similarly to :meth:`~ClientUser.edit`.
        reason: Optional[:class:`str`]
            The reason for creating this webhook. Shows up in the audit logs.

        Raises
        ------
        HTTPException
            Creating the webhook failed.
        Forbidden
            You do not have permissions to create a webhook.

        Returns
        -------
        :class:`Webhook`
            The created webhook.
        """

        from .webhook import Webhook

        avatar_base64 = await utils.obj_to_base64_data(avatar)

        data = await self._state.http.create_webhook(
            self.id, name=str(name), avatar=avatar_base64, reason=reason
        )
        return Webhook.from_state(data, state=self._state)

    async def follow(self, *, destination: TextChannel, reason: Optional[str] = None) -> Webhook:
        """
        Follows a channel using a webhook.

        Only news channels can be followed.

        .. note::

            The webhook returned will not provide a token to do webhook
            actions, as Discord does not provide it.

        .. versionadded:: 1.3

        Parameters
        ----------
        destination: :class:`TextChannel`
            The channel you would like to follow from.
        reason: Optional[:class:`str`]
            The reason for following the channel. Shows up on the destination guild's audit log.

            .. versionadded:: 1.4

        Raises
        ------
        HTTPException
            Following the channel failed.
        Forbidden
            You do not have the permissions to create a webhook.

        Returns
        -------
        :class:`Webhook`
            The created webhook.
        """

        if not self.is_news():
            raise ClientException("The channel must be a news channel.")

        if not isinstance(destination, TextChannel):
            raise InvalidArgument(f"Expected TextChannel received {destination.__class__.__name__}")

        from .webhook import Webhook

        data = await self._state.http.follow_webhook(
            self.id, webhook_channel_id=destination.id, reason=reason
        )
        return Webhook._as_follower(data, channel=destination, user=self._state.user)

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        .. versionadded:: 1.6

        Parameters
        ----------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        -------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)

    def get_thread(self, thread_id: int, /) -> Optional[Thread]:
        """Returns a thread with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        thread_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Thread`]
            The returned thread or ``None`` if not found.
        """
        return self.guild.get_thread(thread_id)

    async def create_thread(
        self,
        *,
        name: str,
        message: Optional[Snowflake] = None,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
        type: Optional[
            Literal[ChannelType.news_thread, ChannelType.public_thread, ChannelType.private_thread]
        ] = None,
        invitable: bool = True,
        reason: Optional[str] = None,
    ) -> Thread:
        """|coro|

        Creates a thread in this text channel.

        To create a public thread, you must have :attr:`~nextcord.Permissions.create_public_threads`.
        For a private thread, :attr:`~nextcord.Permissions.create_private_threads` is needed instead.

        .. versionadded:: 2.0

        Parameters
        ----------
        name: :class:`str`
            The name of the thread.
        message: Optional[:class:`abc.Snowflake`]
            A snowflake representing the message to create the thread with.
            If ``None`` is passed then a private thread is created.
            Defaults to ``None``.
        auto_archive_duration: :class:`int`
            The duration in minutes before a thread is automatically archived for inactivity.
            If not provided, the channel's default auto archive duration is used.
        type: Optional[:class:`ChannelType`]
            The type of thread to create. If a ``message`` is passed then this parameter
            is ignored, as a thread created with a message is always a public thread.
            By default this creates a private thread if this is ``None``.
        invitable: :class:`bool`
            Whether non-moderators can add other non-moderators to this thread.
            Only available for private threads and threads created without a ``message``.
        reason: :class:`str`
            The reason for creating a new thread. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have permissions to create a thread.
        HTTPException
            Starting the thread failed.

        Returns
        -------
        :class:`Thread`
            The created thread
        """

        if type is None:
            type = ChannelType.private_thread

        if message is None:
            data = await self._state.http.start_thread_without_message(
                self.id,
                name=name,
                auto_archive_duration=auto_archive_duration or self.default_auto_archive_duration,
                type=type.value,
                invitable=invitable,
                reason=reason,
            )
        else:
            data = await self._state.http.start_thread_with_message(
                self.id,
                message.id,
                name=name,
                auto_archive_duration=auto_archive_duration or self.default_auto_archive_duration,
                reason=reason,
            )

        return Thread(guild=self.guild, state=self._state, data=data)

    def archived_threads(
        self,
        *,
        private: bool = False,
        joined: bool = False,
        limit: Optional[int] = 50,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
    ) -> ArchivedThreadIterator:
        """Returns an :class:`~nextcord.AsyncIterator` that iterates over all archived threads in the guild.

        You must have :attr:`~Permissions.read_message_history` to use this. If iterating over private threads
        then :attr:`~Permissions.manage_threads` is also required.

        .. versionadded:: 2.0

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of threads to retrieve.
            If ``None``, retrieves every archived thread in the channel. Note, however,
            that this would make it a slow operation.
            This defaults to ``50``.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve archived channels before the given date or ID.
        private: :class:`bool`
            Whether to retrieve private archived threads.
            This defaults to ``False``.
        joined: :class:`bool`
            Whether to retrieve private archived threads that you've joined.
            This defaults to ``False``.

            .. warning::

                You cannot set ``joined`` to ``True`` and ``private`` to ``False``.

        Raises
        ------
        Forbidden
            You do not have permissions to get archived threads.
        HTTPException
            The request to get the archived threads failed.

        Yields
        ------
        :class:`Thread`
            The archived threads.
        """

        return ArchivedThreadIterator(
            self.id, self.guild, limit=limit, joined=joined, private=private, before=before
        )


class ForumChannel(abc.GuildChannel, Hashable):
    """Represents a Discord guild forum channel.

    .. versionadded:: 2.1

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    ----------
    id: :class:`int`
        The snowflake ID of this channel.
    guild: :class:`Guild`
        The guild this channel belongs to.
    name: :class:`str`
        The name of this channel.
    category_id: Optional[:class:`int`]
        The ID of the :class:`CategoryChannel` this channel belongs to, if any.
    topic: :class:`str`
        The topic of this channel, if any. This is what is shown in the "Guidelines" section visually.
    position: :class:`int`
        The position in the channel list, where the first channel is ``0``.
    nsfw: :class:`bool`
        If this channel is marked as NSFW.
    slowmode_delay: :class:`int`
        The delay in seconds which members must wait between sending messages.
    flags: :class:`ChannelFlags`
        The flags that detail features of this channel.
    default_auto_archive_duration: :class:`int`
        The archive duration which threads from this channel inherit by default.
    last_message_id: :class:`int`
        The snowflake ID of the message starting the last thread in this channel.
    default_sort_order: :class:`SortOrderType`
        The default sort order type used to sort posts in forum channels.

        .. versionadded:: 2.3
    default_forum_layout: :class:`ForumLayoutType`
        The default layout type used to display posts in this forum.

        .. versionadded:: 2.4
    default_thread_slowmode_delay: :class:`int`
        The default amount of seconds a user has to wait
        before creating another thread in this channel.
        This is set on every new thread in this channel.

        .. versionadded:: 2.4
    default_reaction: Optional[:class:`PartialEmoji`]
        The emoji that is used to add a reaction to every post in this forum.

        .. versionadded:: 2.4
    """

    __slots__ = (
        "id",
        "guild",
        "name",
        "category_id",
        "position",
        "topic",
        "nsfw",
        "flags",
        "slowmode_delay",
        "default_auto_archive_duration",
        "last_message_id",
        "default_sort_order",
        "default_forum_layout",
        "_state",
        "_type",
        "_overwrites",
        "default_thread_slowmode_delay",
        "_available_tags",
        "default_reaction",
    )

    def __init__(self, *, state: ConnectionState, guild: Guild, data: ForumChannelPayload) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data["id"])
        self._type: int = data["type"]
        self._update(guild, data)

    def _update(self, guild: Guild, data: ForumChannelPayload) -> None:
        self.guild = guild
        self.name = data["name"]
        self.category_id: Optional[int] = utils.get_as_snowflake(data, "parent_id")
        self.topic: Optional[str] = data.get("topic")
        self.position: int = data["position"]
        self.nsfw: bool = data.get("nsfw", False)
        # Does this need coercion into `int`? No idea yet.
        self.slowmode_delay: int = data.get("rate_limit_per_user", 0)
        self.flags: ChannelFlags = ChannelFlags._from_value(data.get("flags", 0))
        self.default_auto_archive_duration: ThreadArchiveDuration = data.get(
            "default_auto_archive_duration", 1440
        )

        self.last_message_id: Optional[int] = utils.get_as_snowflake(data, "last_message_id")
        self.default_forum_layout: ForumLayoutType = try_enum(
            ForumLayoutType, data.get("default_forum_layout", 0)
        )

        if sort_order := data.get("default_sort_order"):
            self.default_sort_order: Optional[SortOrderType] = try_enum(SortOrderType, sort_order)
        else:
            self.default_sort_order: Optional[SortOrderType] = None

        self.default_thread_slowmode_delay: Optional[int] = data.get(
            "default_thread_slowmode_delay"
        )
        self._available_tags: Dict[int, ForumTag] = {
            int(tag["id"]): ForumTag.from_data(tag) for tag in data.get("available_tags", [])
        }

        self.default_reaction: Optional[PartialEmoji]

        reaction = data.get("default_reaction_emoji")
        if reaction is None:
            self.default_reaction = None
        else:
            self.default_reaction = PartialEmoji.from_default_reaction(reaction)

        self._fill_overwrites(data)

    async def _get_channel(self):
        return self

    @property
    def type(self) -> ChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return try_enum(ChannelType, self._type)

    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.text.value

    @utils.copy_doc(abc.GuildChannel.permissions_for)
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        base = super().permissions_for(obj)

        # forum channels do not have voice related permissions
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base

    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: Returns all members that can see this channel."""
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]

    @property
    def threads(self) -> List[Thread]:
        """List[:class:`Thread`]: Returns all the threads of this channel."""
        return [thread for thread in self.guild._threads.values() if thread.parent_id == self.id]

    def is_nsfw(self) -> bool:
        """:class:`bool`: Checks if the channel is NSFW."""
        return self.nsfw

    @property
    def last_message(self) -> Optional[Message]:
        """Fetches the message that started the last thread from this channel in cache.

        The message might not be valid or point to an existing message.

        .. admonition:: Reliable Fetching
            :class: helpful

            For a slightly more reliable method of fetching the
            last message, consider using either :meth:`history`
            or :meth:`fetch_message` with the :attr:`last_message_id`
            attribute.

        Returns
        -------
        Optional[:class:`Message`]
            The message that started the last thread in this channel or ``None`` if not found.
        """
        return self._state._get_message(self.last_message_id) if self.last_message_id else None

    @property
    def available_tags(self) -> List[ForumTag]:
        """List[:class:`ForumTag`]: Returns all the tags available in this channel.

        .. versionadded:: 2.4
        """

        return list(self._available_tags.values())

    def get_tag(self, id: int, /) -> Optional[ForumTag]:
        """Returns a tag from this channel by its ID.

        .. versionadded:: 2.4

        Parameters
        ----------
        id: :class:`int`
            The ID of the tag to get from cache.

        Returns
        -------
        Optional[:class:`ForumTag`]
            The tag with the given ID or ``None`` if not found.
        """

        return self._available_tags.get(id)

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        topic: str = ...,
        position: int = ...,
        nsfw: bool = ...,
        sync_permissions: bool = ...,
        category: Optional[CategoryChannel] = ...,
        slowmode_delay: int = ...,
        default_auto_archive_duration: ThreadArchiveDuration = ...,
        overwrites: Mapping[Union[Role, Member, Snowflake], PermissionOverwrite] = ...,
        flags: ChannelFlags = ...,
        reason: Optional[str] = ...,
        default_sort_order: Optional[SortOrderType] = ...,
        default_forum_layout: ForumLayoutType = ...,
        default_thread_slowmode_delay: int = ...,
        available_tags: List[ForumTag] = ...,
        default_reaction: Optional[Union[Emoji, PartialEmoji, str]] = ...,
    ) -> ForumChannel:
        ...

    @overload
    async def edit(self) -> ForumChannel:
        ...

    async def edit(self, *, reason=None, **options) -> ForumChannel:
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        Parameters
        ----------
        name: :class:`str`
            The new channel name.
        topic: :class:`str`
            The new channel's topic.
        position: :class:`int`
            The new channel's position.
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing
            category. Defaults to ``False``.
        category: Optional[:class:`CategoryChannel`]
            The new category for this channel. Can be ``None`` to remove the
            category.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
            A value of ``0`` disables slowmode. The maximum value possible is ``21600``.
        reason: Optional[:class:`str`]
            The reason for editing this channel. Shows up on the audit log.
        overwrites: :class:`Mapping`
            A :class:`Mapping` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply to the channel.
        default_auto_archive_duration: :class:`int`
            The new default auto archive duration in minutes for threads created in this channel.
            Must be one of ``60``, ``1440``, ``4320``, or ``10080``.
        flags: :class:`ChannelFlags`
            The new channel flags.

            .. versionadded:: 2.1
        default_sort_order: :class:`SortOrderType`
            The default sort order type used to sort posts in forum channels.

            .. versionadded:: 2.3
        default_forum_layout: :class:`ForumLayoutType`
            The default layout type used to display posts in.

            .. versionadded:: 2.4
        default_thread_slowmode_delay: :class:`int`
            The new default slowmode delay for threads created in this channel.
            This is not retroactively applied to old posts.
            Must be between ``0`` and ``21600``.

            .. versionadded:: 2.4
        available_tags: List[:class:`ForumTag`]
            The new list of tags available in this channel.

            .. versionadded:: 2.4
        default_reaction: Optional[Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`]]
            The new default reaction for threads created in this channel.

            .. versionadded:: 2.4

        Raises
        ------
        InvalidArgument
            If position is less than 0 or greater than the number of channels, or if
            the permission overwrite information is not in proper form.
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.

        Returns
        -------
        :class:`.ForumChannel`
            The newly edited forum channel.
        """

        payload = await self._edit(options, reason=reason)
        if payload is not None:
            # the payload will always be the proper channel payload
            return self.__class__(state=self._state, guild=self.guild, data=payload)  # type: ignore
        return self

    def get_thread(self, thread_id: int, /) -> Optional[Thread]:
        """Returns a thread with the given ID.

        Parameters
        ----------
        thread_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Thread`]
            The returned thread or ``None`` if not found.
        """
        return self.guild.get_thread(thread_id)

    async def create_thread(
        self,
        *,
        name: str,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
        slowmode_delay: int = 0,
        content: Optional[str] = None,
        embed: Optional[Embed] = None,
        embeds: Optional[List[Embed]] = None,
        file: Optional[File] = None,
        files: Optional[List[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        nonce: Optional[str] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        mention_author: Optional[bool] = None,
        view: Optional[ui.View] = None,
        reason: Optional[str] = None,
        applied_tags: Optional[List[ForumTag]] = None,
        flags: Optional[MessageFlags] = None,
        suppress_embeds: Optional[bool] = None,
    ) -> Thread:
        """|coro|

        Creates a thread in this forum channel.

        To create a public thread, you must have
        :attr:`~nextcord.Permissions.create_public_threads`.
        For a private thread, :attr:`~nextcord.Permissions.create_private_threads`
        is needed instead.

        Parameters
        ----------
        name: :class:`str`
            The name of the thread.
        auto_archive_duration: :class:`int`
            The duration in minutes before a thread is automatically archived for inactivity.
            If not provided, the channel's default auto archive duration is used.
        reason: :class:`str`
            The reason for creating a new thread. Shows up on the audit log.
        content: Optional[:class:`str`]
            The content of the message to send.
        embed: Optional[:class:`~nextcord.Embed`]
            The rich embed for the content.
        embeds: Optional[List[:class:`~nextcord.Embed`]]
            A list of rich embeds for the content.
        file: :class:`~nextcord.File`
            The file to upload.
        files: Optional[List[:class:`~nextcord.File`]]
            A list of files to upload. Must be a maximum of 10.
        nonce: Optional[:class:`int`]
            The nonce to use for sending this message. If the message was successfully sent,
            then the message will have a nonce with this value.
        allowed_mentions: Optional[:class:`~nextcord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~nextcord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~nextcord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~nextcord.Client.allowed_mentions`
            are used instead.
        mention_author: Optional[:class:`bool`]
            Whether to mention the author of the message being replied to. Defaults to ``True``.
        view: Optional[:class:`~nextcord.ui.View`]
            The view to send with the message.
        stickers: Optional[Sequence[Union[:class:`~nextcord.GuildSticker`, :class:`~nextcord.StickerItem`]]]
            A list of stickers to send with the message.
        applied_tags: Optional[List[:class:`ForumTag`]]
            A list of tags to apply to the thread.

            .. versionadded:: 2.4
        flags: Optional[:class:`~nextcord.MessageFlags`]
            The message flags being set for this message.
            Currently only :class:`~nextcord.MessageFlags.suppress_embeds` is able to be set.
            .. versionadded:: 2.4
        suppress_embeds: Optional[:class:`bool`]
            Whether to suppress embeds on this message.
            .. versionadded:: 2.4

        Raises
        ------
        Forbidden
            You do not have permissions to create a thread.
        HTTPException
            Starting the thread failed.
        InvalidArgument
            You cannot pass both ``embed`` and ``embeds`` parameters.

        Returns
        -------
        :class:`Thread`
            The created thread.
        """
        state = self._state
        content = str(content) if content is not None else None

        if embed is not None and embeds is not None:
            raise InvalidArgument("Cannot pass both embed and embeds parameter to create_thread()")

        if embed is not None:
            raw_embeds = [embed.to_dict()]
        elif embeds is not None:
            raw_embeds = [embed.to_dict() for embed in embeds]
        else:
            raw_embeds = []

        raw_stickers = [sticker.id for sticker in stickers] if stickers is not None else []

        if allowed_mentions is not None:
            if state.allowed_mentions is not None:
                raw_allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
            else:
                raw_allowed_mentions = allowed_mentions.to_dict()
        else:
            raw_allowed_mentions = state.allowed_mentions and state.allowed_mentions.to_dict()

        if mention_author is not None:
            raw_allowed_mentions = raw_allowed_mentions or AllowedMentions().to_dict()
            raw_allowed_mentions["replied_user"] = bool(mention_author)

        if view:
            if not hasattr(view, "__discord_ui_view__"):
                raise InvalidArgument(f"View parameter must be View not {view.__class__!r}")

            components = view.to_components()
        else:
            components = None

        if file is not None and files is not None:
            raise InvalidArgument("Cannot pass both file and files parameter to send()")

        if file is not None:
            files = [file]

        if applied_tags is None:
            applied_tag_ids = []
        else:
            applied_tag_ids = [str(tag.id) for tag in applied_tags if tag.id is not None]

        if flags is None:
            flags = MessageFlags()
        if suppress_embeds is not None:
            flags.suppress_embeds = suppress_embeds

        flag_value: Optional[int] = flags.value if flags.value != 0 else None

        if files is not None:
            if not all(isinstance(file, File) for file in files):
                raise TypeError("Files parameter must be a list of type File")

            try:
                data = await state.http.start_thread_in_forum_channel_with_files(
                    self.id,
                    name=name,
                    auto_archive_duration=auto_archive_duration
                    or self.default_auto_archive_duration,
                    rate_limit_per_user=slowmode_delay,
                    files=files,
                    content=content,
                    embeds=raw_embeds,
                    nonce=nonce,
                    allowed_mentions=raw_allowed_mentions,
                    stickers=raw_stickers,
                    components=components,  # type: ignore
                    applied_tag_ids=applied_tag_ids,
                    reason=reason,
                    flags=flag_value,
                )
            finally:
                for f in files:
                    f.close()
        else:
            data = await state.http.start_thread_in_forum_channel(
                self.id,
                name=name,
                auto_archive_duration=auto_archive_duration or self.default_auto_archive_duration,
                rate_limit_per_user=slowmode_delay,
                content=content,
                embeds=raw_embeds,
                nonce=nonce,
                allowed_mentions=raw_allowed_mentions,
                stickers=raw_stickers,
                components=components,  # type: ignore
                applied_tag_ids=applied_tag_ids,
                reason=reason,
                flags=flag_value,
            )

        if view:
            msg_id = data.get("id")
            state.store_view(view, int(msg_id) if msg_id else None)

        return Thread(guild=self.guild, state=self._state, data=data)

    def archived_threads(
        self,
        *,
        private: bool = False,
        joined: bool = False,
        limit: Optional[int] = 50,
        before: Optional[Union[Snowflake, datetime.datetime]] = None,
    ) -> ArchivedThreadIterator:
        """Returns an :class:`~nextcord.AsyncIterator` that iterates over all archived threads in the guild.

        You must have :attr:`~Permissions.read_message_history` to use this.
        If iterating over private threads then :attr:`~Permissions.manage_threads` is also required.

        Parameters
        ----------
        limit: Optional[:class:`bool`]
            The number of threads to retrieve.
            If ``None``, retrieves every archived thread in the channel. Note, however,
            that this would make it a slow operation.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve archived channels before the given date or ID.
        private: :class:`bool`
            Whether to retrieve private archived threads.
        joined: :class:`bool`
            Whether to retrieve private archived threads that you've joined.
            This defaults to ``False``.

        .. note::

            You cannot set ``joined`` to ``True`` and ``private`` to ``False``.

        Raises
        ------
        Forbidden
            You do not have permissions to get archived threads.
        HTTPException
            The request to get the archived threads failed.

        Yields
        ------
        :class:`Thread`
            The archived threads.
        """
        return ArchivedThreadIterator(
            self.id, self.guild, limit=limit, joined=joined, private=private, before=before
        )

    async def create_webhook(
        self,
        *,
        name: str,
        avatar: Optional[Union[bytes, Asset, Attachment, File]] = None,
        reason: Optional[str] = None,
    ) -> Webhook:
        """|coro|

        Creates a webhook for this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        .. versionadded:: 2.4

        Parameters
        ----------
        name: :class:`str`
            The webhook's name.
        avatar: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`,
            or :class:`Asset` representing the webhook's default avatar.
            This operates similarly to :meth:`~ClientUser.edit`.
        reason: Optional[:class:`str`]
            The reason for creating this webhook. Shows up in the audit logs.

        Raises
        ------
        HTTPException
            Creating the webhook failed.
        Forbidden
            You do not have permissions to create a webhook.

        Returns
        -------
        :class:`Webhook`
            The created webhook.
        """

        from .webhook import Webhook

        avatar_base64 = await utils.obj_to_base64_data(avatar)

        data = await self._state.http.create_webhook(
            self.id, name=str(name), avatar=avatar_base64, reason=reason
        )
        return Webhook.from_state(data, state=self._state)


class VocalGuildChannel(abc.Connectable, abc.GuildChannel, Hashable):
    __slots__ = (
        "name",
        "id",
        "guild",
        "bitrate",
        "user_limit",
        "_state",
        "position",
        "_overwrites",
        "category_id",
        "rtc_region",
        "video_quality_mode",
        "flags",
    )

    def __init__(
        self,
        *,
        state: ConnectionState,
        guild: Guild,
        data: Union[VoiceChannelPayload, StageChannelPayload],
    ) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data["id"])
        self._update(guild, data)

    def _get_voice_client_key(self) -> Tuple[int, str]:
        return self.guild.id, "guild_id"

    def _get_voice_state_pair(self) -> Tuple[int, int]:
        return self.guild.id, self.id

    def _update(self, guild: Guild, data: Union[VoiceChannelPayload, StageChannelPayload]) -> None:
        self.guild = guild
        self.name: str = data["name"]
        rtc = data.get("rtc_region")
        self.rtc_region: Optional[VoiceRegion] = (
            try_enum(VoiceRegion, rtc) if rtc is not None else None
        )
        self.video_quality_mode: VideoQualityMode = try_enum(
            VideoQualityMode, data.get("video_quality_mode", 1)
        )
        self.category_id: Optional[int] = utils.get_as_snowflake(data, "parent_id")
        self.position: int = data["position"]
        self.bitrate: int = data.get("bitrate")
        self.user_limit: int = data.get("user_limit")
        self.flags: ChannelFlags = ChannelFlags._from_value(data.get("flags", 0))
        self.nsfw: bool = data.get("nsfw", False)
        self._fill_overwrites(data)

    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.voice.value

    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: Returns all members that are currently inside this voice channel."""
        ret = []
        for user_id, state in self.guild._voice_states.items():
            if state.channel and state.channel.id == self.id:
                member = self.guild.get_member(user_id)
                if member is not None:
                    ret.append(member)
        return ret

    @property
    def voice_states(self) -> Dict[int, VoiceState]:
        """Returns a mapping of member IDs who have voice states in this channel.

        .. versionadded:: 1.3

        .. note::

            This function is intentionally low level to replace :attr:`members`
            when the member cache is unavailable.

        Returns
        -------
        Mapping[:class:`int`, :class:`VoiceState`]
            The mapping of member ID to a voice state.
        """
        return {
            key: value
            for key, value in self.guild._voice_states.items()
            if value.channel and value.channel.id == self.id
        }

    @utils.copy_doc(abc.GuildChannel.permissions_for)
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        base = super().permissions_for(obj)

        # voice channels cannot be edited by people who can't connect to them
        # It also implicitly denies all other voice perms
        if not base.connect:
            denied = Permissions.voice()
            denied.update(manage_channels=True, manage_roles=True)
            base.value &= ~denied.value
        return base

    def is_nsfw(self) -> bool:
        """:class:`bool`: Checks if the channel is NSFW."""
        return self.nsfw


class VoiceChannel(VocalGuildChannel, abc.Messageable):
    """Represents a Discord guild voice channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    ----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a voice channel.
    rtc_region: Optional[:class:`VoiceRegion`]
        The region for the voice channel's voice communication.
        A value of ``None`` indicates automatic voice region detection.

        .. versionadded:: 1.7
    video_quality_mode: :class:`VideoQualityMode`
        The camera video quality for the voice channel's participants.

        .. versionadded:: 2.0
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.

        .. versionadded:: 2.1
    nsfw: :class:`bool`
        If the channel is marked as "not safe for work".

        .. note::

            To check if the channel or the guild of that channel are marked as NSFW, consider :meth:`is_nsfw` instead.

        .. versionadded:: 2.1
    flags: :class:`ChannelFlags`
        Extra features of the channel.

        ..versionadded:: 2.1
    """

    __slots__ = (
        "last_message_id",
        "nsfw",
    )

    def __repr__(self) -> str:
        attrs = [
            ("id", self.id),
            ("name", self.name),
            ("rtc_region", self.rtc_region),
            ("position", self.position),
            ("bitrate", self.bitrate),
            ("video_quality_mode", self.video_quality_mode),
            ("user_limit", self.user_limit),
            ("category_id", self.category_id),
        ]
        joined = " ".join("%s=%r" % t for t in attrs)
        return f"<{self.__class__.__name__} {joined}>"

    def _update(self, guild: Guild, data: VoiceChannelPayload) -> None:
        VocalGuildChannel._update(self, guild, data)
        self.last_message_id: Optional[int] = utils.get_as_snowflake(data, "last_message_id")

    async def _get_channel(self):
        return self

    @property
    def type(self) -> ChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.voice

    @property
    def last_message(self) -> Optional[Message]:
        """Fetches the last message from this channel in cache.

        The message might not be valid or point to an existing message.

        .. admonition:: Reliable Fetching
            :class: helpful

            For a slightly more reliable method of fetching the
            last message, consider using either :meth:`history`
            or :meth:`fetch_message` with the :attr:`last_message_id`
            attribute.

        .. versionadded:: 2.1

        Returns
        -------
        Optional[:class:`Message`]
            The last message in this channel or ``None`` if not found.
        """
        return self._state._get_message(self.last_message_id) if self.last_message_id else None

    @utils.copy_doc(abc.GuildChannel.clone)
    async def clone(
        self, *, name: Optional[str] = None, reason: Optional[str] = None
    ) -> VoiceChannel:
        return await self._clone_impl(
            {"bitrate": self.bitrate, "user_limit": self.user_limit}, name=name, reason=reason
        )

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        bitrate: int = ...,
        user_limit: int = ...,
        position: int = ...,
        sync_permissions: int = ...,
        category: Optional[CategoryChannel] = ...,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        rtc_region: Optional[VoiceRegion] = ...,
        video_quality_mode: VideoQualityMode = ...,
        flags: ChannelFlags = ...,
        reason: Optional[str] = ...,
    ) -> Optional[VoiceChannel]:
        ...

    @overload
    async def edit(self) -> Optional[VoiceChannel]:
        ...

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        .. versionchanged:: 1.3
            The ``overwrites`` keyword-only parameter was added.

        .. versionchanged:: 2.0
            Edits are no longer in-place, the newly edited channel is returned instead.

        Parameters
        ----------
        name: :class:`str`
            The new channel's name.
        bitrate: :class:`int`
            The new channel's bitrate.
        user_limit: :class:`int`
            The new channel's user limit.

            This must be a number between ``0`` and ``99``. ``0`` indicates no limit.
        position: :class:`int`
            The new channel's position.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing
            category. Defaults to ``False``.
        category: Optional[:class:`CategoryChannel`]
            The new category for this channel. Can be ``None`` to remove the
            category.
        reason: Optional[:class:`str`]
            The reason for editing this channel. Shows up on the audit log.
        overwrites: :class:`Mapping`
            A :class:`Mapping` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply to the channel.
        rtc_region: Optional[:class:`VoiceRegion`]
            The new region for the voice channel's voice communication.
            A value of ``None`` indicates automatic voice region detection.

            .. versionadded:: 1.7
        video_quality_mode: :class:`VideoQualityMode`
            The camera video quality for the voice channel's participants.

            .. versionadded:: 2.0

        Raises
        ------
        InvalidArgument
            If the permission overwrite information is not in proper form.
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.

        Returns
        -------
        Optional[:class:`.VoiceChannel`]
            The newly edited voice channel. If the edit was only positional
            then ``None`` is returned instead.
        """

        payload = await self._edit(options, reason=reason)
        if payload is not None:
            # the payload will always be the proper channel payload
            return self.__class__(state=self._state, guild=self.guild, data=payload)  # type: ignore
        return None

    async def delete_messages(self, messages: Iterable[Snowflake]) -> None:
        """|coro|

        Deletes a list of messages. This is similar to :meth:`Message.delete`
        except it bulk deletes multiple messages.

        As a special case, if the number of messages is 0, then nothing
        is done. If the number of messages is 1 then single message
        delete is done. If it's more than two, then bulk delete is used.

        You cannot bulk delete more than 100 messages or messages that
        are older than 14 days old.

        You must have the :attr:`~Permissions.manage_messages` permission to
        use this.

        .. versionadded:: 2.1

        Parameters
        ----------
        messages: Iterable[:class:`abc.Snowflake`]
            An iterable of messages denoting which ones to bulk delete.

        Raises
        ------
        ClientException
            The number of messages to delete was more than 100.
        Forbidden
            You do not have proper permissions to delete the messages.
        NotFound
            If single delete, then the message was already deleted.
        HTTPException
            Deleting the messages failed.
        """
        if not isinstance(messages, (list, tuple)):
            messages = list(messages)

        if len(messages) == 0:
            return  # do nothing

        if len(messages) == 1:
            message_id: int = messages[0].id
            await self._state.http.delete_message(self.id, message_id)
            return

        if len(messages) > 100:
            raise ClientException("Can only bulk delete messages up to 100 messages")

        message_ids: SnowflakeList = [m.id for m in messages]
        await self._state.http.delete_messages(self.id, message_ids)

    async def purge(
        self,
        *,
        limit: Optional[int] = 100,
        check: Callable[[Message], bool] = MISSING,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        around: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = False,
        bulk: bool = True,
    ) -> List[Message]:
        """|coro|

        Purges a list of messages that meet the criteria given by the predicate
        ``check``. If a ``check`` is not provided then all messages are deleted
        without discrimination.

        You must have the :attr:`~Permissions.manage_messages` permission to
        delete messages even if they are your own.
        The :attr:`~Permissions.read_message_history` permission is
        also needed to retrieve message history.

        .. versionadded:: 2.1

        Examples
        --------

        Deleting bot's messages ::

            def is_me(m):
                return m.author == client.user

            deleted = await channel.purge(limit=100, check=is_me)
            await channel.send(f'Deleted {len(deleted)} message(s)')

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of messages to search through. This is not the number
            of messages that will be deleted, though it can be.
        check: Callable[[:class:`Message`], :class:`bool`]
            The function used to check if a message should be deleted.
            It must take a :class:`Message` as its sole parameter.
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``before`` in :meth:`history`.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``after`` in :meth:`history`.
        around: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Same as ``around`` in :meth:`history`.
        oldest_first: Optional[:class:`bool`]
            Same as ``oldest_first`` in :meth:`history`.
        bulk: :class:`bool`
            If ``True``, use bulk delete. Setting this to ``False`` is useful for mass-deleting
            a bot's own messages without :attr:`Permissions.manage_messages`. When ``True``, will
            fall back to single delete if messages are older than two weeks.

        Raises
        ------
        Forbidden
            You do not have proper permissions to do the actions required.
        HTTPException
            Purging the messages failed.

        Returns
        -------
        List[:class:`.Message`]
            The list of messages that were deleted.
        """

        if check is MISSING:
            check = lambda _: True

        iterator = self.history(
            limit=limit, before=before, after=after, oldest_first=oldest_first, around=around
        )
        ret: List[Message] = []
        count = 0

        minimum_time = int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
        strategy = self.delete_messages if bulk else _single_delete_strategy

        async for message in iterator:
            if count == 100:
                to_delete = ret[-100:]
                await strategy(to_delete)
                count = 0
                await asyncio.sleep(1)

            if not check(message):
                continue

            if message.id < minimum_time:
                # older than 14 days old
                if count == 1:
                    await ret[-1].delete()
                elif count >= 2:
                    to_delete = ret[-count:]
                    await strategy(to_delete)

                count = 0
                strategy = _single_delete_strategy

            count += 1
            ret.append(message)

        # Some messages remaining to poll
        if count >= 2:
            # more than 2 messages -> bulk delete
            to_delete = ret[-count:]
            await strategy(to_delete)
        elif count == 1:
            # delete a single message
            await ret[-1].delete()

        return ret

    async def create_webhook(
        self,
        *,
        name: str,
        avatar: Optional[Union[bytes, Asset, Attachment, File]] = None,
        reason: Optional[str] = None,
    ) -> Webhook:
        """|coro|

        Creates a webhook for this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        .. versionadded:: 2.4

        Parameters
        ----------
        name: :class:`str`
            The webhook's name.
        avatar: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`,
            or :class:`Asset` representing the webhook's default avatar.
            This operates similarly to :meth:`~ClientUser.edit`.
        reason: Optional[:class:`str`]
            The reason for creating this webhook. Shows up in the audit logs.

        Raises
        ------
        HTTPException
            Creating the webhook failed.
        Forbidden
            You do not have permissions to create a webhook.

        Returns
        -------
        :class:`Webhook`
            The created webhook.
        """

        from .webhook import Webhook

        avatar_base64 = await utils.obj_to_base64_data(avatar)

        data = await self._state.http.create_webhook(
            self.id, name=str(name), avatar=avatar_base64, reason=reason
        )
        return Webhook.from_state(data, state=self._state)


class StageChannel(VocalGuildChannel, abc.Messageable):
    """Represents a Discord guild stage channel.

    .. versionadded:: 1.7

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    ----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    topic: Optional[:class:`str`]
        The channel's topic. ``None`` if it isn't set.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a stage channel.
    rtc_region: Optional[:class:`VoiceRegion`]
        The region for the stage channel's voice communication.
        A value of ``None`` indicates automatic voice region detection.
    video_quality_mode: :class:`VideoQualityMode`
        The camera video quality for the stage channel's participants.

        .. versionadded:: 2.0
    flags: :class:`ChannelFlags`
        Extra features of the channel.

        ..versionadded:: 2.1
    nsfw: :class:`bool`
        If the channel is marked as "not safe for work".

        .. versionadded:: 2.6

        .. note::

            To check if the channel or the guild of that channel are marked as NSFW,
            consider :meth:`is_nsfw` instead.
    """

    __slots__ = ("topic", "nsfw")

    def __repr__(self) -> str:
        attrs = [
            ("id", self.id),
            ("name", self.name),
            ("topic", self.topic),
            ("rtc_region", self.rtc_region),
            ("position", self.position),
            ("bitrate", self.bitrate),
            ("video_quality_mode", self.video_quality_mode),
            ("user_limit", self.user_limit),
            ("category_id", self.category_id),
            ("nsfw", self.nsfw),
        ]
        joined = " ".join("%s=%r" % t for t in attrs)
        return f"<{self.__class__.__name__} {joined}>"

    def _update(self, guild: Guild, data: StageChannelPayload) -> None:
        super()._update(guild, data)
        self.topic: Optional[str] = data.get("topic")

    async def _get_channel(self):
        return self

    @property
    def requesting_to_speak(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who are requesting to speak in the stage channel."""
        return [
            member
            for member in self.members
            if member.voice and member.voice.requested_to_speak_at is not None
        ]

    @property
    def speakers(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who have been permitted to speak in the stage channel.

        .. versionadded:: 2.0
        """
        return [
            member
            for member in self.members
            if member.voice
            and not member.voice.suppress
            and member.voice.requested_to_speak_at is None
        ]

    @property
    def listeners(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who are listening in the stage channel.

        .. versionadded:: 2.0
        """
        return [member for member in self.members if member.voice and member.voice.suppress]

    @property
    def moderators(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who are moderating the stage channel.

        .. versionadded:: 2.0
        """
        required_permissions = Permissions.stage_moderator()
        return [
            member
            for member in self.members
            if self.permissions_for(member) >= required_permissions
        ]

    @property
    def type(self) -> ChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.stage_voice

    @utils.copy_doc(abc.GuildChannel.clone)
    async def clone(
        self, *, name: Optional[str] = None, reason: Optional[str] = None
    ) -> StageChannel:
        return await self._clone_impl({}, name=name, reason=reason)

    @property
    def instance(self) -> Optional[StageInstance]:
        """Optional[:class:`StageInstance`]: The running stage instance of the stage channel.

        .. versionadded:: 2.0
        """
        return utils.get(self.guild.stage_instances, channel_id=self.id)

    async def create_instance(
        self,
        *,
        topic: str,
        privacy_level: StagePrivacyLevel = MISSING,
        reason: Optional[str] = None,
    ) -> StageInstance:
        """|coro|

        Create a stage instance.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        .. versionadded:: 2.0

        Parameters
        ----------
        topic: :class:`str`
            The stage instance's topic.
        privacy_level: :class:`StagePrivacyLevel`
            The stage instance's privacy level. Defaults to :attr:`StagePrivacyLevel.guild_only`.
        reason: :class:`str`
            The reason the stage instance was created. Shows up on the audit log.

        Raises
        ------
        InvalidArgument
            If the ``privacy_level`` parameter is not the proper type.
        Forbidden
            You do not have permissions to create a stage instance.
        HTTPException
            Creating a stage instance failed.

        Returns
        -------
        :class:`StageInstance`
            The newly created stage instance.
        """

        payload: Dict[str, Any] = {"channel_id": self.id, "topic": topic}

        if privacy_level is not MISSING:
            if not isinstance(privacy_level, StagePrivacyLevel):
                raise InvalidArgument("privacy_level field must be of type PrivacyLevel")

            payload["privacy_level"] = privacy_level.value

        data = await self._state.http.create_stage_instance(**payload, reason=reason)
        return StageInstance(guild=self.guild, state=self._state, data=data)

    async def fetch_instance(self) -> StageInstance:
        """|coro|

        Gets the running :class:`StageInstance`.

        .. versionadded:: 2.0

        Raises
        ------
        :exc:`.NotFound`
            The stage instance or channel could not be found.
        :exc:`.HTTPException`
            Getting the stage instance failed.

        Returns
        -------
        :class:`StageInstance`
            The stage instance.
        """
        data = await self._state.http.get_stage_instance(self.id)
        return StageInstance(guild=self.guild, state=self._state, data=data)

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        topic: Optional[str] = ...,
        position: int = ...,
        sync_permissions: int = ...,
        category: Optional[CategoryChannel] = ...,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        rtc_region: Optional[VoiceRegion] = ...,
        video_quality_mode: VideoQualityMode = ...,
        flags: ChannelFlags = ...,
        user_limit: int = ...,
        reason: Optional[str] = ...,
    ) -> Optional[StageChannel]:
        ...

    @overload
    async def edit(self) -> Optional[StageChannel]:
        ...

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        .. versionchanged:: 2.0
            The ``topic`` parameter must now be set via :attr:`create_instance`.

        .. versionchanged:: 2.0
            Edits are no longer in-place, the newly edited channel is returned instead.

        Parameters
        ----------
        name: :class:`str`
            The new channel's name.
        position: :class:`int`
            The new channel's position.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing
            category. Defaults to ``False``.
        category: Optional[:class:`CategoryChannel`]
            The new category for this channel. Can be ``None`` to remove the
            category.
        reason: Optional[:class:`str`]
            The reason for editing this channel. Shows up on the audit log.
        overwrites: :class:`Mapping`
            A :class:`Mapping` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply to the channel.
        rtc_region: Optional[:class:`VoiceRegion`]
            The new region for the stage channel's voice communication.
            A value of ``None`` indicates automatic voice region detection.
        video_quality_mode: :class:`VideoQualityMode`
            The camera video quality for the stage channel's participants.

            .. versionadded:: 2.0
        user_limit: :class:`int`
            The maximum number of users allowed in the stage channel.

            This must be between ``0`` and ``10,000``. A value of ``0`` indicates
            no limit.

            .. versionadded:: 2.6

        Raises
        ------
        InvalidArgument
            If the permission overwrite information is not in proper form.
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.

        Returns
        -------
        Optional[:class:`.StageChannel`]
            The newly edited stage channel. If the edit was only positional
            then ``None`` is returned instead.
        """

        payload = await self._edit(options, reason=reason)
        if payload is not None:
            # the payload will always be the proper channel payload
            return self.__class__(state=self._state, guild=self.guild, data=payload)  # type: ignore
        return None


class CategoryChannel(abc.GuildChannel, Hashable):
    """Represents a Discord channel category.

    These are useful to group channels to logical compartments.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the category's hash.

        .. describe:: str(x)

            Returns the category's name.

    Attributes
    ----------
    name: :class:`str`
        The category name.
    guild: :class:`Guild`
        The guild the category belongs to.
    id: :class:`int`
        The category channel ID.
    position: :class:`int`
        The position in the category list. This is a number that starts at 0. e.g. the
        top category is position 0.
    nsfw: :class:`bool`
        If the channel is marked as "not safe for work".

        .. note::

            To check if the channel or the guild of that channel are marked as NSFW, consider :meth:`is_nsfw` instead.
    flags: :class:`ChannelFlags`
        Extra features of the channel.

        ..versionadded:: 2.1
    """

    __slots__ = (
        "name",
        "id",
        "guild",
        "nsfw",
        "_state",
        "position",
        "_overwrites",
        "category_id",
        "flags",
    )

    def __init__(
        self, *, state: ConnectionState, guild: Guild, data: CategoryChannelPayload
    ) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data["id"])
        self._update(guild, data)

    def __repr__(self) -> str:
        return f"<CategoryChannel id={self.id} name={self.name!r} position={self.position} nsfw={self.nsfw}>"

    def _update(self, guild: Guild, data: CategoryChannelPayload) -> None:
        self.guild: Guild = guild
        self.name: str = data["name"]
        self.category_id: Optional[int] = utils.get_as_snowflake(data, "parent_id")
        self.nsfw: bool = data.get("nsfw", False)
        self.position: int = data["position"]
        self.flags: ChannelFlags = ChannelFlags._from_value(data.get("flags", 0))
        self._fill_overwrites(data)

    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.category.value

    @property
    def type(self) -> ChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.category

    def is_nsfw(self) -> bool:
        """:class:`bool`: Checks if the category is NSFW."""
        return self.nsfw

    @utils.copy_doc(abc.GuildChannel.clone)
    async def clone(
        self, *, name: Optional[str] = None, reason: Optional[str] = None
    ) -> CategoryChannel:
        return await self._clone_impl({"nsfw": self.nsfw}, name=name, reason=reason)

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        position: int = ...,
        nsfw: bool = ...,
        overwrites: Mapping[Union[Role, Member], PermissionOverwrite] = ...,
        flags: ChannelFlags = ...,
        reason: Optional[str] = ...,
    ) -> Optional[CategoryChannel]:
        ...

    @overload
    async def edit(self) -> Optional[CategoryChannel]:
        ...

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        .. versionchanged:: 1.3
            The ``overwrites`` keyword-only parameter was added.

        .. versionchanged:: 2.0
            Edits are no longer in-place, the newly edited channel is returned instead.

        Parameters
        ----------
        name: :class:`str`
            The new category's name.
        position: :class:`int`
            The new category's position.
        nsfw: :class:`bool`
            To mark the category as NSFW or not.
        reason: Optional[:class:`str`]
            The reason for editing this category. Shows up on the audit log.
        overwrites: :class:`Mapping`
            A :class:`Mapping` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply to the channel.

        Raises
        ------
        InvalidArgument
            If position is less than 0 or greater than the number of categories.
        Forbidden
            You do not have permissions to edit the category.
        HTTPException
            Editing the category failed.

        Returns
        -------
        Optional[:class:`.CategoryChannel`]
            The newly edited category channel. If the edit was only positional
            then ``None`` is returned instead.
        """

        payload = await self._edit(options, reason=reason)
        if payload is not None:
            # the payload will always be the proper channel payload
            return self.__class__(state=self._state, guild=self.guild, data=payload)  # type: ignore
        return None

    @utils.copy_doc(abc.GuildChannel.move)
    async def move(self, **kwargs) -> None:
        kwargs.pop("category", None)
        await super().move(**kwargs)

    @property
    def channels(self) -> List[GuildChannelType]:
        """List[:class:`abc.GuildChannel`]: Returns the channels that are under this category.

        These are sorted by the official Discord UI, which places voice channels below the text channels.
        """

        def comparator(channel):
            return (not isinstance(channel, TextChannel), channel.position)

        ret = [c for c in self.guild.channels if c.category_id == self.id]
        ret.sort(key=comparator)
        return ret

    @property
    def text_channels(self) -> List[TextChannel]:
        """List[:class:`TextChannel`]: Returns the text channels that are under this category."""
        ret = [
            c
            for c in self.guild.channels
            if c.category_id == self.id and isinstance(c, TextChannel)
        ]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

    @property
    def voice_channels(self) -> List[VoiceChannel]:
        """List[:class:`VoiceChannel`]: Returns the voice channels that are under this category."""
        ret = [
            c
            for c in self.guild.channels
            if c.category_id == self.id and isinstance(c, VoiceChannel)
        ]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

    @property
    def stage_channels(self) -> List[StageChannel]:
        """List[:class:`StageChannel`]: Returns the stage channels that are under this category.

        .. versionadded:: 1.7
        """
        ret = [
            c
            for c in self.guild.channels
            if c.category_id == self.id and isinstance(c, StageChannel)
        ]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

    async def create_text_channel(self, name: str, **options: Any) -> TextChannel:
        """|coro|

        A shortcut method to :meth:`Guild.create_text_channel` to create a :class:`TextChannel` in the category.

        Returns
        -------
        :class:`TextChannel`
            The channel that was just created.
        """
        return await self.guild.create_text_channel(name, category=self, **options)

    async def create_voice_channel(self, name: str, **options: Any) -> VoiceChannel:
        """|coro|

        A shortcut method to :meth:`Guild.create_voice_channel` to create a :class:`VoiceChannel` in the category.

        Returns
        -------
        :class:`VoiceChannel`
            The channel that was just created.
        """
        return await self.guild.create_voice_channel(name, category=self, **options)

    async def create_stage_channel(self, name: str, **options: Any) -> StageChannel:
        """|coro|

        A shortcut method to :meth:`Guild.create_stage_channel` to create a :class:`StageChannel` in the category.

        .. versionadded:: 1.7

        Returns
        -------
        :class:`StageChannel`
            The channel that was just created.
        """
        return await self.guild.create_stage_channel(name, category=self, **options)

    async def create_forum_channel(self, name: str, **options: Any) -> ForumChannel:
        """|coro|

        A shortcut method to :meth:`Guild.create_forum_channel` to create a :class:`ForumChannel`
        in the category.

        .. versionadded:: 2.1

        Returns
        -------
        :class:`ForumChannel`
            The channel that was just created.
        """
        return await self.guild.create_forum_channel(name, category=self, **options)


DMC = TypeVar("DMC", bound="DMChannel")


class DMChannel(abc.Messageable, abc.PrivateChannel, Hashable, PinsMixin):
    """Represents a Discord direct message channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns a string representation of the channel

    Attributes
    ----------
    recipient: Optional[:class:`User`]
        The user you are participating with in the direct message channel.
        If this channel is received through the gateway, the recipient information
        may not be always available.
    me: :class:`ClientUser`
        The user presenting yourself.
    id: :class:`int`
        The direct message channel ID.
    """

    __slots__ = ("id", "recipient", "me", "_state")

    def __init__(self, *, me: ClientUser, state: ConnectionState, data: DMChannelPayload) -> None:
        self._state: ConnectionState = state
        self.recipient: Optional[User] = state.store_user(data["recipients"][0])  # type: ignore
        self.me: ClientUser = me
        self.id: int = int(data["id"])

    async def _get_channel(self):
        return self

    def __str__(self) -> str:
        if self.recipient:
            return f"Direct Message with {self.recipient}"
        return "Direct Message with Unknown User"

    def __repr__(self) -> str:
        return f"<DMChannel id={self.id} recipient={self.recipient!r}>"

    @classmethod
    def _from_message(cls, state: ConnectionState, channel_id: int) -> Self:
        self = cls.__new__(cls)
        self._state = state
        self.id = channel_id
        self.recipient = None
        # state.user won't be None here
        self.me = state.user  # type: ignore
        return self

    @property
    def type(self) -> ChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.private

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the direct message channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def permissions_for(self, obj: Any = None, /) -> Permissions:
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with other channel types.

        Actual direct messages do not really have the concept of permissions.

        This returns all the Text related permissions set to ``True`` except:

        - :attr:`~Permissions.send_tts_messages`: You cannot send TTS messages in a DM.
        - :attr:`~Permissions.manage_messages`: You cannot delete others messages in a DM.

        Parameters
        ----------
        obj: :class:`User`
            The user to check permissions for. This parameter is ignored
            but kept for compatibility with other ``permissions_for`` methods.

        Returns
        -------
        :class:`Permissions`
            The resolved permissions.
        """

        base = Permissions.text()
        base.read_messages = True
        base.send_tts_messages = False
        base.manage_messages = False
        return base

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        .. versionadded:: 1.6

        Parameters
        ----------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        -------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)


class GroupChannel(abc.Messageable, abc.PrivateChannel, Hashable, PinsMixin):
    """Represents a Discord group channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns a string representation of the channel

    Attributes
    ----------
    recipients: List[:class:`User`]
        The users you are participating with in the group channel.
    me: :class:`ClientUser`
        The user presenting yourself.
    id: :class:`int`
        The group channel ID.
    owner: Optional[:class:`User`]
        The user that owns the group channel.
    owner_id: :class:`int`
        The owner ID that owns the group channel.

        .. versionadded:: 2.0
    name: Optional[:class:`str`]
        The group channel's name if provided.
    """

    __slots__ = ("id", "recipients", "owner_id", "owner", "_icon", "name", "me", "_state")

    def __init__(
        self, *, me: ClientUser, state: ConnectionState, data: GroupChannelPayload
    ) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data["id"])
        self.me: ClientUser = me
        self._update_group(data)

    def _update_group(self, data: GroupChannelPayload) -> None:
        self.owner_id: Optional[int] = utils.get_as_snowflake(data, "owner_id")
        self._icon: Optional[str] = data.get("icon")
        self.name: Optional[str] = data.get("name")
        self.recipients: List[User] = [
            self._state.store_user(u) for u in data.get("recipients", [])
        ]

        self.owner: Optional[BaseUser]
        if self.owner_id == self.me.id:
            self.owner = self.me
        else:
            self.owner = utils.find(lambda u: u.id == self.owner_id, self.recipients)

    async def _get_channel(self):
        return self

    def __str__(self) -> str:
        if self.name:
            return self.name

        if len(self.recipients) == 0:
            return "Unnamed"

        return ", ".join((x.name for x in self.recipients))

    def __repr__(self) -> str:
        return f"<GroupChannel id={self.id} name={self.name!r}>"

    @property
    def type(self) -> ChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.group

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the channel's icon asset if available."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path="channel")

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def permissions_for(self, obj: Snowflake, /) -> Permissions:
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with other channel types.

        Actual direct messages do not really have the concept of permissions.

        This returns all the Text related permissions set to ``True`` except:

        - :attr:`~Permissions.send_tts_messages`: You cannot send TTS messages in a DM.
        - :attr:`~Permissions.manage_messages`: You cannot delete others messages in a DM.

        This also checks the kick_members permission if the user is the owner.

        Parameters
        ----------
        obj: :class:`~abc.Snowflake`
            The user to check permissions for.

        Returns
        -------
        :class:`Permissions`
            The resolved permissions for the user.
        """

        base = Permissions.text()
        base.read_messages = True
        base.send_tts_messages = False
        base.manage_messages = False
        base.mention_everyone = True

        if obj.id == self.owner_id:
            base.kick_members = True

        return base

    async def leave(self) -> None:
        """|coro|

        Leave the group.

        If you are the only one in the group, this deletes it as well.

        Raises
        ------
        HTTPException
            Leaving the group failed.
        """

        await self._state.http.leave_group(self.id)


class PartialMessageable(abc.Messageable, Hashable):
    """Represents a partial messageable to aid with working messageable channels when
    only a channel ID are present.

    The only way to construct this class is through :meth:`Client.get_partial_messageable`.

    Note that this class is trimmed down and has no rich attributes.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two partial messageables are equal.

        .. describe:: x != y

            Checks if two partial messageables are not equal.

        .. describe:: hash(x)

            Returns the partial messageable's hash.

    Attributes
    ----------
    id: :class:`int`
        The channel ID associated with this partial messageable.
    type: Optional[:class:`ChannelType`]
        The channel type associated with this partial messageable, if given.
    """

    def __init__(self, state: ConnectionState, id: int, type: Optional[ChannelType] = None) -> None:
        self._state: ConnectionState = state
        self._channel: Object = Object(id=id)
        self.id: int = id
        self.type: Optional[ChannelType] = type

    async def _get_channel(self) -> Object:
        return self._channel

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        Parameters
        ----------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        -------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)


def _guild_channel_factory(channel_type: int):
    value = try_enum(ChannelType, channel_type)
    if value is ChannelType.text:
        return TextChannel, value
    if value is ChannelType.voice:
        return VoiceChannel, value
    if value is ChannelType.category:
        return CategoryChannel, value
    if value is ChannelType.news:
        return TextChannel, value
    if value is ChannelType.stage_voice:
        return StageChannel, value
    if value is ChannelType.forum:
        return ForumChannel, value
    return None, value


def _channel_factory(channel_type: int):
    cls, value = _guild_channel_factory(channel_type)
    if value is ChannelType.private:
        return DMChannel, value
    if value is ChannelType.group:
        return GroupChannel, value
    return cls, value


def _threaded_channel_factory(channel_type: int):
    cls, value = _channel_factory(channel_type)
    if value in (ChannelType.private_thread, ChannelType.public_thread, ChannelType.news_thread):
        return Thread, value
    return cls, value


def _threaded_guild_channel_factory(channel_type: int):
    cls, value = _guild_channel_factory(channel_type)
    if value in (ChannelType.private_thread, ChannelType.public_thread, ChannelType.news_thread):
        return Thread, value
    return cls, value


class ForumTag:
    """Represents a tag in a forum channel that can be used to filter posts.

    .. versionadded:: 2.4

    Attributes
    ----------
    id: :class:`int`
        The ID of the tag.
    name: :class:`str`
        The name of the tag.
    moderated: :class:`bool`
        Whether this tag can only be added to or removed from threads
        by a member with the :attr:`~Permissions.manage_threads` permission.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji that represents this tag.

    Parameters
    ----------
    id: :class:`int`
        The ID of the tag.

        .. warning::

            This should not *really* be passed when constructing this manually.
            This is only documented here for the sake of completeness.

    name: :class:`str`
        The name of the tag.
    moderated: :class:`bool`
        Whether this tag can only be added to or removed from threads
        by a member with the :attr:`~Permissions.manage_threads` permission.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji that represents this tag.
    """

    __slots__ = ("id", "name", "moderated", "emoji")

    def __init__(
        self,
        *,
        id: Optional[int] = None,
        name: str,
        moderated: bool = False,
        emoji: Union[PartialEmoji, Emoji, str, None] = None,
    ) -> None:
        self.id: Optional[int] = id
        self.name: str = name
        self.moderated: bool = moderated

        if isinstance(emoji, Emoji):
            partial = emoji._to_partial()
        elif isinstance(emoji, str):
            partial = PartialEmoji.from_str(emoji)
        else:
            partial = emoji

        self.emoji: Optional[PartialEmoji] = partial

    @classmethod
    def from_data(cls, data: ForumTagPayload) -> ForumTag:
        return cls(
            id=int(data["id"]),
            name=data["name"],
            moderated=data["moderated"],
            emoji=PartialEmoji.from_default_reaction(data),
        )

    def __repr__(self) -> str:
        attrs = (
            ("id", self.id),
            ("name", self.name),
            ("moderated", self.moderated),
            ("emoji", self.emoji),
        )

        inner = " ".join("%s=%r" % t for t in attrs)
        return f"{type(self).__name__} {inner}"

    @property
    def payload(self) -> ForumTagPayload:
        data: ForumTagPayload = {
            "id": str(self.id),
            "name": self.name,
            "moderated": self.moderated,
        }

        if self.emoji is not None:
            if self.emoji.id is not None:
                data["emoji_id"] = str(self.emoji.id)
            else:
                data["emoji_name"] = self.emoji.name

        return data
