# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
import contextlib
import time
from typing import TYPE_CHECKING, Callable, Dict, Iterable, List, Optional, Union

from . import channel
from .abc import Messageable
from .enums import ChannelType, try_enum
from .errors import ClientException
from .flags import ChannelFlags
from .mixins import Hashable, PinsMixin
from .utils import MISSING, get_as_snowflake, parse_time

__all__ = (
    "Thread",
    "ThreadMember",
)

if TYPE_CHECKING:
    from datetime import datetime

    from .abc import Snowflake, SnowflakeTime
    from .channel import CategoryChannel, ForumChannel, ForumTag, TextChannel
    from .guild import Guild
    from .member import Member
    from .message import Message, PartialMessage
    from .permissions import Permissions
    from .role import Role
    from .state import ConnectionState
    from .types.snowflake import SnowflakeList
    from .types.threads import (
        Thread as ThreadPayload,
        ThreadArchiveDuration,
        ThreadMember as ThreadMemberPayload,
        ThreadMetadata,
    )


class Thread(Messageable, Hashable, PinsMixin):
    """Represents a Discord thread.

    .. container:: operations

        .. describe:: x == y

            Checks if two threads are equal.

        .. describe:: x != y

            Checks if two threads are not equal.

        .. describe:: hash(x)

            Returns the thread's hash.

        .. describe:: str(x)

            Returns the thread's name.

    .. versionadded:: 2.0

    Attributes
    ----------
    name: :class:`str`
        The thread name.
    guild: :class:`Guild`
        The guild the thread belongs to.
    id: :class:`int`
        The thread ID.
    parent_id: :class:`int`
        The parent :class:`TextChannel` ID this thread belongs to.
    owner_id: :class:`int`
        The user's ID that created this thread.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this thread. It may
        *not* point to an existing or valid message.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this thread. A value of ``0`` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    message_count: :class:`int`
        An approximate number of messages in this thread. This caps at 50.
    member_count: :class:`int`
        An approximate number of members in this thread. This caps at 50.
    me: Optional[:class:`ThreadMember`]
        A thread member representing yourself, if you've joined the thread.
        This could not be available.
    archived: :class:`bool`
        Whether the thread is archived.
    locked: :class:`bool`
        Whether the thread is locked.
    invitable: :class:`bool`
        Whether non-moderators can add other non-moderators to this thread.
        This is always ``True`` for public threads.
    archiver_id: Optional[:class:`int`]
        The user's ID that archived this thread.
    auto_archive_duration: :class:`int`
        The duration in minutes until the thread is automatically archived due to inactivity.
        Usually a value of 60, 1440, 4320 and 10080.
    archive_timestamp: :class:`datetime.datetime`
        An aware timestamp of when the thread's archived status was last updated in UTC.
    create_timestamp: Optional[:class:`datetime.datetime`]
        Returns the threads's creation time in UTC.
        This is ``None`` if the thread was created before January 9th, 2021.

        .. versionadded:: 2.0
    applied_tag_ids: List[:class:`int`]
        A list of tag IDs that have been applied to this thread.

        .. versionadded:: 2.4
    """

    __slots__ = (
        "name",
        "id",
        "guild",
        "_type",
        "_state",
        "_members",
        "owner_id",
        "parent_id",
        "last_message_id",
        "message_count",
        "member_count",
        "slowmode_delay",
        "me",
        "locked",
        "archived",
        "invitable",
        "archiver_id",
        "auto_archive_duration",
        "archive_timestamp",
        "create_timestamp",
        "flags",
        "applied_tag_ids",
    )

    def __init__(self, *, guild: Guild, state: ConnectionState, data: ThreadPayload) -> None:
        self._state: ConnectionState = state
        self.guild = guild
        self._members: Dict[int, ThreadMember] = {}
        self._from_data(data)

    async def _get_channel(self):
        return self

    def __repr__(self) -> str:
        return (
            f"<Thread id={self.id!r} name={self.name!r} parent={self.parent}"
            f" owner_id={self.owner_id!r} locked={self.locked} archived={self.archived}>"
        )

    def __str__(self) -> str:
        return self.name

    def _from_data(self, data: ThreadPayload) -> None:
        self.id = int(data["id"])
        self.parent_id = int(data["parent_id"])
        self.owner_id = int(data["owner_id"])
        self.name = data["name"]
        self._type = try_enum(ChannelType, data["type"])
        self.last_message_id = get_as_snowflake(data, "last_message_id")
        self.slowmode_delay = data.get("rate_limit_per_user", 0)
        self.message_count = data["message_count"]
        self.member_count = data["member_count"]
        self._unroll_metadata(data["thread_metadata"])
        self.flags: ChannelFlags = ChannelFlags._from_value(data.get("flags", 0))

        try:
            member = data["member"]
        except KeyError:
            self.me = None
        else:
            self.me = ThreadMember(self, member)

        self.applied_tag_ids: List[int] = [int(tag_id) for tag_id in data.get("applied_tags", [])]

    def _unroll_metadata(self, data: ThreadMetadata) -> None:
        self.archived = data["archived"]
        self.archiver_id = get_as_snowflake(data, "archiver_id")
        self.auto_archive_duration = data["auto_archive_duration"]
        self.archive_timestamp = parse_time(data["archive_timestamp"])
        self.locked = data.get("locked", False)
        self.invitable = data.get("invitable", True)
        self.create_timestamp = parse_time(data.get("create_timestamp"))

    def _update(self, data) -> None:
        with contextlib.suppress(KeyError):
            self.name = data["name"]

        self.slowmode_delay = data.get("rate_limit_per_user", 0)
        self.flags: ChannelFlags = ChannelFlags._from_value(data.get("flags", 0))
        self.applied_tag_ids: List[int] = [int(tag_id) for tag_id in data.get("applied_tags", [])]

        with contextlib.suppress(KeyError):
            self._unroll_metadata(data["thread_metadata"])

    @property
    def created_at(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: Returns the threads's creation time in UTC.
        This is ``None`` if the thread was created before January 9th, 2021.

        .. versionadded:: 2.0
        """
        return self.create_timestamp

    @property
    def type(self) -> ChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return self._type

    @property
    def parent(self) -> Optional[Union[TextChannel, ForumChannel]]:
        """Optional[Union[:class:`TextChannel`, :class:`ForumChannel`]]: The parent channel this thread belongs to."""
        return self.guild.get_channel(self.parent_id)  # type: ignore

    @property
    def owner(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member this thread belongs to."""
        return self.guild.get_member(self.owner_id)

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the thread."""
        return f"<#{self.id}>"

    @property
    def members(self) -> List[ThreadMember]:
        """List[:class:`ThreadMember`]: A list of thread members in this thread.

        This requires :attr:`Intents.members` to be properly filled. Most of the time however,
        this data is not provided by the gateway and a call to :meth:`fetch_members` is
        needed.
        """
        return list(self._members.values())

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

    @property
    def category(self) -> Optional[CategoryChannel]:
        """The category channel the parent channel belongs to, if applicable.

        Raises
        ------
        ClientException
            The parent channel was not cached and returned ``None``.

        Returns
        -------
        Optional[:class:`CategoryChannel`]
            The parent channel's category.
        """

        parent = self.parent
        if parent is None:
            raise ClientException("Parent channel not found")
        return parent.category

    @property
    def category_id(self) -> Optional[int]:
        """The category channel ID the parent channel belongs to, if applicable.

        Raises
        ------
        ClientException
            The parent channel was not cached and returned ``None``.

        Returns
        -------
        Optional[:class:`int`]
            The parent channel's category ID.
        """

        parent = self.parent
        if parent is None:
            raise ClientException("Parent channel not found")
        return parent.category_id

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to this channel.

        .. versionadded:: 2.0
        """
        return f"https://discord.com/channels/{self.guild.id}/{self.id}"

    @property
    def applied_tags(self) -> Optional[List[ForumTag]]:
        """Optional[List[:class:`ForumTag`]]: A list of tags applied to this thread.

        This is ``None`` if the parent channel was not found in cache.

        .. versionadded:: 2.4
        """

        if self.parent is None:
            return None

        parent = self.parent

        if not isinstance(parent, channel.ForumChannel):
            return None

        tags: List[ForumTag] = []

        for tag_id in self.applied_tag_ids:
            tag = parent.get_tag(tag_id)
            if tag is not None:
                tags.append(tag)

        return tags

    def is_private(self) -> bool:
        """:class:`bool`: Whether the thread is a private thread.

        A private thread is only viewable by those that have been explicitly
        invited or have :attr:`~.Permissions.manage_threads`.
        """
        return self._type is ChannelType.private_thread

    def is_news(self) -> bool:
        """:class:`bool`: Whether the thread is a news thread.

        A news thread is a thread that has a parent that is a news channel,
        i.e. :meth:`.TextChannel.is_news` is ``True``.
        """
        return self._type is ChannelType.news_thread

    def is_nsfw(self) -> bool:
        """:class:`bool`: Whether the thread is NSFW or not.

        An NSFW thread is a thread that has a parent that is an NSFW channel,
        i.e. :meth:`.TextChannel.is_nsfw` is ``True``.
        """
        parent = self.parent
        return parent is not None and parent.is_nsfw()

    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        """Handles permission resolution for the :class:`~nextcord.Member`
        or :class:`~nextcord.Role`.

        Since threads do not have their own permissions, they inherit them
        from the parent channel. This is a convenience method for
        calling :meth:`~nextcord.TextChannel.permissions_for` on the
        parent channel.

        Parameters
        ----------
        obj: Union[:class:`~nextcord.Member`, :class:`~nextcord.Role`]
            The object to resolve permissions for. This could be either
            a member or a role. If it's a role then member overwrites
            are not computed.

        Raises
        ------
        ClientException
            The parent channel was not cached and returned ``None``

        Returns
        -------
        :class:`~nextcord.Permissions`
            The resolved permissions for the member or role.
        """

        parent = self.parent
        if parent is None:
            raise ClientException("Parent channel not found")
        return parent.permissions_for(obj)

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

        Usable only by bot accounts.

        Parameters
        ----------
        messages: Iterable[:class:`abc.Snowflake`]
            An iterable of messages denoting which ones to bulk delete.

        Raises
        ------
        ClientException
            The number of messages to delete was more than 100.
        Forbidden
            You do not have proper permissions to delete the messages or
            you're not using a bot account.
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
            message_id = messages[0].id
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
        delete messages even if they are your own (unless you are a user
        account). The :attr:`~Permissions.read_message_history` permission is
        also needed to retrieve message history.

        Examples
        --------

        Deleting bot's messages ::

            def is_me(m):
                return m.author == client.user

            deleted = await thread.purge(limit=100, check=is_me)
            await thread.send(f'Deleted {len(deleted)} message(s)')

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

        async def _single_delete_strategy(messages: Iterable[Message]) -> None:
            for m in messages:
                await m.delete()

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

        # SOme messages remaining to poll
        if count >= 2:
            # more than 2 messages -> bulk delete
            to_delete = ret[-count:]
            await strategy(to_delete)
        elif count == 1:
            # delete a single message
            await ret[-1].delete()

        return ret

    async def edit(
        self,
        *,
        name: str = MISSING,
        archived: bool = MISSING,
        locked: bool = MISSING,
        invitable: bool = MISSING,
        slowmode_delay: int = MISSING,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
        flags: ChannelFlags = MISSING,
        applied_tags: List[ForumTag] = MISSING,
    ) -> Thread:
        """|coro|

        Edits the thread.

        Editing the thread requires :attr:`.Permissions.manage_threads`. The thread
        creator can also edit ``name``, ``archived`` or ``auto_archive_duration``.
        Note that if the thread is locked then only those with :attr:`.Permissions.manage_threads`
        can unarchive a thread.

        The thread must be unarchived to be edited.

        Parameters
        ----------
        name: :class:`str`
            The new name of the thread.
        archived: :class:`bool`
            Whether to archive the thread or not.
        locked: :class:`bool`
            Whether to lock the thread or not.
        invitable: :class:`bool`
            Whether non-moderators can add other non-moderators to this thread.
            Only available for private threads.
        auto_archive_duration: :class:`int`
            The new duration in minutes before a thread is automatically archived for inactivity.
            Must be one of ``60``, ``1440``, ``4320``, or ``10080``.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this thread, in seconds.
            A value of ``0`` disables slowmode. The maximum value possible is ``21600``.
        flags: :class:`ChannelFlags`
            The new channel flags to use for this thread.

            .. versionadded:: 2.1
        applied_tags: List[:class:`ForumTag`]
            The new tags to apply to this thread.

            .. versionadded:: 2.4

        Raises
        ------
        Forbidden
            You do not have permissions to edit the thread.
        HTTPException
            Editing the thread failed.

        Returns
        -------
        :class:`Thread`
            The newly edited thread.
        """
        payload = {}
        if name is not MISSING:
            payload["name"] = str(name)
        if archived is not MISSING:
            payload["archived"] = archived
        if auto_archive_duration is not MISSING:
            payload["auto_archive_duration"] = auto_archive_duration
        if locked is not MISSING:
            payload["locked"] = locked
        if invitable is not MISSING:
            payload["invitable"] = invitable
        if slowmode_delay is not MISSING:
            payload["rate_limit_per_user"] = slowmode_delay
        if flags is not MISSING:
            payload["flags"] = flags.value
        if applied_tags is not MISSING:
            payload["applied_tags"] = [tag.id for tag in applied_tags]

        data = await self._state.http.edit_channel(self.id, **payload)
        # The data payload will always be a Thread payload
        return Thread(data=data, state=self._state, guild=self.guild)  # type: ignore

    async def join(self) -> None:
        """|coro|

        Joins this thread.

        You must have :attr:`~Permissions.send_messages_in_threads` to join a thread.
        If the thread is private, :attr:`~Permissions.manage_threads` is also needed.

        Raises
        ------
        Forbidden
            You do not have permissions to join the thread.
        HTTPException
            Joining the thread failed.
        """
        await self._state.http.join_thread(self.id)

    async def leave(self) -> None:
        """|coro|

        Leaves this thread.

        Raises
        ------
        HTTPException
            Leaving the thread failed.
        """
        await self._state.http.leave_thread(self.id)

    async def add_user(self, user: Snowflake) -> None:
        """|coro|

        Adds a user to this thread.

        You must have :attr:`~Permissions.send_messages` and :attr:`~Permissions.use_threads`
        to add a user to a public thread. If the thread is private then :attr:`~Permissions.send_messages`
        and either :attr:`~Permissions.use_private_threads` or :attr:`~Permissions.manage_messages`
        is required to add a user to the thread.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
            The user to add to the thread.

        Raises
        ------
        Forbidden
            You do not have permissions to add the user to the thread.
        HTTPException
            Adding the user to the thread failed.
        """
        await self._state.http.add_user_to_thread(self.id, user.id)

    async def remove_user(self, user: Snowflake) -> None:
        """|coro|

        Removes a user from this thread.

        You must have :attr:`~Permissions.manage_threads` or be the creator of the thread to remove a user.

        Parameters
        ----------
        user: :class:`abc.Snowflake`
            The user to add to the thread.

        Raises
        ------
        Forbidden
            You do not have permissions to remove the user from the thread.
        HTTPException
            Removing the user from the thread failed.
        """
        await self._state.http.remove_user_from_thread(self.id, user.id)

    async def fetch_members(self) -> List[ThreadMember]:
        """|coro|

        Retrieves all :class:`ThreadMember` that are in this thread.

        This requires :attr:`Intents.members` to get information about members
        other than yourself.

        Raises
        ------
        HTTPException
            Retrieving the members failed.

        Returns
        -------
        List[:class:`ThreadMember`]
            All thread members in the thread.
        """

        members = await self._state.http.get_thread_members(self.id)
        return [ThreadMember(parent=self, data=data) for data in members]

    async def delete(self) -> None:
        """|coro|

        Deletes this thread.

        You must have :attr:`~Permissions.manage_threads` to delete threads.

        Raises
        ------
        Forbidden
            You do not have permissions to delete this thread.
        HTTPException
            Deleting the thread failed.
        """
        await self._state.http.delete_channel(self.id)

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        .. versionadded:: 2.0

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

    def _add_member(self, member: ThreadMember) -> None:
        self._members[member.id] = member

    def _pop_member(self, member_id: int) -> Optional[ThreadMember]:
        return self._members.pop(member_id, None)


class ThreadMember(Hashable):
    """Represents a Discord thread member.

    .. container:: operations

        .. describe:: x == y

            Checks if two thread members are equal.

        .. describe:: x != y

            Checks if two thread members are not equal.

        .. describe:: hash(x)

            Returns the thread member's hash.

        .. describe:: str(x)

            Returns the thread member's name.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The thread member's ID.
    thread_id: :class:`int`
        The thread's ID.
    joined_at: :class:`datetime.datetime`
        The time the member joined the thread in UTC.
    """

    __slots__ = (
        "id",
        "thread_id",
        "joined_at",
        "flags",
        "_state",
        "parent",
    )

    def __init__(self, parent: Thread, data: ThreadMemberPayload) -> None:
        self.parent = parent
        self._state = parent._state
        self._from_data(data)

    def __repr__(self) -> str:
        return (
            f"<ThreadMember id={self.id} thread_id={self.thread_id} joined_at={self.joined_at!r}>"
        )

    def _from_data(self, data: ThreadMemberPayload) -> None:
        try:
            self.id = int(data["user_id"])
        except KeyError:
            assert self._state.self_id is not None
            self.id = self._state.self_id

        try:
            self.thread_id = int(data["id"])
        except KeyError:
            self.thread_id = self.parent.id

        self.joined_at = parse_time(data["join_timestamp"])
        self.flags = data["flags"]

    @property
    def thread(self) -> Thread:
        """:class:`Thread`: The thread this member belongs to."""
        return self.parent

    @property
    def member(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The :class:`Member` of this thread member."""
        return self.parent.guild.get_member(self.id)

    async def fetch_member(self) -> Member:
        """:class:`Member`: Retrieves the :class:`Member` of this thread member.

        .. note::
            This method is an API call. If you have :attr:`Intents.members` and members cache enabled, consider :attr:`member` instead.
        """
        return await self.parent.guild.fetch_member(self.id)
