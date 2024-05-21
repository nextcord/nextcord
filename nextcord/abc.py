# SPDX-License-Identifier: MIT

from __future__ import annotations

import asyncio
import contextlib
import copy
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
    runtime_checkable,
)

from .context_managers import Typing
from .enums import ChannelType
from .errors import ClientException, InvalidArgument
from .file import File
from .flags import ChannelFlags, MessageFlags
from .invite import Invite
from .iterators import HistoryIterator
from .mentions import AllowedMentions
from .partial_emoji import PartialEmoji
from .permissions import PermissionOverwrite, Permissions
from .role import Role
from .sticker import GuildSticker, StickerItem
from .types.components import Component as ComponentPayload
from .utils import MISSING, get, snowflake_time
from .voice_client import VoiceClient, VoiceProtocol

__all__ = (
    "Snowflake",
    "User",
    "PrivateChannel",
    "GuildChannel",
    "Messageable",
    "Connectable",
)

T = TypeVar("T", bound=VoiceProtocol)

if TYPE_CHECKING:
    from datetime import datetime

    from typing_extensions import Self

    from .asset import Asset
    from .channel import (
        CategoryChannel,
        DMChannel,
        GroupChannel,
        PartialMessageable,
        StageChannel,
        TextChannel,
        VoiceChannel,
    )
    from .client import Client
    from .embeds import Embed, EmbedData
    from .enums import InviteTarget
    from .guild import Guild
    from .member import Member
    from .message import Message, MessageReference, PartialMessage
    from .state import ConnectionState
    from .threads import Thread
    from .types.channel import (
        Channel as ChannelPayload,
        GuildChannel as GuildChannelPayload,
        OverwriteType,
        PermissionOverwrite as PermissionOverwritePayload,
    )
    from .types.message import (
        AllowedMentions as AllowedMentionsPayload,
        MessageReference as MessageReferencePayload,
    )
    from .ui.view import View
    from .user import ClientUser

    PartialMessageableChannel = Union[
        TextChannel, Thread, DMChannel, PartialMessageable, VoiceChannel, StageChannel
    ]
    MessageableChannel = Union[PartialMessageableChannel, GroupChannel]
    SnowflakeTime = Union["Snowflake", datetime]


@runtime_checkable
class Snowflake(Protocol):
    """An ABC that details the common operations on a Discord model.

    Almost all :ref:`Discord models <discord_api_models>` meet this
    abstract base class.

    If you want to create a snowflake on your own, consider using
    :class:`.Object`.

    Attributes
    ----------
    id: :class:`int`
        The model's unique ID.
    """

    __slots__ = ()
    id: int


@runtime_checkable
class User(Snowflake, Protocol):
    """An ABC that details the common operations on a Discord user.

    The following implement this ABC:

    - :class:`~nextcord.User`
    - :class:`~nextcord.ClientUser`
    - :class:`~nextcord.Member`

    This ABC must also implement :class:`~nextcord.abc.Snowflake`.

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    global_name: :class:`str`
        The user's global name. This is represented in the UI as "Display Name"

        .. versionadded:: 2.6
    discriminator: :class:`str`
        The user's discriminator.

        .. warning::
            This field is deprecated, and will only return if the user has not yet migrated to the
            new `username <https://dis.gd/usernames>`_ update.
        .. deprecated:: 2.6
    avatar: :class:`~nextcord.Asset`
        The avatar asset the user has.
    bot: :class:`bool`
        If the user is a bot account.
    """

    __slots__ = ()

    name: str
    global_name: str
    discriminator: str
    avatar: Asset
    bot: bool

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name."""
        raise NotImplementedError

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user."""
        raise NotImplementedError


