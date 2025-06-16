# SPDX-License-Identifier: MIT

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from . import abc
from .asset import Asset
from .colour import Colour
from .entitlement import Entitlement
from .enums import DefaultAvatar, EntitlementOwnerType
from .flags import PublicUserFlags
from .object import Object
from .utils import MISSING, obj_to_base64_data, snowflake_time, time_snowflake

if TYPE_CHECKING:
    from typing_extensions import Self

    from .abc import SnowflakeTime
    from .channel import DMChannel
    from .file import File
    from .guild import Guild
    from .message import Attachment, Message
    from .state import ConnectionState
    from .types.channel import DMChannel as DMChannelPayload
    from .types.user import (
        AvatarDecorationData as AvatarDecorationDataPayload,
        PartialUser as PartialUserPayload,
        User as UserPayload,
    )


__all__ = (
    "User",
    "ClientUser",
    "AvatarDecoration",
)


class AvatarDecoration:
    """Represents an avatar decoration. This is a cosmetic item that can be applied to a user's avatar.

    You can get this object via :meth:`User.avatar_decoration`.

    .. versionadded:: 3.2

    Attributes
    ----------
    user: :class:`.BaseUser`
        The user this avatar decoration belongs to.
    sku_id: :class:`str`
        The sku id of the avatar decoration.
    asset: :class:`Asset`
        The asset of the avatar decoration.
    """

    __slots__ = (
        "user",
        "sku_id",
        "_asset",
    )

    def __init__(self, *, user: BaseUser, data: AvatarDecorationDataPayload) -> None:
        self._update(user, data)

    def __repr__(self) -> str:
        return f"<AvatarDecoration sku_id={self.sku_id!r} asset={self.asset!r}>"

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, AvatarDecoration)
            and other.sku_id == self.sku_id
            and other.asset == self.asset
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def _update(self, user: BaseUser, data: AvatarDecorationDataPayload, /) -> None:
        self.user: BaseUser = user
        self.sku_id: str = data["sku_id"]
        self._asset: str = data["asset"]

    @property
    def asset(self) -> Asset:
        return Asset._from_avatar_decoration(self.user._state, self._asset)


class _UserTag:
    __slots__ = ()
    id: int


