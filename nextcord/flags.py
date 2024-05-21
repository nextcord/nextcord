# SPDX-License-Identifier: MIT

from __future__ import annotations

from functools import reduce
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    overload,
)

from .enums import UserFlags

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = (
    "SystemChannelFlags",
    "MessageFlags",
    "PublicUserFlags",
    "MemberFlags",
    "Intents",
    "MemberCacheFlags",
    "ApplicationFlags",
    "ChannelFlags",
    "AttachmentFlags",
    "RoleFlags",
)

BF = TypeVar("BF", bound="BaseFlags")


class flag_value:
    def __init__(self, func: Callable[[Any], int]) -> None:
        self.flag = func(None)
        self.__doc__ = func.__doc__

    @overload
    def __get__(self, instance: None, owner: Type[BF]) -> Self:
        ...

    @overload
    def __get__(self, instance: BF, owner: Type[BF]) -> bool:
        ...

    def __get__(self, instance: Optional[BF], owner: Type[BF]) -> Any:
        if instance is None:
            return self
        return instance._has_flag(self.flag)

    def __set__(self, instance: BaseFlags, value: bool) -> None:
        instance._set_flag(self.flag, value)

    def __repr__(self) -> str:
        return f"<flag_value flag={self.flag!r}>"


class alias_flag_value(flag_value):
    pass


def fill_with_flags(*, inverted: bool = False):
    def decorator(cls: Type[BF]):
        cls.VALID_FLAGS = {
            name: value.flag
            for name, value in cls.__dict__.items()
            if isinstance(value, flag_value)
        }

        if inverted:
            max_bits = max(cls.VALID_FLAGS.values()).bit_length()
            cls.DEFAULT_VALUE = -1 + (2**max_bits)
        else:
            cls.DEFAULT_VALUE = 0

        return cls

    return decorator


# n.b. flags must inherit from this and use the decorator above
class BaseFlags:
    VALID_FLAGS: ClassVar[Dict[str, int]]
    DEFAULT_VALUE: ClassVar[int]

    value: int

    __slots__ = ("value",)

    def __init__(self, **kwargs: bool) -> None:
        self.value = self.DEFAULT_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f"{key!r} is not a valid flag name.")
            setattr(self, key, value)

    @classmethod
    def _from_value(cls, value):
        self = cls.__new__(cls)
        self.value = value
        return self

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} value={self.value}>"

    def __iter__(self) -> Iterator[Tuple[str, bool]]:
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, alias_flag_value):
                continue

            if isinstance(value, flag_value):
                yield (name, self._has_flag(value.flag))

    def _has_flag(self, o: int) -> bool:
        return (self.value & o) == o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value |= o
        elif toggle is False:
            self.value &= ~o
        else:
            raise TypeError(f"Value to set for {self.__class__.__name__} must be a bool.")