@runtime_checkable
class PrivateChannel(Snowflake, Protocol):
    """An ABC that details the common operations on a private Discord channel.

    The following implement this ABC:

    - :class:`~nextcord.DMChannel`
    - :class:`~nextcord.GroupChannel`

    This ABC must also implement :class:`~nextcord.abc.Snowflake`.

    Attributes
    ----------
    me: :class:`~nextcord.ClientUser`
        The user presenting yourself.
    """

    __slots__ = ()

    me: ClientUser

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the referenced messageable.

        .. versionadded:: 2.0
        """
        return f"https://discord.com/channels/@me/{self.id}"


class _Overwrites:
    __slots__ = ("id", "allow", "deny", "type")

    ROLE = 0
    MEMBER = 1

    def __init__(self, data: PermissionOverwritePayload) -> None:
        self.id: int = int(data["id"])
        self.allow: int = int(data.get("allow", 0))
        self.deny: int = int(data.get("deny", 0))
        self.type: OverwriteType = data["type"]

    def _asdict(self) -> PermissionOverwritePayload:
        return {
            "id": self.id,
            "allow": str(self.allow),
            "deny": str(self.deny),
            "type": self.type,
        }

    def is_role(self) -> bool:
        return self.type == 0

    def is_member(self) -> bool:
        return self.type == 1


GCH = TypeVar("GCH", bound="GuildChannel")


class GuildChannel:
    """An ABC that details the common operations on a Discord guild channel.

    The following implement this ABC:

    - :class:`~nextcord.TextChannel`
    - :class:`~nextcord.VoiceChannel`
    - :class:`~nextcord.CategoryChannel`
    - :class:`~nextcord.StageChannel`
    - :class:`~nextcord.ForumChannel`

    This ABC must also implement :class:`~nextcord.abc.Snowflake`.

    Attributes
    ----------
    name: :class:`str`
        The channel name.
    guild: :class:`~nextcord.Guild`
        The guild the channel belongs to.
    position: :class:`int`
        The position in the channel list.

        .. note::
            Due to API inconsistencies, the position may not mirror the correct UI ordering
    """

    __slots__ = ()

    id: int
    name: str
    guild: Guild
    type: ChannelType
    position: int
    category_id: Optional[int]
    flags: ChannelFlags
    _state: ConnectionState
    _overwrites: List[_Overwrites]

    if TYPE_CHECKING:

        def __init__(
            self, *, state: ConnectionState, guild: Guild, data: GuildChannelPayload
        ) -> None:
            ...

    def __str__(self) -> str:
        return self.name

    @property
    def _sorting_bucket(self) -> int:
        raise NotImplementedError

    def _update(self, guild: Guild, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    async def _move(
        self,
        position: int,
        parent_id: Optional[Any] = None,
        lock_permissions: bool = False,
        *,
        reason: Optional[str],
    ) -> None:
        if position < 0:
            raise InvalidArgument("Channel position cannot be less than 0.")

        http = self._state.http
        bucket = self._sorting_bucket
        channels: List[GuildChannel] = [
            c for c in self.guild.channels if c._sorting_bucket == bucket
        ]

        channels.sort(key=lambda c: c.position)

        try:
            # remove ourselves from the channel list
            channels.remove(self)
        except ValueError:
            # not there somehow lol
            return
        else:
            index = next(
                (i for i, c in enumerate(channels) if c.position >= position), len(channels)
            )
            # add ourselves at our designated position
            channels.insert(index, self)

        payload = []
        for index, c in enumerate(channels):
            d: Dict[str, Any] = {"id": c.id, "position": index}
            if parent_id is not MISSING and c.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=lock_permissions)
            payload.append(d)

        await http.bulk_channel_update(self.guild.id, payload, reason=reason)

    async def _edit(
        self, options: Dict[str, Any], reason: Optional[str]
    ) -> Optional[ChannelPayload]:
        try:
            parent = options.pop("category")
        except KeyError:
            parent_id = MISSING
        else:
            parent_id = parent and parent.id

        with contextlib.suppress(KeyError):
            options["rate_limit_per_user"] = options.pop("slowmode_delay")

        try:
            rtc_region = options.pop("rtc_region")
        except KeyError:
            pass
        else:
            options["rtc_region"] = None if rtc_region is None else str(rtc_region)

        try:
            video_quality_mode = options.pop("video_quality_mode")
        except KeyError:
            pass
        else:
            options["video_quality_mode"] = int(video_quality_mode)

        try:
            default_sort_order = options.pop("default_sort_order")
        except KeyError:
            pass
        else:
            options["default_sort_order"] = default_sort_order.value

        try:
            default_forum_layout = options.pop("default_forum_layout")
        except KeyError:
            pass
        else:
            options["default_forum_layout"] = default_forum_layout.value

        lock_permissions = options.pop("sync_permissions", False)

        try:
            position = options.pop("position")
        except KeyError:
            if parent_id is not MISSING:
                if lock_permissions:
                    category = self.guild.get_channel(parent_id)
                    if category:
                        options["permission_overwrites"] = [
                            c._asdict() for c in category._overwrites
                        ]
                options["parent_id"] = parent_id
            elif lock_permissions and self.category_id is not None:
                # if we're syncing permissions on a pre-existing channel category without changing it
                # we need to update the permissions to point to the pre-existing category
                category = self.guild.get_channel(self.category_id)
                if category:
                    options["permission_overwrites"] = [c._asdict() for c in category._overwrites]
        else:
            await self._move(
                position, parent_id=parent_id, lock_permissions=lock_permissions, reason=reason
            )

        overwrites = options.get("overwrites", None)
        if overwrites is not None:
            perms = []
            for target, perm in overwrites.items():
                if not isinstance(perm, PermissionOverwrite):
                    raise InvalidArgument(
                        f"Expected PermissionOverwrite received {perm.__class__.__name__}"
                    )

                allow, deny = perm.pair()
                payload = {
                    "allow": allow.value,
                    "deny": deny.value,
                    "id": target.id,
                }

                if isinstance(target, Role):
                    payload["type"] = _Overwrites.ROLE
                else:
                    payload["type"] = _Overwrites.MEMBER

                perms.append(payload)
            options["permission_overwrites"] = perms

        try:
            ch_type = options["type"]
        except KeyError:
            pass
        else:
            if not isinstance(ch_type, ChannelType):
                raise InvalidArgument("type field must be of type ChannelType")
            options["type"] = ch_type.value

        with contextlib.suppress(KeyError):
            options["default_thread_rate_limit_per_user"] = options.pop(
                "default_thread_slowmode_delay"
            )

        try:
            default_reaction = options.pop("default_reaction")
        except KeyError:
            pass
        else:
            if default_reaction is None:
                options["default_reaction_emoji"] = None
            else:
                if isinstance(default_reaction, str):
                    default_reaction = PartialEmoji.from_str(default_reaction)
                options["default_reaction_emoji"] = (
                    {
                        "emoji_id": default_reaction.id,
                    }
                    if default_reaction.id is not None
                    else {
                        "emoji_name": default_reaction.name,
                    }
                )

        try:
            available_tags = options.pop("available_tags")
        except KeyError:
            pass
        else:
            options["available_tags"] = [tag.payload for tag in available_tags]

        if options:
            return await self._state.http.edit_channel(self.id, reason=reason, **options)
        return None

    def _fill_overwrites(self, data: GuildChannelPayload) -> None:
        self._overwrites = []
        everyone_index = 0
        everyone_id = self.guild.id

        for index, overridden in enumerate(data.get("permission_overwrites", [])):
            overwrite = _Overwrites(overridden)
            self._overwrites.append(overwrite)

            if overwrite.type == _Overwrites.MEMBER:
                continue

            if overwrite.id == everyone_id:
                # the @everyone role is not guaranteed to be the first one
                # in the list of permission overwrites, however the permission
                # resolution code kind of requires that it is the first one in
                # the list since it is special. So we need the index so we can
                # swap it to be the first one.
                everyone_index = index

        # do the swap
        tmp = self._overwrites
        if tmp:
            tmp[everyone_index], tmp[0] = tmp[0], tmp[everyone_index]

    @property
    def changed_roles(self) -> List[Role]:
        """List[:class:`~nextcord.Role`]: Returns a list of roles that have been overridden from
        their default values in the :attr:`~nextcord.Guild.roles` attribute."""
        ret = []
        g = self.guild
        for overwrite in filter(lambda o: o.is_role(), self._overwrites):
            role = g.get_role(overwrite.id)
            if role is None:
                continue

            role = copy.copy(role)
            role.permissions.handle_overwrite(overwrite.allow, overwrite.deny)
            ret.append(role)
        return ret

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the channel."""
        return f"<#{self.id}>"

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return snowflake_time(self.id)

    def overwrites_for(self, obj: Union[Role, User]) -> PermissionOverwrite:
        """Returns the channel-specific overwrites for a member or a role.

        Parameters
        ----------
        obj: Union[:class:`~nextcord.Role`, :class:`~nextcord.abc.User`]
            The role or user denoting
            whose overwrite to get.

        Returns
        -------
        :class:`~nextcord.PermissionOverwrite`
            The permission overwrites for this object.
        """
        predicate: Callable[[_Overwrites], bool]

        if isinstance(obj, User):
            predicate = lambda p: p.is_member()
        elif isinstance(obj, Role):
            predicate = lambda p: p.is_role()
        else:
            predicate = lambda _: True

        for overwrite in filter(predicate, self._overwrites):
            if overwrite.id == obj.id:
                allow = Permissions(overwrite.allow)
                deny = Permissions(overwrite.deny)
                return PermissionOverwrite.from_pair(allow, deny)

        return PermissionOverwrite()

    @property
    def overwrites(self) -> Dict[Union[Role, Member], PermissionOverwrite]:
        """Returns all of the channel's overwrites.

        This is returned as a dictionary where the key contains the target which
        can be either a :class:`~nextcord.Role` or a :class:`~nextcord.Member` and the value is the
        overwrite as a :class:`~nextcord.PermissionOverwrite`.

        Returns
        -------
        Dict[Union[:class:`~nextcord.Role`, :class:`~nextcord.Member`], :class:`~nextcord.PermissionOverwrite`]
            The channel's permission overwrites.
        """
        ret = {}
        for ow in self._overwrites:
            allow = Permissions(ow.allow)
            deny = Permissions(ow.deny)
            overwrite = PermissionOverwrite.from_pair(allow, deny)
            target = None

            if ow.is_role():
                target = self.guild.get_role(ow.id)
            elif ow.is_member():
                target = self.guild.get_member(ow.id)

            # TODO: There is potential data loss here in the non-chunked
            # case, i.e. target is None because get_member returned nothing.
            # This can be fixed with a slight breaking change to the return type,
            # i.e. adding nextcord.Object to the list of it
            # However, for now this is an acceptable compromise.
            if target is not None:
                ret[target] = overwrite
        return ret

    @property
    def category(self) -> Optional[CategoryChannel]:
        """Optional[:class:`~nextcord.CategoryChannel`]: The category this channel belongs to.

        If there is no category then this is ``None``.
        """
        return self.guild.get_channel(self.category_id)  # type: ignore

    @property
    def permissions_synced(self) -> bool:
        """:class:`bool`: Whether or not the permissions for this channel are synced with the
        category it belongs to.

        If there is no category then this is ``False``.

        .. versionadded:: 1.3
        """
        if self.category_id is None:
            return False

        category = self.guild.get_channel(self.category_id)
        return bool(category and category.overwrites == self.overwrites)

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to this channel.

        .. versionadded:: 2.0
        """
        return f"https://discord.com/channels/{self.guild.id}/{self.id}"

    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        """Handles permission resolution for the :class:`~nextcord.Member`
        or :class:`~nextcord.Role`.

        This function takes into consideration the following cases:

        - Guild owner
        - Guild roles
        - Channel overrides
        - Member overrides
        - Timed-out members

        If a :class:`~nextcord.Role` is passed, then it checks the permissions
        someone with that role would have, which is essentially:

        - The default role permissions
        - The permissions of the role used as a parameter
        - The default role permission overwrites
        - The permission overwrites of the role used as a parameter

        .. versionchanged:: 2.3
            Only ``view_channel`` and ``read_message_history`` can be returned for timed-out members

        .. versionchanged:: 2.0
            The object passed in can now be a role object.

        Parameters
        ----------
        obj: Union[:class:`~nextcord.Member`, :class:`~nextcord.Role`]
            The object to resolve permissions for. This could be either
            a member or a role. If it's a role then member overwrites
            are not computed.

        Returns
        -------
        :class:`~nextcord.Permissions`
            The resolved permissions for the member or role.
        """

        # The current cases can be explained as:
        # Guild owner get all permissions -- no questions asked. Otherwise...
        # The @everyone role gets the first application.
        # After that, the applied roles that the user has in the channel
        # (or otherwise) are then OR'd together.
        # After the role permissions are resolved, the member permissions
        # have to take into effect.
        # After all that is done.. you have to do the following:

        # If manage permissions is True, then all permissions are set to True.

        # The operation first takes into consideration the denied
        # and then the allowed.

        if self.guild.owner_id == obj.id:
            return Permissions.all()

        default = self.guild.default_role
        base = Permissions(default.permissions.value)

        # Handle the role case first
        if isinstance(obj, Role):
            base.value |= obj._permissions

            if base.administrator:
                return Permissions.all()

            # Apply @everyone allow/deny first since it's special
            try:
                maybe_everyone = self._overwrites[0]
                if maybe_everyone.id == self.guild.id:
                    base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
            except IndexError:
                pass

            if obj.is_default():
                return base

            overwrite = get(self._overwrites, type=_Overwrites.ROLE, id=obj.id)
            if overwrite is not None:
                base.handle_overwrite(overwrite.allow, overwrite.deny)

            return base

        roles = obj._roles
        get_role = self.guild.get_role

        # Apply guild roles that the member has.
        for role_id in roles:
            role = get_role(role_id)
            if role is not None:
                base.value |= role._permissions

        # Guild-wide Administrator -> True for everything
        # Bypass all channel-specific overrides
        if base.administrator:
            return Permissions.all()

        # Apply @everyone allow/deny first since it's special
        try:
            maybe_everyone = self._overwrites[0]
            if maybe_everyone.id == self.guild.id:
                base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
                remaining_overwrites = self._overwrites[1:]
            else:
                remaining_overwrites = self._overwrites
        except IndexError:
            remaining_overwrites = self._overwrites

        denies = 0
        allows = 0

        # Apply channel specific role permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.is_role() and roles.has(overwrite.id):
                denies |= overwrite.deny
                allows |= overwrite.allow

        base.handle_overwrite(allow=allows, deny=denies)

        # Apply member specific permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.is_member() and overwrite.id == obj.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break

        # if you can't send a message in a channel then you can't have certain
        # permissions as well
        if not base.send_messages:
            base.send_tts_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False

        # if you can't read a channel then you have no permissions there
        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value

        # if you are timed out then you lose all permissions except view_channel and read_message_history
        if obj.communication_disabled_until is not None:
            allowed = Permissions(view_channel=True, read_message_history=True)
            base.value &= allowed.value

        return base

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the channel.

        You must have :attr:`~nextcord.Permissions.manage_channels` permission to use this.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for deleting this channel.
            Shows up on the audit log.

        Raises
        ------
        ~nextcord.Forbidden
            You do not have proper permissions to delete the channel.
        ~nextcord.NotFound
            The channel was not found or was already deleted.
        ~nextcord.HTTPException
            Deleting the channel failed.
        """
        await self._state.http.delete_channel(self.id, reason=reason)

    @overload
    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        overwrite: Optional[PermissionOverwrite] = ...,
        reason: Optional[str] = ...,
    ) -> None:
        ...

    @overload
    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        reason: Optional[str] = ...,
        **permissions: bool,
    ) -> None:
        ...

    async def set_permissions(
        self,
        target: Union[Member, Role],
        *,
        reason: Optional[str] = None,
        **kwargs: Any,
    ):
        r"""|coro|

        Sets the channel specific permission overwrites for a target in the
        channel.

        The ``target`` parameter should either be a :class:`~nextcord.Member` or a
        :class:`~nextcord.Role` that belongs to guild.

        The ``overwrite`` parameter, if given, must either be ``None`` or
        :class:`~nextcord.PermissionOverwrite`. For convenience, you can pass in
        keyword arguments denoting :class:`~nextcord.Permissions` attributes. If this is
        done, then you cannot mix the keyword arguments with the ``overwrite``
        parameter.

        If the ``overwrite`` parameter is ``None``, then the permission
        overwrites are deleted.

        You must have the :attr:`~nextcord.Permissions.manage_roles` permission to use this.

        .. note::

            This method *replaces* the old overwrites with the ones given.

        Examples
        --------

        Setting allow and deny: ::

            await message.channel.set_permissions(message.author, read_messages=True,
                                                                  send_messages=False)

        Deleting overwrites ::

            await channel.set_permissions(member, overwrite=None)

        Using :class:`~nextcord.PermissionOverwrite` ::

            overwrite = nextcord.PermissionOverwrite()
            overwrite.send_messages = False
            overwrite.read_messages = True
            await channel.set_permissions(member, overwrite=overwrite)

        Parameters
        ----------
        target: Union[:class:`~nextcord.Member`, :class:`~nextcord.Role`]
            The member or role to overwrite permissions for.
        overwrite: Optional[:class:`~nextcord.PermissionOverwrite`]
            The permissions to allow and deny to the target, or ``None`` to
            delete the overwrite.
        \*\*permissions
            A keyword argument list of permissions to set for ease of use.
            Cannot be mixed with ``overwrite``.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.

        Raises
        ------
        ~nextcord.Forbidden
            You do not have permissions to edit channel specific permissions.
        ~nextcord.HTTPException
            Editing channel specific permissions failed.
        ~nextcord.NotFound
            The role or member being edited is not part of the guild.
        ~nextcord.InvalidArgument
            The overwrite parameter invalid or the target type was not
            :class:`~nextcord.Role` or :class:`~nextcord.Member`.
        """

        http = self._state.http
        overwrite: Optional[PermissionOverwrite] = kwargs.pop("overwrite", MISSING)
        permissions: Dict[str, bool] = kwargs

        if isinstance(target, User):
            perm_type = _Overwrites.MEMBER
        elif isinstance(target, Role):
            perm_type = _Overwrites.ROLE
        else:
            raise InvalidArgument("target parameter must be either Member or Role")

        if overwrite is MISSING:
            if len(permissions) == 0:
                raise InvalidArgument("No overwrite provided.")
            try:
                overwrite = PermissionOverwrite(**permissions)
            except (ValueError, TypeError) as e:
                raise InvalidArgument("Invalid permissions given to keyword arguments.") from e
        elif len(permissions) > 0:
            raise InvalidArgument("Cannot mix overwrite and keyword arguments.")

        # TODO: wait for event

        if overwrite is None:
            await http.delete_channel_permissions(self.id, target.id, reason=reason)
        elif isinstance(overwrite, PermissionOverwrite):
            (allow, deny) = overwrite.pair()
            await http.edit_channel_permissions(
                self.id, target.id, str(allow.value), str(deny.value), perm_type, reason=reason
            )
        else:
            raise InvalidArgument("Invalid overwrite type provided.")

    async def _clone_impl(
        self,
        base_attrs: Dict[str, Any],
        *,
        name: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Self:
        base_attrs["permission_overwrites"] = [x._asdict() for x in self._overwrites]
        base_attrs["parent_id"] = self.category_id
        base_attrs["name"] = name or self.name
        guild_id = self.guild.id
        cls = self.__class__
        data = await self._state.http.create_channel(
            guild_id, self.type.value, reason=reason, **base_attrs
        )
        obj = cls(state=self._state, guild=self.guild, data=data)

        # temporarily add it to the cache
        self.guild._channels[obj.id] = obj  # type: ignore
        return obj

    async def clone(self, *, name: Optional[str] = None, reason: Optional[str] = None) -> Self:
        """|coro|

        Clones this channel. This creates a channel with the same properties
        as this channel.

        You must have the :attr:`~nextcord.Permissions.manage_channels` permission to
        do this.

        .. versionadded:: 1.1

        Parameters
        ----------
        name: Optional[:class:`str`]
            The name of the new channel. If not provided, defaults to this
            channel name.
        reason: Optional[:class:`str`]
            The reason for cloning this channel. Shows up on the audit log.

        Raises
        ------
        ~nextcord.Forbidden
            You do not have the proper permissions to create this channel.
        ~nextcord.HTTPException
            Creating the channel failed.

        Returns
        -------
        :class:`.abc.GuildChannel`
            The channel that was created.
        """
        raise NotImplementedError

    @overload
    async def move(
        self,
        *,
        beginning: bool,
        offset: int = ...,
        category: Optional[Snowflake] = ...,
        sync_permissions: bool = ...,
        reason: Optional[str] = None,
    ) -> None:
        ...

    @overload
    async def move(
        self,
        *,
        end: bool,
        offset: int = ...,
        category: Optional[Snowflake] = ...,
        sync_permissions: bool = ...,
        reason: Optional[str] = None,
    ) -> None:
        ...

    @overload
    async def move(
        self,
        *,
        before: Snowflake,
        offset: int = ...,
        category: Optional[Snowflake] = ...,
        sync_permissions: bool = ...,
        reason: Optional[str] = None,
    ) -> None:
        ...

    @overload
    async def move(
        self,
        *,
        after: Snowflake,
        offset: int = ...,
        category: Optional[Snowflake] = ...,
        sync_permissions: bool = ...,
        reason: Optional[str] = None,
    ) -> None:
        ...

    async def move(
        self,
        *,
        beginning: Optional[bool] = None,
        end: Optional[bool] = None,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
        offset: int = 0,
        category: Optional[Snowflake] = MISSING,
        sync_permissions: bool = False,
        reason: Optional[str] = None,
    ) -> None:
        """|coro|

        A rich interface to help move a channel relative to other channels.

        If exact position movement is required, ``edit`` should be used instead.

        You must have the :attr:`~nextcord.Permissions.manage_channels` permission to
        do this.

        .. note::

            Voice channels will always be sorted below text channels.
            This is a Discord limitation.

        .. versionadded:: 1.7

        .. versionchanged:: 2.4

            ``beginning``, ``end``, ``before``, ``after`` and ``reason`` now accept ``None``.

        Parameters
        ----------
        beginning: Optional[:class:`bool`]
            Whether to move the channel to the beginning of the
            channel list (or category if given).
            This is mutually exclusive with ``end``, ``before``, and ``after``.
        end: Optional[:class:`bool`]
            Whether to move the channel to the end of the
            channel list (or category if given).
            This is mutually exclusive with ``beginning``, ``before``, and ``after``.
        before: Optional[:class:`~nextcord.abc.Snowflake`]
            The channel that should be before our current channel.
            This is mutually exclusive with ``beginning``, ``end``, and ``after``.
        after: Optional[:class:`~nextcord.abc.Snowflake`]
            The channel that should be after our current channel.
            This is mutually exclusive with ``beginning``, ``end``, and ``before``.
        offset: :class:`int`
            The number of channels to offset the move by. For example,
            an offset of ``2`` with ``beginning=True`` would move
            it 2 after the beginning. A positive number moves it below
            while a negative number moves it above. Note that this
            number is relative and computed after the ``beginning``,
            ``end``, ``before``, and ``after`` parameters.
        category: Optional[:class:`~nextcord.abc.Snowflake`]
            The category to move this channel under.
            If ``None`` is given then it moves it out of the category.
            This parameter is ignored if moving a category channel.
        sync_permissions: :class:`bool`
            Whether to sync the permissions with the category (if given).
        reason: Optional[:class:`str`]
            The reason for the move.

        Raises
        ------
        InvalidArgument
            An invalid position was given or a bad mix of arguments were passed.
        Forbidden
            You do not have permissions to move the channel.
        HTTPException
            Moving the channel failed.
        """

        if sum(bool(a) for a in (beginning, end, before, after)) > 1:
            raise InvalidArgument("Only one of [before, after, end, beginning] can be used.")

        bucket = self._sorting_bucket
        channels: List[GuildChannel]
        if category:
            parent_id = category.id
            channels = [
                ch
                for ch in self.guild.channels
                if ch._sorting_bucket == bucket and ch.category_id == parent_id
            ]
        else:
            parent_id = None
            channels = [
                ch
                for ch in self.guild.channels
                if ch._sorting_bucket == bucket and ch.category_id == self.category_id
            ]

        channels.sort(key=lambda c: (c.position, c.id))

        with contextlib.suppress(ValueError):
            # Try to remove ourselves from the channel list
            # If we're not there then it's probably due to not being in the category
            channels.remove(self)

        index = None
        if beginning:
            index = 0
        elif end:
            index = len(channels)
        elif before:
            index = next((i for i, c in enumerate(channels) if c.id == before.id), None)
        elif after:
            index = next((i + 1 for i, c in enumerate(channels) if c.id == after.id), None)

        if index is None:
            raise InvalidArgument("Could not resolve appropriate move position")

        channels.insert(max((index + offset), 0), self)
        payload = []

        for index, channel in enumerate(channels):
            d: Dict[str, Any] = {"id": channel.id, "position": index}
            if category is not MISSING and channel.id == self.id:
                d.update(parent_id=parent_id, lock_permissions=sync_permissions)
            payload.append(d)

        await self._state.http.bulk_channel_update(self.guild.id, payload, reason=reason)

    async def create_invite(
        self,
        *,
        reason: Optional[str] = None,
        max_age: int = 0,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = True,
        target_type: Optional[InviteTarget] = None,
        target_user: Optional[User] = None,
        target_application_id: Optional[int] = None,
    ) -> Invite:
        """|coro|

        Creates an instant invite from a text or voice channel.

        You must have the :attr:`~nextcord.Permissions.create_instant_invite` permission to
        do this.

        Parameters
        ----------
        max_age: :class:`int`
            How long the invite should last in seconds. If it's 0 then the invite
            doesn't expire. Defaults to ``0``.
        max_uses: :class:`int`
            How many uses the invite could be used for. If it's 0 then there
            are unlimited uses. Defaults to ``0``.
        temporary: :class:`bool`
            Denotes that the invite grants temporary membership
            (i.e. they get kicked after they disconnect). Defaults to ``False``.
        unique: :class:`bool`
            Indicates if a unique invite URL should be created. Defaults to True.
            If this is set to ``False`` then it will return a previously created
            invite.
        reason: Optional[:class:`str`]
            The reason for creating this invite. Shows up on the audit log.
        target_type: Optional[:class:`.InviteTarget`]
            The type of target for the voice channel invite, if any.

            .. versionadded:: 2.0

        target_user: Optional[:class:`User`]
            The user whose stream to display for this invite, required if ``target_type``
            is :attr:`.InviteTarget.stream`. The user must be streaming in the channel.

            .. versionadded:: 2.0

        target_application_id:: Optional[:class:`int`]
            The id of the embedded application for the invite, required if ``target_type``
            is :attr:`.InviteTarget.embedded_application`.

            .. versionadded:: 2.0

        Raises
        ------
        ~nextcord.HTTPException
            Invite creation failed.

        ~nextcord.NotFound
            The channel that was passed is a category or an invalid channel.

        Returns
        -------
        :class:`~nextcord.Invite`
            The invite that was created.
        """

        data = await self._state.http.create_invite(
            self.id,
            reason=reason,
            max_age=max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            target_type=target_type.value if target_type else None,
            target_user_id=target_user.id if target_user else None,
            target_application_id=target_application_id,
        )
        return Invite.from_incomplete(data=data, state=self._state)

    async def invites(self) -> List[Invite]:
        """|coro|

        Returns a list of all active instant invites from this channel.

        You must have :attr:`~nextcord.Permissions.manage_channels` to get this information.

        Raises
        ------
        ~nextcord.Forbidden
            You do not have proper permissions to get the information.
        ~nextcord.HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        List[:class:`~nextcord.Invite`]
            The list of invites that are currently active.
        """

        state = self._state
        data = await state.http.invites_from_channel(self.id)
        guild = self.guild
        return [Invite(state=state, data=invite, channel=self, guild=guild) for invite in data]


class Messageable:
    """An ABC that details the common operations on a model that can send messages.

    The following implement this ABC:

    - :class:`~nextcord.TextChannel`
    - :class:`~nextcord.DMChannel`
    - :class:`~nextcord.GroupChannel`
    - :class:`~nextcord.VoiceChannel`
    - :class:`~nextcord.StageChannel`
    - :class:`~nextcord.User`
    - :class:`~nextcord.Member`
    - :class:`~nextcord.ext.commands.Context`
    - :class:`~nextcord.Thread`
    """

    __slots__ = ()
    _state: ConnectionState

    async def _get_channel(self) -> MessageableChannel:
        raise NotImplementedError

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embed: Embed = ...,
        file: File = ...,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = ...,
        delete_after: Optional[float] = ...,
        nonce: Optional[Union[str, int]] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = ...,
        mention_author: Optional[bool] = ...,
        view: Optional[View] = ...,
        flags: Optional[MessageFlags] = ...,
        suppress_embeds: Optional[bool] = ...,
    ) -> Message:
        ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embed: Embed = ...,
        files: List[File] = ...,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = ...,
        delete_after: Optional[float] = ...,
        nonce: Optional[Union[str, int]] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = ...,
        mention_author: Optional[bool] = ...,
        view: Optional[View] = ...,
        flags: Optional[MessageFlags] = ...,
        suppress_embeds: Optional[bool] = ...,
    ) -> Message:
        ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embeds: List[Embed] = ...,
        file: File = ...,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = ...,
        delete_after: Optional[float] = ...,
        nonce: Optional[Union[str, int]] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = ...,
        mention_author: Optional[bool] = ...,
        view: Optional[View] = ...,
        flags: Optional[MessageFlags] = ...,
        suppress_embeds: Optional[bool] = ...,
    ) -> Message:
        ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embeds: List[Embed] = ...,
        files: List[File] = ...,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = ...,
        delete_after: Optional[float] = ...,
        nonce: Optional[Union[str, int]] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = ...,
        mention_author: Optional[bool] = ...,
        view: Optional[View] = ...,
        flags: Optional[MessageFlags] = ...,
        suppress_embeds: Optional[bool] = ...,
    ) -> Message:
        ...

    async def send(
        self,
        content: Optional[str] = None,
        *,
        tts: bool = False,
        embed: Optional[Embed] = None,
        embeds: Optional[List[Embed]] = None,
        file: Optional[File] = None,
        files: Optional[List[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = None,
        mention_author: Optional[bool] = None,
        view: Optional[View] = None,
        flags: Optional[MessageFlags] = None,
        suppress_embeds: Optional[bool] = None,
    ):
        """|coro|

        Sends a message to the destination with the content given.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` or ``embeds``
        parameter must be provided.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`~nextcord.File` object. To upload multiple files, the ``files``
        parameter should be used with a :class:`list` of :class:`~nextcord.File` objects.
        **Specifying both parameters will lead to an exception**.

        To upload a single embed, the ``embed`` parameter should be used with a
        single :class:`~nextcord.Embed` object. To upload multiple embeds, the ``embeds``
        parameter should be used with a :class:`list` of :class:`~nextcord.Embed` objects.
        **Specifying both parameters will lead to an exception**.

        Parameters
        ----------
        content: Optional[:class:`str`]
            The content of the message to send.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        embed: :class:`~nextcord.Embed`
            The rich embed for the content.
        file: :class:`~nextcord.File`
            The file to upload.
        files: List[:class:`~nextcord.File`]
            A list of files to upload. Must be a maximum of 10.
        nonce: Union[:class:`int`, :class:`str`]
            The nonce to use for sending this message. If the message was successfully sent,
            then the message will have a nonce with this value.
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: :class:`~nextcord.AllowedMentions`
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~nextcord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~nextcord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~nextcord.Client.allowed_mentions`
            are used instead.

            .. versionadded:: 1.4

        reference: Union[:class:`~nextcord.Message`, :class:`~nextcord.MessageReference`, :class:`~nextcord.PartialMessage`]
            A reference to the :class:`~nextcord.Message` to which you are replying, this can be created using
            :meth:`~nextcord.Message.to_reference` or passed directly as a :class:`~nextcord.Message`. You can control
            whether this mentions the author of the referenced message using the :attr:`~nextcord.AllowedMentions.replied_user`
            attribute of ``allowed_mentions`` or by setting ``mention_author``.

            .. versionadded:: 1.6

        mention_author: Optional[:class:`bool`]
            If set, overrides the :attr:`~nextcord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.

            .. versionadded:: 1.6
        view: :class:`nextcord.ui.View`
            A Discord UI View to add to the message.
        embeds: List[:class:`~nextcord.Embed`]
            A list of embeds to upload. Must be a maximum of 10.

            .. versionadded:: 2.0
        stickers: Sequence[Union[:class:`~nextcord.GuildSticker`, :class:`~nextcord.StickerItem`]]
            A list of stickers to upload. Must be a maximum of 3.

            .. versionadded:: 2.0
        flags: Optional[:class:`~nextcord.MessageFlags`]
            The message flags being set for this message.
            Currently only :class:`~nextcord.MessageFlags.suppress_embeds` is able to be set.

            .. versionadded:: 2.4
        suppress_embeds: Optional[:class:`bool`]
            Whether to suppress embeds on this message.

            .. versionadded:: 2.4

        Raises
        ------
        ~nextcord.HTTPException
            Sending the message failed.
        ~nextcord.Forbidden
            You do not have the proper permissions to send the message.
        ~nextcord.InvalidArgument
            The ``files`` list is not of the appropriate size,
            you specified both ``file`` and ``files``,
            or you specified both ``embed`` and ``embeds``,
            or the ``reference`` object is not a :class:`~nextcord.Message`,
            :class:`~nextcord.MessageReference` or :class:`~nextcord.PartialMessage`

        Returns
        -------
        :class:`~nextcord.Message`
            The message that was sent.
        """

        channel = await self._get_channel()
        state = self._state
        content = str(content) if content is not None else None
        if flags is None:
            flags = MessageFlags()
        if suppress_embeds is not None:
            flags.suppress_embeds = suppress_embeds

        flag_value: Optional[int] = flags.value if flags.value != 0 else None

        embed_payload: Optional[EmbedData] = None
        embeds_payload: Optional[List[EmbedData]] = None
        stickers_payload: Optional[List[int]] = None
        reference_payload: Optional[MessageReferencePayload] = None
        allowed_mentions_payload: Optional[AllowedMentionsPayload] = None

        if embed is not None and embeds is not None:
            raise InvalidArgument("Cannot pass both embed and embeds parameter to send()")

        if embed is not None:
            embed_payload = embed.to_dict()

        elif embeds is not None:
            embeds_payload = [em.to_dict() for em in embeds]

        if stickers is not None:
            stickers_payload = [sticker.id for sticker in stickers]

        if allowed_mentions is not None:
            if state.allowed_mentions is not None:
                allowed_mentions_payload = state.allowed_mentions.merge(allowed_mentions).to_dict()
            else:
                allowed_mentions_payload = allowed_mentions.to_dict()
        else:
            allowed_mentions_payload = state.allowed_mentions and state.allowed_mentions.to_dict()

        if mention_author is not None:
            allowed_mentions_payload = allowed_mentions_payload or AllowedMentions().to_dict()
            allowed_mentions_payload["replied_user"] = bool(mention_author)

        if reference is not None:
            try:
                reference_payload = reference.to_message_reference_dict()
            except AttributeError:
                raise InvalidArgument(
                    "reference parameter must be Message, MessageReference, or PartialMessage"
                ) from None

        components: Optional[List[ComponentPayload]] = None
        if view:
            if not hasattr(view, "__discord_ui_view__"):
                raise InvalidArgument(f"view parameter must be View not {view.__class__!r}")

            components = cast(List[ComponentPayload], view.to_components())

        if file is not None and files is not None:
            raise InvalidArgument("Cannot pass both file and files parameter to send()")

        if file is not None:
            if not isinstance(file, File):
                raise InvalidArgument("file parameter must be File")

            try:
                data = await state.http.send_files(
                    channel.id,
                    files=[file],
                    allowed_mentions=allowed_mentions_payload,
                    content=content,
                    tts=tts,
                    embed=embed_payload,
                    embeds=embeds_payload,
                    nonce=nonce,
                    message_reference=reference_payload,
                    stickers=stickers_payload,
                    components=components,
                    flags=flag_value,
                )
            finally:
                file.close()

        elif files is not None:
            if not all(isinstance(file, File) for file in files):
                raise TypeError("Files parameter must be a list of type File")

            try:
                data = await state.http.send_files(
                    channel.id,
                    files=files,
                    content=content,
                    tts=tts,
                    embed=embed_payload,
                    embeds=embeds_payload,
                    nonce=nonce,
                    allowed_mentions=allowed_mentions_payload,
                    message_reference=reference_payload,
                    stickers=stickers_payload,
                    components=components,
                    flags=flag_value,
                )
            finally:
                for f in files:
                    f.close()
        else:
            data = await state.http.send_message(
                channel.id,
                content,
                tts=tts,
                embed=embed_payload,
                embeds=embeds_payload,
                nonce=nonce,
                allowed_mentions=allowed_mentions_payload,
                message_reference=reference_payload,
                stickers=stickers_payload,
                components=components,
                flags=flag_value,
            )

        ret = state.create_message(channel=channel, data=data)
        if view and view.prevent_update:
            state.store_view(view, ret.id)

        if delete_after is not None:
            await ret.delete(delay=delete_after)
        return ret

    async def trigger_typing(self) -> None:
        """|coro|

        Triggers a *typing* indicator to the destination.

        *Typing* indicator will go away after 10 seconds, or after a message is sent.
        """

        channel = await self._get_channel()
        await self._state.http.send_typing(channel.id)

    def typing(self) -> Typing:
        """Returns a context manager that allows you to type for an indefinite period of time.

        This is useful for denoting long computations in your bot.

        .. note::

            This is both a regular context manager and an async context manager.
            This means that both ``with`` and ``async with`` work with this.

        Example Usage: ::

            async with channel.typing():
                # simulate something heavy
                await asyncio.sleep(10)

            await channel.send('done!')

        """
        return Typing(self)

    async def fetch_message(self, id: int, /) -> Message:
        """|coro|

        Retrieves a single :class:`~nextcord.Message` from the destination.

        Parameters
        ----------
        id: :class:`int`
            The message ID to look for.

        Raises
        ------
        ~nextcord.NotFound
            The specified message was not found.
        ~nextcord.Forbidden
            You do not have the permissions required to get a message.
        ~nextcord.HTTPException
            Retrieving the message failed.

        Returns
        -------
        :class:`~nextcord.Message`
            The message asked for.
        """

        channel = await self._get_channel()
        data = await self._state.http.get_message(channel.id, id)
        return self._state.create_message(channel=channel, data=data)

    def history(
        self,
        *,
        limit: Optional[int] = 100,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        around: Optional[SnowflakeTime] = None,
        oldest_first: Optional[bool] = None,
    ) -> HistoryIterator:
        """Returns an :class:`~nextcord.AsyncIterator` that enables receiving the destination's message history.

        You must have :attr:`~nextcord.Permissions.read_message_history` permissions to use this.

        Examples
        --------

        Usage ::

            counter = 0
            async for message in channel.history(limit=200):
                if message.author == client.user:
                    counter += 1

        Flattening into a list: ::

            messages = await channel.history(limit=123).flatten()
            # messages is now a list of Message...

        All parameters are optional.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of messages to retrieve.
            If ``None``, retrieves every message in the channel. Note, however,
            that this would make it a slow operation.
        before: Optional[Union[:class:`~nextcord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages before this date or message.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Optional[Union[:class:`~nextcord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages after this date or message.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        around: Optional[Union[:class:`~nextcord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages around this date or message.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
            When using this argument, the maximum limit is 101. Note that if the limit is an
            even number then this will return at most limit + 1 messages.
        oldest_first: Optional[:class:`bool`]
            If set to ``True``, return messages in oldest->newest order. Defaults to ``True`` if
            ``after`` is specified, otherwise ``False``.

        Raises
        ------
        ~nextcord.Forbidden
            You do not have permissions to get channel message history.
        ~nextcord.HTTPException
            The request to get message history failed.

        Yields
        ------
        :class:`~nextcord.Message`
            The message with the message data parsed.
        """
        return HistoryIterator(
            self, limit=limit, before=before, after=after, around=around, oldest_first=oldest_first
        )


class Connectable(Protocol):
    """An ABC that details the common operations on a channel that can
    connect to a voice server.

    The following implement this ABC:

    - :class:`~nextcord.VoiceChannel`
    - :class:`~nextcord.StageChannel`

    Note
    ----
    This ABC is not decorated with :func:`typing.runtime_checkable`, so will fail :func:`isinstance`/:func:`issubclass`
    checks.
    """

    __slots__ = ()
    _state: ConnectionState

    def _get_voice_client_key(self) -> Tuple[int, str]:
        raise NotImplementedError

    def _get_voice_state_pair(self) -> Tuple[int, int]:
        raise NotImplementedError

    async def connect(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, Connectable], T] = VoiceClient,
    ) -> T:
        """|coro|

        Connects to voice and creates a :class:`VoiceClient` to establish
        your connection to the voice server.

        This requires :attr:`Intents.voice_states`.

        Parameters
        ----------
        timeout: :class:`float`
            The timeout in seconds to wait for the voice endpoint.
        reconnect: :class:`bool`
            Whether the bot should automatically attempt
            a reconnect if a part of the handshake fails
            or the gateway goes down.
        cls: Type[:class:`VoiceProtocol`]
            A type that subclasses :class:`~nextcord.VoiceProtocol` to connect with.
            Defaults to :class:`~nextcord.VoiceClient`.

        Raises
        ------
        asyncio.TimeoutError
            Could not connect to the voice channel in time.
        ~nextcord.ClientException
            You are already connected to a voice channel.
        ~nextcord.opus.OpusNotLoaded
            The opus library has not been loaded.

        Returns
        -------
        :class:`~nextcord.VoiceProtocol`
            A voice client that is fully connected to the voice server.
        """

        key_id, _ = self._get_voice_client_key()
        state = self._state

        if state._get_voice_client(key_id):
            raise ClientException("Already connected to a voice channel.")

        client = state._get_client()
        voice = cls(client, self)

        if not isinstance(voice, VoiceProtocol):
            raise TypeError("Type must meet VoiceProtocol abstract base class.")

        state._add_voice_client(key_id, voice)

        try:
            await voice.connect(timeout=timeout, reconnect=reconnect)
        except asyncio.TimeoutError:
            # we don't care if disconnect failed because connection failed
            with contextlib.suppress(Exception):
                await voice.disconnect(force=True)
            raise  # re-raise

        return voice
