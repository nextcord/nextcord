# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

__all__ = ("AllowedMentions",)

if TYPE_CHECKING:
    from typing_extensions import Self

    from .abc import Snowflake
    from .types.message import AllowedMentions as AllowedMentionsPayload


class AllowedMentions:
    """A class that represents what mentions are allowed in a message.

    This class can be set during :class:`Client` initialisation to apply
    to every message sent. It can also be applied on a per message basis
    via :meth:`abc.Messageable.send` for more fine-grained control.

    Attributes
    ----------
    everyone: :class:`bool`
        Whether to allow everyone and here mentions. Defaults to ``True``.
    users: Union[:class:`bool`, List[:class:`abc.Snowflake`]]
        Controls the users being mentioned. If ``True`` (the default) then
        users are mentioned based on the message content. If ``False`` then
        users are not mentioned at all. If a list of :class:`abc.Snowflake`
        is given then only the users provided will be mentioned, provided those
        users are in the message content.
    roles: Union[:class:`bool`, List[:class:`abc.Snowflake`]]
        Controls the roles being mentioned. If ``True`` (the default) then
        roles are mentioned based on the message content. If ``False`` then
        roles are not mentioned at all. If a list of :class:`abc.Snowflake`
        is given then only the roles provided will be mentioned, provided those
        roles are in the message content.
    replied_user: :class:`bool`
        Whether to mention the author of the message being replied to. Defaults
        to ``True``.

        .. versionadded:: 1.6
    """

    __slots__ = ("everyone", "users", "roles", "replied_user")

    def __init__(
        self,
        *,
        everyone: Optional[bool] = None,
        users: Optional[Union[bool, List[Snowflake]]] = None,
        roles: Optional[Union[bool, List[Snowflake]]] = None,
        replied_user: Optional[bool] = None,
    ) -> None:
        self.everyone = everyone
        self.users = users
        self.roles = roles
        self.replied_user = replied_user

    @classmethod
    def all(cls) -> Self:
        """A factory method that returns a :class:`AllowedMentions` with all fields explicitly set to ``True``

        .. versionadded:: 1.5
        """
        return cls(everyone=True, users=True, roles=True, replied_user=True)

    @classmethod
    def none(cls) -> Self:
        """A factory method that returns a :class:`AllowedMentions` with all fields set to ``False``

        .. versionadded:: 1.5
        """
        return cls(everyone=False, users=False, roles=False, replied_user=False)

    def to_dict(self) -> AllowedMentionsPayload:
        parse = []
        data = {}

        if self.everyone or self.everyone is None:
            parse.append("everyone")

        if self.users is True or self.users is None:
            parse.append("users")
        elif self.users:
            data["users"] = [x.id for x in self.users]

        if self.roles is True or self.users is None:
            parse.append("roles")
        elif self.roles:
            data["roles"] = [x.id for x in self.roles]

        if self.replied_user or self.replied_user is None:
            data["replied_user"] = True

        data["parse"] = parse
        return data  # type: ignore

    def merge(self, other: AllowedMentions) -> AllowedMentions:
        # Creates a new AllowedMentions by merging from another one.
        # Merge is done by using the 'self' values unless explicitly
        # overridden by the 'other' values.
        everyone = self.everyone if other.everyone is None else other.everyone
        users = self.users if other.users is None else other.users
        roles = self.roles if other.roles is None else other.roles
        replied_user = self.replied_user if other.replied_user is None else other.replied_user
        return AllowedMentions(
            everyone=everyone, roles=roles, users=users, replied_user=replied_user
        )

    def __repr__(self) -> str:
        everyone = self.everyone if self.everyone is not None else True
        users = self.users if self.users is not None else True
        roles = self.roles if self.roles is not None else True
        replied_user = self.replied_user if self.replied_user is not None else True
        return (
            f"{self.__class__.__name__}(everyone={everyone}, "
            f"users={users}, roles={roles}, replied_user={replied_user})"
        )