@fill_with_flags(inverted=True)
class SystemChannelFlags(BaseFlags):
    r"""Wraps up a Discord system channel flag value.

    Similar to :class:`Permissions`\, the properties provided are two way.
    You can set and retrieve individual bits using the properties as if they
    were regular bools. This allows you to edit the system flags easily.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

    Attributes
    ----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    __slots__ = ()

    # For some reason the flags for system channels are "inverted"
    # ergo, if they're set then it means "suppress" (off in the GUI toggle)
    # Since this is counter-intuitive from an API perspective and annoying
    # these will be inverted automatically

    def _has_flag(self, o: int) -> bool:
        return (self.value & o) != o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value &= ~o
        elif toggle is False:
            self.value |= o
        else:
            raise TypeError("Value to set for SystemChannelFlags must be a bool.")

    @flag_value
    def join_notifications(self) -> int:
        """:class:`bool`: Returns ``True`` if the system channel is used for member join notifications."""
        return 1

    @flag_value
    def premium_subscriptions(self) -> int:
        """:class:`bool`: Returns ``True`` if the system channel is used for "Nitro boosting" notifications."""
        return 2

    @flag_value
    def guild_reminder_notifications(self) -> int:
        """:class:`bool`: Returns ``True`` if the system channel is used for server setup helpful tips notifications.

        .. versionadded:: 2.0
        """
        return 4

    @flag_value
    def join_notification_replies(self) -> int:
        """:class:`bool`: Returns ``True`` if the button to reply with a sticker to member join notifications is shown.

        .. versionadded:: 2.0
        """
        return 8


@fill_with_flags()
class ChannelFlags(BaseFlags):
    """Wraps up a Discord channel flag value.

    Similar to :class:`Permissions`, the properties provided are two way.
    You can set and retrieve individual bits using the properties as if they
    were regular bools. This allows you to edit the channel flags easily.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    .. versionadded:: 2.1

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.

    Attributes
    ----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    __slots__ = ()

    @flag_value
    def pinned(self):
        """:class:`bool`: Returns ``True`` if the thread is pinned in its parent forum."""
        return 1 << 1

    @flag_value
    def require_tag(self):
        """:class:`bool`: Returns ``True`` if the forum channel requires tags for posts."""
        return 1 << 4


@fill_with_flags()
class MessageFlags(BaseFlags):
    r"""Wraps up a Discord Message flag value.

    See :class:`SystemChannelFlags`.

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

    .. versionadded:: 1.3

    Attributes
    ----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    __slots__ = ()

    @flag_value
    def crossposted(self) -> int:
        """:class:`bool`: Returns ``True`` if the message is the original crossposted message."""
        return 1 << 0

    @flag_value
    def is_crossposted(self) -> int:
        """:class:`bool`: Returns ``True`` if the message was crossposted from another channel."""
        return 1 << 1

    @flag_value
    def suppress_embeds(self) -> int:
        """:class:`bool`: Returns ``True`` if the message's embeds have been suppressed."""
        return 1 << 2

    @flag_value
    def source_message_deleted(self) -> int:
        """:class:`bool`: Returns ``True`` if the source message for this crosspost has been deleted."""
        return 1 << 3

    @flag_value
    def urgent(self) -> int:
        """:class:`bool`: Returns ``True`` if the source message is an urgent message.

        An urgent message is one sent by Discord Trust and Safety.
        """
        return 1 << 4

    @flag_value
    def has_thread(self) -> int:
        """:class:`bool`: Returns ``True`` if the source message is associated with a thread.

        .. versionadded:: 2.0
        """
        return 1 << 5

    @flag_value
    def ephemeral(self) -> int:
        """:class:`bool`: Returns ``True`` if the source message is ephemeral.

        .. versionadded:: 2.0
        """
        return 1 << 6

    @flag_value
    def loading(self) -> int:
        """:class:`bool`: Returns ``True`` if the source message is loading.

        This is represented in the UI as "bot is thinking...".

        .. versionadded:: 2.6
        """
        return 1 << 7

    @flag_value
    def failed_to_mention_roles(self) -> int:
        """:class:`bool`: Returns ``True`` if the message failed to mention some roles in a thread.

        This means that those members were not added.

        .. versionadded:: 2.6
        """
        return 1 << 8

    @flag_value
    def suppress_notifications(self) -> int:
        """:class:`bool`: Returns ``True`` if the message does not trigger notifications.

        These are sent via `@silent` message prefixes in the UI.

        .. versionadded:: 2.6
        """
        return 1 << 12


