# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .enums import VoiceRegion
from .guild import Guild
from .utils import MISSING, obj_to_base64_data, parse_time

__all__ = ("Template",)

if TYPE_CHECKING:
    import datetime

    from .asset import Asset
    from .file import File
    from .message import Attachment
    from .state import ConnectionState
    from .types.template import Template as TemplatePayload
    from .user import User


class _FriendlyHttpAttributeErrorHelper:
    __slots__ = ()

    def __getattr__(self, attr):
        raise AttributeError("PartialTemplateState does not support http methods.")


class _PartialTemplateState:
    def __init__(self, *, state) -> None:
        self.__state = state
        self.http = _FriendlyHttpAttributeErrorHelper()

    @property
    def shard_count(self):
        return self.__state.shard_count

    @property
    def user(self):
        return self.__state.user

    @property
    def self_id(self):
        return self.__state.user.id

    @property
    def member_cache_flags(self):
        return self.__state.member_cache_flags

    def store_emoji(self, guild, packet):
        return None

    def _get_voice_client(self, id):
        return None

    def _get_message(self, id):
        return None

    def _get_guild(self, id):
        return self.__state._get_guild(id)

    async def query_members(self, **kwargs: Any):
        return []

    def __getattr__(self, attr):
        raise AttributeError(f"PartialTemplateState does not support {attr!r}.")


class Template:
    """Represents a Discord template.

    .. versionadded:: 1.4

    Attributes
    ----------
    code: :class:`str`
        The template code.
    uses: :class:`int`
        How many times the template has been used.
    name: :class:`str`
        The name of the template.
    description: :class:`str`
        The description of the template.
    creator: :class:`User`
        The creator of the template.
    created_at: :class:`datetime.datetime`
        An aware datetime in UTC representing when the template was created.
    updated_at: :class:`datetime.datetime`
        An aware datetime in UTC representing when the template was last updated.
        This is referred to as "last synced" in the official Discord client.
    source_guild: :class:`Guild`
        The source guild.
    is_dirty: Optional[:class:`bool`]
        Whether the template has unsynced changes.

        .. versionadded:: 2.0
    """

    __slots__ = (
        "code",
        "uses",
        "name",
        "description",
        "creator",
        "created_at",
        "updated_at",
        "source_guild",
        "is_dirty",
        "_state",
    )

    def __init__(self, *, state: ConnectionState, data: TemplatePayload) -> None:
        self._state = state
        self._store(data)

    def _store(self, data: TemplatePayload) -> None:
        self.code: str = data["code"]
        self.uses: int = data["usage_count"]
        self.name: str = data["name"]
        self.description: Optional[str] = data["description"]
        self.creator: Optional[User] = self._state.create_user(data.get("creator"))

        self.created_at: Optional[datetime.datetime] = parse_time(data.get("created_at"))
        self.updated_at: Optional[datetime.datetime] = parse_time(data.get("updated_at"))

        guild_id = int(data["source_guild_id"])
        guild: Optional[Guild] = self._state._get_guild(guild_id)

        self.source_guild: Guild
        if guild is None:
            source_serialised = data["serialized_source_guild"]
            source_serialised["id"] = guild_id
            state = _PartialTemplateState(state=self._state)
            # Guild expects a ConnectionState, we're passing a _PartialTemplateState
            self.source_guild = Guild(data=source_serialised, state=state)  # type: ignore
        else:
            self.source_guild = guild

        self.is_dirty: Optional[bool] = data.get("is_dirty", None)

    def __repr__(self) -> str:
        return (
            f"<Template code={self.code!r} uses={self.uses} name={self.name!r}"
            f" creator={self.creator!r} source_guild={self.source_guild!r} is_dirty={self.is_dirty}>"
        )

    async def create_guild(
        self,
        name: str,
        region: Optional[VoiceRegion] = None,
        icon: Optional[Union[bytes, Asset, Attachment, File]] = None,
    ) -> Guild:
        """|coro|

        Creates a :class:`.Guild` using the template.

        Bot accounts in more than 10 guilds are not allowed to create guilds.

        .. versionchanged:: 2.1
            The ``icon`` parameter now accepts :class:`File`, :class:`Attachment`, and :class:`Asset`.

        Parameters
        ----------
        name: :class:`str`
            The name of the guild.
        region: :class:`.VoiceRegion`
            The region for the voice communication server.
            Defaults to :attr:`.VoiceRegion.us_west`.
        icon: Optional[Union[:class:`bytes`, :class:`Asset`, :class:`Attachment`, :class:`File`]]
            The :term:`py:bytes-like object`, :class:`File`, :class:`Attachment`, or :class:`Asset`
            representing the icon. See :meth:`.ClientUser.edit` for more details on what is expected.

        Raises
        ------
        HTTPException
            Guild creation failed.
        InvalidArgument
            Invalid icon image format given. Must be PNG or JPG.

        Returns
        -------
        :class:`.Guild`
            The guild created. This is not the same guild that is
            added to cache.
        """
        icon_base64 = await obj_to_base64_data(icon)

        region = region or VoiceRegion.us_west
        region_value = region.value

        data = await self._state.http.create_from_template(
            self.code, name, region_value, icon_base64
        )
        return Guild(data=data, state=self._state)

    async def sync(self) -> Template:
        """|coro|

        Sync the template to the guild's current state.

        You must have the :attr:`~Permissions.manage_guild` permission in the
        source guild to do this.

        .. versionadded:: 1.7

        .. versionchanged:: 2.0
            The template is no longer edited in-place, instead it is returned.

        Raises
        ------
        HTTPException
            Editing the template failed.
        Forbidden
            You don't have permissions to edit the template.
        NotFound
            This template does not exist.

        Returns
        -------
        :class:`Template`
            The newly edited template.
        """

        data = await self._state.http.sync_template(self.source_guild.id, self.code)
        return Template(state=self._state, data=data)

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: Optional[str] = MISSING,
    ) -> Template:
        """|coro|

        Edit the template metadata.

        You must have the :attr:`~Permissions.manage_guild` permission in the
        source guild to do this.

        .. versionadded:: 1.7

        .. versionchanged:: 2.0
            The template is no longer edited in-place, instead it is returned.

        Parameters
        ----------
        name: :class:`str`
            The template's new name.
        description: Optional[:class:`str`]
            The template's new description.

        Raises
        ------
        HTTPException
            Editing the template failed.
        Forbidden
            You don't have permissions to edit the template.
        NotFound
            This template does not exist.

        Returns
        -------
        :class:`Template`
            The newly edited template.
        """
        payload = {}

        if name is not MISSING:
            payload["name"] = name
        if description is not MISSING:
            payload["description"] = description

        data = await self._state.http.edit_template(self.source_guild.id, self.code, payload)
        return Template(state=self._state, data=data)

    async def delete(self) -> None:
        """|coro|

        Delete the template.

        You must have the :attr:`~Permissions.manage_guild` permission in the
        source guild to do this.

        .. versionadded:: 1.7

        Raises
        ------
        HTTPException
            Editing the template failed.
        Forbidden
            You don't have permissions to edit the template.
        NotFound
            This template does not exist.
        """
        await self._state.http.delete_template(self.source_guild.id, self.code)

    @property
    def url(self) -> str:
        """:class:`str`: The template url.

        .. versionadded:: 2.0
        """
        return f"https://discord.new/{self.code}"