class BaseUser(_UserTag):
    __slots__ = (
        "name",
        "id",
        "discriminator",
        "_avatar",
        "_banner",
        "_accent_colour",
        "bot",
        "system",
        "_public_flags",
        "_state",
        "global_name",
        "_avatar_decoration",
    )

    if TYPE_CHECKING:
        name: str
        id: int
        discriminator: str
        bot: bool
        system: bool
        global_name: Optional[str]
        _state: ConnectionState
        _avatar: Optional[str]
        _banner: Optional[str]
        _accent_colour: Optional[str]
        _public_flags: int
        _avatar_decoration: Optional[AvatarDecorationDataPayload]

    def __init__(
        self, *, state: ConnectionState, data: Union[PartialUserPayload, UserPayload]
    ) -> None:
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return (
            f"<BaseUser id={self.id} name={self.name!r} global_name={self.global_name!r}"
            + (f" discriminator={self.discriminator!r}" if self.discriminator != "0" else "")
            + f" bot={self.bot} system={self.system}>"
        )

    def __str__(self) -> str:
        return f"{self.name}#{self.discriminator}" if self.discriminator != "0" else self.name

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, _UserTag) and other.id == self.id

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return self.id >> 22

    def _update(self, data: Union[PartialUserPayload, UserPayload]) -> None:
        self.name = data["username"]
        self.id = int(data["id"])
        self.discriminator = data["discriminator"]
        self._avatar = data["avatar"]
        self._banner = data.get("banner", None)
        self._accent_colour = data.get("accent_color", None)
        self._avatar_decoration = data.get("avatar_decoration_data", None)
        self._public_flags = data.get("public_flags", 0)
        self.bot = data.get("bot", False)
        self.system = data.get("system", False)
        self.global_name = data.get("global_name", None)

    @classmethod
    def _copy(cls, user: Self) -> Self:
        self = cls.__new__(cls)  # bypass __init__

        self.name = user.name
        self.id = user.id
        self.discriminator = user.discriminator
        self._avatar = user._avatar
        self._banner = user._banner
        self._accent_colour = user._accent_colour
        self._avatar_decoration = user._avatar_decoration
        self.bot = user.bot
        self._state = user._state
        self._public_flags = user._public_flags

        return self

    def _to_minimal_user_json(self) -> Dict[str, Any]:
        return {
            "username": self.name,
            "id": self.id,
            "avatar": self._avatar,
            "global_name": self.global_name,
            "discriminator": self.discriminator,  # TODO: possibly remove this?
            "bot": self.bot,
        }

    @property
    def public_flags(self) -> PublicUserFlags:
        """:class:`PublicUserFlags`: The publicly available flags the user has."""
        return PublicUserFlags._from_value(self._public_flags)

    @property
    def avatar(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the avatar the user has.

        If the user does not have a traditional avatar, ``None`` is returned.
        If you want the avatar that a user has displayed, consider :attr:`display_avatar`.
        """
        if self._avatar is not None:
            return Asset._from_avatar(self._state, self.id, self._avatar)
        return None

    @property
    def default_avatar(self) -> Asset:
        """:class:`Asset`: Returns the default avatar for a given user.

        This is calculated by the user's discriminator.

        ..versionchanged:: 2.6
            Added handling for the new username system for users without a discriminator.
        """
        if self.discriminator == "0":
            avatar_index = (self.id >> 22) % len(DefaultAvatar)
        else:
            avatar_index = int(self.discriminator) % 5
        return Asset._from_default_avatar(self._state, avatar_index)

    @property
    def display_avatar(self) -> Asset:
        """:class:`Asset`: Returns the user's display avatar.

        For regular users this is just their default avatar or uploaded avatar.

        .. versionadded:: 2.0
        """
        return self.avatar or self.default_avatar

    @property
    def avatar_decoration(self) -> Optional[AvatarDecoration]:
        """Optional[:class:`AvatarDecoration`]: Returns the user's avatar decoration, if applicable.

        You can get the asset of the avatar decoration via :attr:`AvatarDecoration.asset`.

        .. versionadded:: 3.2
        """
        if self._avatar_decoration is None:
            return None

        return AvatarDecoration(user=self, data=self._avatar_decoration)

    @property
    def banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the user's banner asset, if available.

        .. versionadded:: 2.0


        .. note::
            This information is only available via :meth:`Client.fetch_user`.
        """
        if self._banner is None:
            return None
        return Asset._from_user_banner(self._state, self.id, self._banner)

    @property
    def accent_colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: Returns the user's accent colour, if applicable.

        There is an alias for this named :attr:`accent_color`.

        .. versionadded:: 2.0

        .. note::

            This information is only available via :meth:`Client.fetch_user`.
        """
        if self._accent_colour is None:
            return None
        return Colour(int(self._accent_colour))

    @property
    def accent_color(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: Returns the user's accent color, if applicable.

        There is an alias for this named :attr:`accent_colour`.

        .. versionadded:: 2.0

        .. note::

            This information is only available via :meth:`Client.fetch_user`.
        """
        return self.accent_colour

    @property
    def colour(self) -> Colour:
        """:class:`Colour`: A property that returns a colour denoting the rendered colour
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :attr:`color`.
        """
        return Colour.default()

    @property
    def color(self) -> Colour:
        """:class:`Colour`: A property that returns a color denoting the rendered color
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :attr:`colour`.
        """
        return self.colour

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user."""
        return f"<@{self.id}>"

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the user's creation time in UTC.

        This is when the user's Discord account was created.
        """
        return snowflake_time(self.id)

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name.

        This will return the name using the following hierachy:

        1. Global Name (also known as 'Display Name' in the Discord UI)
        2. Unique username
        """
        return self.global_name or self.name

    def mentioned_in(self, message: Message) -> bool:
        """Checks if the user is mentioned in the specified message.

        Parameters
        ----------
        message: :class:`Message`
            The message to check if you're mentioned in.

        Returns
        -------
        :class:`bool`
            Indicates if the user is mentioned in the message.
        """

        if message.mention_everyone:
            return True

        return any(user.id == self.id for user in message.mentions)


class ClientUser(BaseUser):
    """Represents your Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator.

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    global_name: Optional[:class:`str`]
        The user's display name, if any.

        .. versionadded: 2.6
    discriminator: :class:`str`
        The user's discriminator.

        .. warning::
            This field is deprecated, and will only return if the user has not yet migrated to the
            new `username <https://dis.gd/usernames>`_ update.
        .. deprecated:: 2.6
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).

        .. versionadded:: 1.3

    verified: :class:`bool`
        Specifies if the user's email is verified.
    locale: Optional[:class:`str`]
        The IETF language tag used to identify the language the user is using.
    mfa_enabled: :class:`bool`
        Specifies if the user has MFA turned on and working.
    """

    __slots__ = ("locale", "_flags", "verified", "mfa_enabled", "__weakref__")

    if TYPE_CHECKING:
        verified: bool
        locale: Optional[str]
        mfa_enabled: bool
        _flags: int

    def __init__(self, *, state: ConnectionState, data: UserPayload) -> None:
        super().__init__(state=state, data=data)

    def __repr__(self) -> str:
        return (
            f"<ClientUser id={self.id} name={self.name!r} global_name={self.global_name!r}"
            + (f" discriminator={self.discriminator!r}" if self.discriminator != "0" else "")
            + f" bot={self.bot} verified={self.verified} mfa_enabled={self.mfa_enabled}>"
        )

    def _update(self, data: UserPayload) -> None:
        super()._update(data)
        # There's actually an Optional[str] phone field as well but I won't use it
        self.verified = data.get("verified", False)
        self.locale = data.get("locale")
        self._flags = data.get("flags", 0)
        self.mfa_enabled = data.get("mfa_enabled", False)

    async def edit(
        self,
        *,
        username: str = MISSING,
        avatar: Optional[Union[bytes, Asset, Attachment, File]] = MISSING,
        banner: Optional[Union[bytes, Asset, Attachment, File]] = MISSING,
    ) -> ClientUser:
        """|coro|

        Edits the current profile of the client.

        .. note::

            To upload an avatar, a :term:`py:bytes-like object` must be passed in that
            represents the image being uploaded. If this is done through a file
            then the file must be opened via ``open('some_filename', 'rb')`` and
            the :term:`py:bytes-like object` is given through the use of ``fp.read()``.

            The only image formats supported for uploading is JPEG and PNG.

        .. versionchanged:: 2.0
            The edit is no longer in-place, instead the newly edited client user is returned.

        .. versionchanged:: 2.1
            The ``avatar`` parameter now accepts :class:`File`, :class:`Attachment`, and :class:`Asset`.

        .. versionadded:: 3.0
            The ``banner`` field has been added.

        Parameters
        ----------
        username: :class:`str`
            The new username you wish to change to.
        avatar: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the image to upload. Could be ``None`` to denote no avatar.
        banner: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            A :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the image to upload. Could be ``None`` to denote no banner.

        Raises
        ------
        HTTPException
            Editing your profile failed.
        InvalidArgument
            Wrong image format passed for ``avatar`` and/or ``banner``.

        Returns
        -------
        :class:`ClientUser`
            The newly edited client user.
        """
        payload: Dict[str, Any] = {}
        if username is not MISSING:
            payload["username"] = username
        if avatar is not MISSING:
            payload["avatar"] = await obj_to_base64_data(avatar)
        if banner is not MISSING:
            payload["banner"] = await obj_to_base64_data(banner)

        data: UserPayload = await self._state.http.edit_profile(payload)
        return ClientUser(state=self._state, data=data)


class User(BaseUser, abc.Messageable):
    """Represents a Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator.

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    global_name: Optional[:class:`str`]
        The user's default name, if any.

        ..versionadded: 2.6
    discriminator: :class:`str`
        The user's discriminator.

        .. warning::
          This field is deprecated, and will only return if the user has not yet migrated to the
          new `username <https://dis.gd/usernames>`_ update.
        .. deprecated:: 2.6
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).
    """

    __slots__ = ("_stored",)

    def __init__(
        self, *, state: ConnectionState, data: Union[PartialUserPayload, UserPayload]
    ) -> None:
        super().__init__(state=state, data=data)
        self._stored: bool = False

    def __repr__(self) -> str:
        return (
            f"<User id={self.id} name={self.name!r} global_name={self.global_name!r}"
            + (f" discriminator={self.discriminator!r}" if self.discriminator != "0" else "")
            + f" bot={self.bot}>"
        )

    def __del__(self) -> None:
        try:
            if self._stored:
                self._state.deref_user(self.id)
        except Exception:
            pass

    @classmethod
    def _copy(cls, user: Self) -> Self:
        self = super()._copy(user)
        self._stored = False
        return self

    async def _get_channel(self) -> DMChannel:
        return await self.create_dm()

    @property
    def dm_channel(self) -> Optional[DMChannel]:
        """Optional[:class:`DMChannel`]: Returns the channel associated with this user if it exists.

        If this returns ``None``, you can create a DM channel by calling the
        :meth:`create_dm` coroutine function.
        """
        return self._state._get_private_channel_by_user(self.id)

    @property
    def mutual_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: The guilds that the user shares with the client.

        .. note::

            This will only return mutual guilds within the client's internal cache.

        .. versionadded:: 1.7
        """
        return [guild for guild in self._state._guilds.values() if guild.get_member(self.id)]

    async def create_dm(self) -> DMChannel:
        """|coro|

        Creates a :class:`DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.

        Returns
        -------
        :class:`.DMChannel`
            The channel that was created.
        """
        found = self.dm_channel
        if found is not None:
            return found

        state = self._state
        data: DMChannelPayload = await state.http.start_private_message(self.id)
        return state.add_dm_channel(data)

    async def create_test_entitlement(self, sku_id: int):
        """|coro|

        Creates a test entitlement for this user.

        .. versionadded:: 3.2

        Parameters
        ----------
        sku_id: :class:`int`
            The ID of the SKU to create a test entitlement for.
        """
        if not self._state.application_id:
            raise TypeError("Couldn't get the clients application_id.")
        await self._state.http.create_test_entitlement(
            application_id=self._state.application_id,
            sku_id=sku_id,
            owner_id=self.id,
            owner_type=EntitlementOwnerType.user_subscription.value,
        )

    async def entitlements(
        self,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        limit: Optional[int] = None,
        exclude_ended: bool = False,
    ) -> List[Entitlement]:
        """|coro|

        Fetches the entitlements for this user.

        .. versionadded:: 3.2

        Parameters
        ----------
        before: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve entitlements before this date or entitlement.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
            Defaults to ``None``.
        after: Optional[Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve entitlements after this date or entitlement.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
            Defaults to ``None``.
        limit: Optional[:class:`int`]
            The number of entitlements to retrieve. If ``None`` retrieve all entitlements.
            Defaults to ``None``.
        exclude_ended: :class:`bool`
            Whether to exclude ended entitlements.
            Defaults to ``False``.

        Returns
        -------
        List[:class:`Entitlement`]
            The entitlements for this user.
        """
        if not self._state.application_id:
            raise TypeError("Couldn't get the clients application_id.")

        if isinstance(before, datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime):
            after = Object(id=time_snowflake(after, high=True))

        data = await self._state.http.list_entitlements(
            application_id=self._state.application_id,
            user_id=self.id,
            before=before.id if before else None,
            after=after.id if after else None,
            limit=limit,
            exclude_ended=exclude_ended,
        )
        return [Entitlement(payload) for payload in data]