@fill_with_flags()
class PublicUserFlags(BaseFlags):
    r"""Wraps up the Discord User Public flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two PublicUserFlags are equal.
        .. describe:: x != y

            Checks if two PublicUserFlags are not equal.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

    .. versionadded:: 1.4

    Attributes
    ----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    __slots__ = ()

    @flag_value
    def staff(self):
        """:class:`bool`: Returns ``True`` if the user is a Discord Employee."""
        return UserFlags.staff.value

    @flag_value
    def partner(self):
        """:class:`bool`: Returns ``True`` if the user is a Discord Partner."""
        return UserFlags.partner.value

    @flag_value
    def hypesquad(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Events member."""
        return UserFlags.hypesquad.value

    @flag_value
    def bug_hunter(self):
        """:class:`bool`: Returns ``True`` if the user is a Bug Hunter"""
        return UserFlags.bug_hunter.value

    @flag_value
    def hypesquad_bravery(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Bravery member."""
        return UserFlags.hypesquad_bravery.value

    @flag_value
    def hypesquad_brilliance(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Brilliance member."""
        return UserFlags.hypesquad_brilliance.value

    @flag_value
    def hypesquad_balance(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Balance member."""
        return UserFlags.hypesquad_balance.value

    @flag_value
    def early_supporter(self):
        """:class:`bool`: Returns ``True`` if the user is an Early Supporter."""
        return UserFlags.early_supporter.value

    @flag_value
    def team_user(self):
        """:class:`bool`: Returns ``True`` if the user is a Team User."""
        return UserFlags.team_user.value

    @flag_value
    def system(self):
        """:class:`bool`: Returns ``True`` if the user is a system user (i.e. represents Discord officially)."""
        return UserFlags.system.value

    @flag_value
    def bug_hunter_level_2(self):
        """:class:`bool`: Returns ``True`` if the user is a Bug Hunter Level 2"""
        return UserFlags.bug_hunter_level_2.value

    @flag_value
    def verified_bot(self):
        """:class:`bool`: Returns ``True`` if the user is a Verified Bot."""
        return UserFlags.verified_bot.value

    @flag_value
    def verified_bot_developer(self):
        """:class:`bool`: Returns ``True`` if the user is an Early Verified Bot Developer."""
        return UserFlags.verified_bot_developer.value

    @alias_flag_value
    def early_verified_bot_developer(self):
        """:class:`bool`: An alias for :attr:`verified_bot_developer`.

        .. versionadded:: 1.5
        """
        return UserFlags.verified_bot_developer.value

    @flag_value
    def discord_certified_moderator(self):
        """:class:`bool`: Returns ``True`` if the user is a Discord Moderator Programs Alumni.

        Formally known as Discord Certified Moderator.

        .. versionadded:: 2.0
        """
        return UserFlags.discord_certified_moderator.value

    @flag_value
    def known_spammer(self):
        """:class:`bool`: Returns ``True`` if the user is a Known Spammer.

        .. versionadded:: 2.0
        """
        return UserFlags.known_spammer.value

    @flag_value
    def active_developer(self):
        """:class:`bool`: Returns ``True`` if the user is an Active Developer.

        .. versionadded:: 2.4
        """
        return UserFlags.active_developer.value

    def all(self) -> List[UserFlags]:
        """List[:class:`UserFlags`]: Returns all public flags the user has."""
        return [public_flag for public_flag in UserFlags if self._has_flag(public_flag.value)]


@fill_with_flags()
class MemberFlags(BaseFlags):
    r"""Wraps up the Discord Guild Member flags

    .. versionadded:: 2.6

    .. container:: operations

        .. describe:: x == y

            Checks if two MemberFlags are equal.

        .. describe:: x != y

            Checks if two MemberFlags are not equal.
        .. describe:: hash(x)

            Returns the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

    Attributes
    -----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def did_rejoin(self):
        """:class:`bool`: Returns ``True`` if the member left and rejoined the :attr:`~nextcord.Guild`."""
        return 1 << 0

    @flag_value
    def completed_onboarding(self):
        """:class:`bool`: Returns ``True`` if the member has completed onboarding."""
        return 1 << 1

    @flag_value
    def bypasses_verification(self):
        """:class:`bool`: Returns ``True`` if the member can bypass the guild verification requirements."""
        return 1 << 2

    @flag_value
    def started_onboarding(self):
        """:class:`bool`: Returns ``True`` if the member has started onboarding."""
        return 1 << 3


@fill_with_flags()
class Intents(BaseFlags):
    r"""Wraps up a Discord gateway intent flag.

    Similar to :class:`Permissions`\, the properties provided are two way.
    You can set and retrieve individual bits using the properties as if they
    were regular bools.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    This is used to disable certain gateway features that are unnecessary to
    run your bot. To make use of this, it is passed to the ``intents`` keyword
    argument of :class:`Client`.

    .. versionadded:: 1.5

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    __slots__ = ()

    def __init__(self, **kwargs: bool) -> None:
        self.value = self.DEFAULT_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f"{key!r} is not a valid flag name.")
            setattr(self, key, value)

    @classmethod
    def all(cls) -> Self:
        """A factory method that creates a :class:`Intents` with everything enabled."""
        self = cls.__new__(cls)
        add_bits: Callable[[int, int], int] = lambda a, b: a | b
        self.value = reduce(add_bits, cls.VALID_FLAGS.values())
        return self

    @classmethod
    def none(cls) -> Self:
        """A factory method that creates a :class:`Intents` with everything disabled."""
        self = cls.__new__(cls)
        self.value = self.DEFAULT_VALUE
        return self

    @classmethod
    def default(cls) -> Self:
        """A factory method that creates a :class:`Intents` with everything enabled
        except :attr:`presences`, :attr:`members`, and :attr:`message_content`.
        """
        self = cls.all()
        self.presences = False
        self.members = False
        self.message_content = False
        return self

    @flag_value
    def guilds(self):
        """:class:`bool`: Whether guild related events are enabled.

        This corresponds to the following events:

        - :func:`on_guild_join`
        - :func:`on_guild_remove`
        - :func:`on_guild_available`
        - :func:`on_guild_unavailable`
        - :func:`on_guild_channel_update`
        - :func:`on_guild_channel_create`
        - :func:`on_guild_channel_delete`
        - :func:`on_guild_channel_pins_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Client.guilds`
        - :class:`Guild` and all its attributes.
        - :meth:`Client.get_channel`
        - :meth:`Client.get_all_channels`

        It is highly advisable to leave this intent enabled for your bot to function.
        """
        return 1 << 0

    @flag_value
    def members(self):
        """:class:`bool`: Whether guild member related events are enabled.

        This corresponds to the following events:

        - :func:`on_member_join`
        - :func:`on_member_remove`
        - :func:`on_member_update`
        - :func:`on_user_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :meth:`Client.get_all_members`
        - :meth:`Client.get_user`
        - :meth:`Guild.chunk`
        - :meth:`Guild.fetch_members`
        - :meth:`Guild.get_member`
        - :attr:`Guild.members`
        - :attr:`Member.roles`
        - :attr:`Member.nick`
        - :attr:`Member.premium_since`
        - :attr:`User.name`
        - :attr:`User.avatar`
        - :attr:`User.discriminator`

        For more information go to the :ref:`member intent documentation <need_members_intent>`.

        .. note::

            Currently, this requires opting in explicitly via the developer portal as well.
            Bots in over 100 guilds will need to apply to Discord for verification.
        """
        return 1 << 1

    @flag_value
    def moderation(self):
        """:class:`bool`: Whether guild moderation related events are enabled.

        This corresponds to the following events:

        - :func:`on_member_ban`
        - :func:`on_member_unban`
        - :func:`on_audit_log_entry_create`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 2

    @alias_flag_value
    def bans(self):
        """:class:`bool`: Alias of :attr:`.moderation`.

        .. versionchanged:: 2.4
            Changed to an alias.
        """
        return 1 << 2

    @flag_value
    def emojis(self):
        """:class:`bool`: Alias of :attr:`.emojis_and_stickers`.

        .. versionchanged:: 2.0
            Changed to an alias.
        """
        return 1 << 3

    @alias_flag_value
    def emojis_and_stickers(self):
        """:class:`bool`: Whether guild emoji and sticker related events are enabled.

        .. versionadded:: 2.0

        This corresponds to the following events:

        - :func:`on_guild_emojis_update`
        - :func:`on_guild_stickers_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Emoji`
        - :class:`GuildSticker`
        - :meth:`Client.get_emoji`
        - :meth:`Client.get_sticker`
        - :meth:`Client.emojis`
        - :meth:`Client.stickers`
        - :attr:`Guild.emojis`
        - :attr:`Guild.stickers`
        """
        return 1 << 3

    @flag_value
    def integrations(self):
        """:class:`bool`: Whether guild integration related events are enabled.

        This corresponds to the following events:

        - :func:`on_guild_integrations_update`
        - :func:`on_integration_create`
        - :func:`on_integration_update`
        - :func:`on_raw_integration_delete`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 4

    @flag_value
    def webhooks(self):
        """:class:`bool`: Whether guild webhook related events are enabled.

        This corresponds to the following events:

        - :func:`on_webhooks_update`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 5

    @flag_value
    def invites(self):
        """:class:`bool`: Whether guild invite related events are enabled.

        This corresponds to the following events:

        - :func:`on_invite_create`
        - :func:`on_invite_delete`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 6

    @flag_value
    def voice_states(self):
        """:class:`bool`: Whether guild voice state related events are enabled.

        This corresponds to the following events:

        - :func:`on_voice_state_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`VoiceChannel.members`
        - :attr:`VoiceChannel.voice_states`
        - :attr:`Member.voice`

        .. note::

            This intent is required to connect to voice.
        """
        return 1 << 7

    @flag_value
    def presences(self):
        """:class:`bool`: Whether guild presence related events are enabled.

        This corresponds to the following events:

        - :func:`on_presence_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Member.activities`
        - :attr:`Member.status`
        - :attr:`Member.raw_status`

        For more information go to the :ref:`presence intent documentation <need_presence_intent>`.

        .. note::

            Currently, this requires opting in explicitly via the developer portal as well.
            Bots in over 100 guilds will need to apply to Discord for verification.
        """
        return 1 << 8

    @alias_flag_value
    def messages(self):
        """:class:`bool`: Whether guild and direct message related events are enabled.

        This is a shortcut to set or get both :attr:`guild_messages` and :attr:`dm_messages`.

        This corresponds to the following events:

        - :func:`on_message` (both guilds and DMs)
        - :func:`on_message_edit` (both guilds and DMs)
        - :func:`on_message_delete` (both guilds and DMs)
        - :func:`on_raw_message_delete` (both guilds and DMs)
        - :func:`on_raw_message_edit` (both guilds and DMs)

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Message`
        - :attr:`Client.cached_messages`

        Note that due to an implicit relationship this also corresponds to the following events:

        - :func:`on_reaction_add` (both guilds and DMs)
        - :func:`on_reaction_remove` (both guilds and DMs)
        - :func:`on_reaction_clear` (both guilds and DMs)
        """
        return (1 << 9) | (1 << 12)

    @flag_value
    def guild_messages(self):
        """:class:`bool`: Whether guild message related events are enabled.

        See also :attr:`dm_messages` for DMs or :attr:`messages` for both.

        This corresponds to the following events:

        - :func:`on_message` (only for guilds)
        - :func:`on_message_edit` (only for guilds)
        - :func:`on_message_delete` (only for guilds)
        - :func:`on_raw_message_delete` (only for guilds)
        - :func:`on_raw_message_edit` (only for guilds)

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Message`
        - :attr:`Client.cached_messages` (only for guilds)

        Note that due to an implicit relationship this also corresponds to the following events:

        - :func:`on_reaction_add` (only for guilds)
        - :func:`on_reaction_remove` (only for guilds)
        - :func:`on_reaction_clear` (only for guilds)
        """
        return 1 << 9

    @flag_value
    def dm_messages(self):
        """:class:`bool`: Whether direct message related events are enabled.

        See also :attr:`guild_messages` for guilds or :attr:`messages` for both.

        This corresponds to the following events:

        - :func:`on_message` (only for DMs)
        - :func:`on_message_edit` (only for DMs)
        - :func:`on_message_delete` (only for DMs)
        - :func:`on_raw_message_delete` (only for DMs)
        - :func:`on_raw_message_edit` (only for DMs)

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Message`
        - :attr:`Client.cached_messages` (only for DMs)

        Note that due to an implicit relationship this also corresponds to the following events:

        - :func:`on_reaction_add` (only for DMs)
        - :func:`on_reaction_remove` (only for DMs)
        - :func:`on_reaction_clear` (only for DMs)
        """
        return 1 << 12

    @alias_flag_value
    def reactions(self):
        """:class:`bool`: Whether guild and direct message reaction related events are enabled.

        This is a shortcut to set or get both :attr:`guild_reactions` and :attr:`dm_reactions`.

        This corresponds to the following events:

        - :func:`on_reaction_add` (both guilds and DMs)
        - :func:`on_reaction_remove` (both guilds and DMs)
        - :func:`on_reaction_clear` (both guilds and DMs)
        - :func:`on_raw_reaction_add` (both guilds and DMs)
        - :func:`on_raw_reaction_remove` (both guilds and DMs)
        - :func:`on_raw_reaction_clear` (both guilds and DMs)

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Message.reactions` (both guild and DM messages)
        """
        return (1 << 10) | (1 << 13)

    @flag_value
    def guild_reactions(self):
        """:class:`bool`: Whether guild message reaction related events are enabled.

        See also :attr:`dm_reactions` for DMs or :attr:`reactions` for both.

        This corresponds to the following events:

        - :func:`on_reaction_add` (only for guilds)
        - :func:`on_reaction_remove` (only for guilds)
        - :func:`on_reaction_clear` (only for guilds)
        - :func:`on_raw_reaction_add` (only for guilds)
        - :func:`on_raw_reaction_remove` (only for guilds)
        - :func:`on_raw_reaction_clear` (only for guilds)

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Message.reactions` (only for guild messages)
        """
        return 1 << 10

    @flag_value
    def dm_reactions(self):
        """:class:`bool`: Whether direct message reaction related events are enabled.

        See also :attr:`guild_reactions` for guilds or :attr:`reactions` for both.

        This corresponds to the following events:

        - :func:`on_reaction_add` (only for DMs)
        - :func:`on_reaction_remove` (only for DMs)
        - :func:`on_reaction_clear` (only for DMs)
        - :func:`on_raw_reaction_add` (only for DMs)
        - :func:`on_raw_reaction_remove` (only for DMs)
        - :func:`on_raw_reaction_clear` (only for DMs)

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Message.reactions` (only for DM messages)
        """
        return 1 << 13

    @alias_flag_value
    def typing(self):
        """:class:`bool`: Whether guild and direct message typing related events are enabled.

        This is a shortcut to set or get both :attr:`guild_typing` and :attr:`dm_typing`.

        This corresponds to the following events:

        - :func:`on_typing` (both guilds and DMs)

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return (1 << 11) | (1 << 14)

    @flag_value
    def guild_typing(self):
        """:class:`bool`: Whether guild and direct message typing related events are enabled.

        See also :attr:`dm_typing` for DMs or :attr:`typing` for both.

        This corresponds to the following events:

        - :func:`on_typing` (only for guilds)

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 11

    @flag_value
    def dm_typing(self):
        """:class:`bool`: Whether guild and direct message typing related events are enabled.

        See also :attr:`guild_typing` for guilds or :attr:`typing` for both.

        This corresponds to the following events:

        - :func:`on_typing` (only for DMs)

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 14

    @flag_value
    def message_content(self):
        """:class:`bool`: Whether most message content can be accessed.

        Without this intent, the following attributes may appear empty - either an
        empty string or empty array depending on the data type:

        - :attr:`Message.content`
        - :attr:`Message.embeds`
        - :attr:`Message.attachments`
        - :attr:`Message.components`

        A bot will always be able to get these attributes from:

        - Messages the bot sends
        - Messages the bot receives in DMs
        - Messages in which the bot is mentioned

        For more information go to the :ref:`message content intent documentation <need_message_content_intent>`.

        .. note::

            As of September 1, 2022, this requires opting in explicitly via the developer portal as well.
            Bots in over 100 guilds will need to apply to Discord for verification.
        """
        return 1 << 15

    @flag_value
    def scheduled_events(self):
        """:class:`bool`: Whether scheduled events related events are enabled.

        This corresponds to the following events:

        - :func:`on_guild_scheduled_event_create`
        - :func:`on_guild_scheduled_event_delete`
        - :func:`on_guild_scheduled_event_update`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 16

    @flag_value
    def auto_moderation_configuration(self):
        """:class:`bool`: Whether auto moderation configuration related events are enabled.

        This corresponds to the following events:

        - :func:`on_auto_moderation_rule_create`
        - :func:`on_auto_moderation_rule_update`
        - :func:`on_auto_moderation_rule_delete`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 20

    @flag_value
    def auto_moderation_execution(self):
        """:class:`bool`: Whether auto moderation execution related events are enabled.

        This corresponds to the following events:

        - :func:`on_auto_moderation_action_execution`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return 1 << 21

    @alias_flag_value
    def auto_moderation(self):
        """:class:`bool`: Whether auto moderation related events are enabled.

        This is a shortcut to set or get both
        :attr:`auto_moderation_configuration` and :attr:`auto_moderation_execution`.

        This corresponds to the following events:

        - :func:`on_auto_moderation_rule_create`
        - :func:`on_auto_moderation_rule_update`
        - :func:`on_auto_moderation_rule_delete`
        - :func:`on_auto_moderation_action_execution`

        This does not correspond to any attributes or classes in the library in terms of cache.
        """
        return (1 << 20) | (1 << 21)


@fill_with_flags()
class MemberCacheFlags(BaseFlags):
    """Controls the library's cache policy when it comes to members.

    This allows for finer grained control over what members are cached.
    Note that the bot's own member is always cached. This class is passed
    to the ``member_cache_flags`` parameter in :class:`Client`.

    Due to a quirk in how Discord works, in order to ensure proper cleanup
    of cache resources it is recommended to have :attr:`Intents.members`
    enabled. Otherwise the library cannot know when a member leaves a guild and
    is thus unable to cleanup after itself.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    The default value is all flags enabled.

    .. versionadded:: 1.5

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    __slots__ = ()

    def __init__(self, **kwargs: bool) -> None:
        bits = max(self.VALID_FLAGS.values()).bit_length()
        self.value = (1 << bits) - 1
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f"{key!r} is not a valid flag name.")
            setattr(self, key, value)

    @classmethod
    def all(cls) -> Self:
        """A factory method that creates a :class:`MemberCacheFlags` with everything enabled."""
        bits = max(cls.VALID_FLAGS.values()).bit_length()
        value = (1 << bits) - 1
        self = cls.__new__(cls)
        self.value = value
        return self

    @classmethod
    def none(cls) -> Self:
        """A factory method that creates a :class:`MemberCacheFlags` with everything disabled."""
        self = cls.__new__(cls)
        self.value = self.DEFAULT_VALUE
        return self

    @property
    def _empty(self):
        return self.value == self.DEFAULT_VALUE

    @flag_value
    def voice(self) -> int:
        """:class:`bool`: Whether to cache members that are in voice.

        This requires :attr:`Intents.voice_states`.

        Members that leave voice are no longer cached.
        """
        return 1

    @flag_value
    def joined(self) -> int:
        """:class:`bool`: Whether to cache members that joined the guild
        or are chunked as part of the initial log in flow.

        This requires :attr:`Intents.members`.

        Members that leave the guild are no longer cached.
        """
        return 2

    @classmethod
    def from_intents(cls, intents: Intents) -> Self:
        """A factory method that creates a :class:`MemberCacheFlags` based on
        the currently selected :class:`Intents`.

        Parameters
        ----------
        intents: :class:`Intents`
            The intents to select from.

        Returns
        -------
        :class:`MemberCacheFlags`
            The resulting member cache flags.
        """

        self = cls.none()
        if intents.members:
            self.joined = True
        if intents.voice_states:
            self.voice = True

        return self

    def _verify_intents(self, intents: Intents):
        if self.voice and not intents.voice_states:
            raise ValueError("MemberCacheFlags.voice requires Intents.voice_states")

        if self.joined and not intents.members:
            raise ValueError("MemberCacheFlags.joined requires Intents.members")

    @property
    def _voice_only(self):
        return self.value == 1


@fill_with_flags()
class ApplicationFlags(BaseFlags):
    r"""Wraps up the Discord Application flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two ApplicationFlags are equal.
        .. describe:: x != y

            Checks if two ApplicationFlags are not equal.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

    .. versionadded:: 2.0

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def application_auto_moderation_rule_create(self):
        """:class:`bool`: Returns ``True`` if the application uses the Auto Moderation API.

        .. versionadded:: 2.6
        """
        return 1 << 6

    @flag_value
    def gateway_presence(self):
        """:class:`bool`: Returns ``True`` if the application is verified and is allowed to
        receive presence information over the gateway.
        """
        return 1 << 12

    @flag_value
    def gateway_presence_limited(self):
        """:class:`bool`: Returns ``True`` if the application is allowed to receive limited
        presence information over the gateway.
        """
        return 1 << 13

    @flag_value
    def gateway_guild_members(self):
        """:class:`bool`: Returns ``True`` if the application is verified and is allowed to
        receive guild members information over the gateway.
        """
        return 1 << 14

    @flag_value
    def gateway_guild_members_limited(self):
        """:class:`bool`: Returns ``True`` if the application is allowed to receive limited
        guild members information over the gateway.
        """
        return 1 << 15

    @flag_value
    def verification_pending_guild_limit(self):
        """:class:`bool`: Returns ``True`` if the application is currently pending verification
        and has hit the guild limit.
        """
        return 1 << 16

    @flag_value
    def embedded(self):
        """:class:`bool`: Returns ``True`` if the application is embedded within the Discord client."""
        return 1 << 17

    @flag_value
    def gateway_message_content(self):
        """:class:`bool`: Returns ``True`` if the application is allowed to receive message content
        over the gateway.
        """
        return 1 << 18

    @flag_value
    def gateway_message_content_limited(self):
        """:class:`bool`: Returns ``True`` if the application is allowed to receive limited
        message content over the gateway.
        """
        return 1 << 19

    @flag_value
    def application_command_badge(self):
        """:class:`bool`: Returns ``True`` if the application has registered global application commands."""
        return 1 << 23


@fill_with_flags()
class AttachmentFlags(BaseFlags):
    r"""Wraps up the Discord Attachment flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two AttachmentFlags are equal.
        .. describe:: x != y

            Checks if two AttachmentFlags are not equal.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

    .. versionadded:: 2.6

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def is_remix(self):
        """:class:`bool`: Returns ``True`` if the attachment has been edited using the remix feature on mobile."""
        return 1 << 2


@fill_with_flags()
class RoleFlags(BaseFlags):
    r"""Wraps up the Discord Guild Role Flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two RoleFlags are equal.
        .. describe:: x != y

            Checks if two RoleFlags are not equal.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

    .. versionadded:: 2.6

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def in_prompt(self):
        """:class:`bool`: Returns ``True`` if the role can be selected in an onboarding prompt."""
        return 1 << 0
