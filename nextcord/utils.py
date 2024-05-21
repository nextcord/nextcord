# SPDX-License-Identifier: MIT

# reportUnknownVariableType and reportUnknownMemberType:
# array.array is poorly typed (SnowflakeList superclass)
# pyright: strict, reportUnknownVariableType = false, reportUnknownMemberType = false
from __future__ import annotations

import array
import asyncio
import datetime
import functools
import inspect
import json
import re
import sys
import unicodedata
import warnings
from base64 import b64encode
from bisect import bisect_left
from inspect import isawaitable as _isawaitable, signature as _signature
from operator import attrgetter
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    ForwardRef,
    Generic,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from .errors import InvalidArgument
from .file import File

try:
    import orjson
except ModuleNotFoundError:
    _orjson_defined = False

    def to_json(obj: Any) -> str:
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=True)

    from_json = json.loads
else:
    _orjson_defined = True

    def to_json(obj: Any) -> str:
        return orjson.dumps(obj).decode("utf-8")

    from_json = orjson.loads


HAS_ORJSON = _orjson_defined


PY_310 = sys.version_info >= (3, 10)


if PY_310:
    from types import UnionType  # type: ignore

    # UnionType is the annotation origin when doing Python 3.10 unions. Example: "str | None"
else:
    UnionType = None


if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = (
    "oauth_url",
    "snowflake_time",
    "time_snowflake",
    "find",
    "get",
    "sleep_until",
    "utcnow",
    "remove_markdown",
    "escape_markdown",
    "escape_mentions",
    "parse_raw_mentions",
    "parse_raw_role_mentions",
    "parse_raw_channel_mentions",
    "as_chunks",
    "format_dt",
    "format_ts",
    "cached_property",
)

DISCORD_EPOCH = 1420070400000


class _MissingSentinel:
    def __eq__(self, other: Any) -> bool:
        return self is other

    def __hash__(self):
        return id(self)

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _MissingSentinel()


class _cached_property:
    def __init__(self, function: Callable[..., Any]) -> None:
        self.function = function
        self.__doc__ = function.__doc__

    def __get__(self, instance: Any, owner: Any):
        if instance is None:
            return self

        value = self.function(instance)
        setattr(instance, self.function.__name__, value)

        return value


if TYPE_CHECKING:
    from functools import cached_property

    from typing_extensions import ParamSpec

    from .abc import Snowflake
    from .asset import Asset
    from .invite import Invite
    from .message import Attachment
    from .permissions import Permissions
    from .template import Template

    P = ParamSpec("P")
else:
    cached_property = _cached_property


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
_Iter = Union[Iterator[T], AsyncIterator[T]]
ArrayT = TypeVar("ArrayT", int, float, str)


class CachedSlotProperty(Generic[T, T_co]):
    def __init__(self, name: str, function: Callable[[T], T_co]) -> None:
        self.name = name
        self.function = function
        self.__doc__ = function.__doc__

    @overload
    def __get__(self, instance: None, owner: Type[T]) -> CachedSlotProperty[T, T_co]:
        ...

    @overload
    def __get__(self, instance: T, owner: Type[T]) -> T_co:
        ...

    def __get__(self, instance: Optional[T], owner: Type[T]) -> Any:
        if instance is None:
            return self

        try:
            return getattr(instance, self.name)
        except AttributeError:
            value = self.function(instance)
            setattr(instance, self.name, value)
            return value


class classproperty(Generic[T_co]):
    def __init__(self, fget: Callable[[Any], T_co]) -> None:
        self.fget = fget

    def __get__(self, instance: Optional[Any], owner: Type[Any]) -> T_co:
        return self.fget(owner)

    def __set__(self, instance: Any, value: Any) -> None:
        raise AttributeError("Cannot set attribute")


def cached_slot_property(
    name: str,
) -> Callable[[Callable[[T], T_co]], CachedSlotProperty[T, T_co]]:
    def decorator(func: Callable[[T], T_co]) -> CachedSlotProperty[T, T_co]:
        return CachedSlotProperty(name, func)

    return decorator


class SequenceProxy(Sequence[T_co], Generic[T_co]):
    """Read-only proxy of a Sequence."""

    def __init__(self, proxied: Sequence[T_co]) -> None:
        self.__proxied = proxied

    # Likely Pyright bug. The base method doesn't seem to even have a return type.
    # base method returns type "Sequence[T_co@SequenceProxy]"
    # override returns type "T_co@SequenceProxy"
    def __getitem__(self, idx: int) -> T_co:  # pyright: ignore
        return self.__proxied[idx]

    def __len__(self) -> int:
        return len(self.__proxied)

    def __contains__(self, item: Any) -> bool:
        return item in self.__proxied

    def __iter__(self) -> Iterator[T_co]:
        return iter(self.__proxied)

    def __reversed__(self) -> Iterator[T_co]:
        return reversed(self.__proxied)

    def index(self, value: Any, *args: Any, **kwargs: Any) -> int:
        return self.__proxied.index(value, *args, **kwargs)

    def count(self, value: Any) -> int:
        return self.__proxied.count(value)


@overload
def parse_time(timestamp: None) -> None:
    ...


@overload
def parse_time(timestamp: str) -> datetime.datetime:
    ...


@overload
def parse_time(timestamp: Optional[str]) -> Optional[datetime.datetime]:
    ...


def parse_time(timestamp: Optional[str]) -> Optional[datetime.datetime]:
    if timestamp:
        return datetime.datetime.fromisoformat(timestamp)
    return None


def copy_doc(original: Callable[..., Any]) -> Callable[[T], T]:
    def decorator(overriden: T) -> T:
        overriden.__doc__ = original.__doc__
        overriden.__signature__ = _signature(original)  # type: ignore
        return overriden

    return decorator


def deprecated(
    instead: Optional[str] = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def actual_decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def decorated(*args: P.args, **kwargs: P.kwargs) -> T:
            warnings.simplefilter("always", DeprecationWarning)  # turn off filter
            if instead:
                fmt = "{0.__name__} is deprecated, use {1} instead."
            else:
                fmt = "{0.__name__} is deprecated."

            warnings.warn(fmt.format(func, instead), stacklevel=3, category=DeprecationWarning)
            warnings.simplefilter("default", DeprecationWarning)  # reset filter
            return func(*args, **kwargs)

        return decorated

    return actual_decorator


def oauth_url(
    client_id: Union[int, str],
    *,
    permissions: Permissions = MISSING,
    guild: Snowflake = MISSING,
    redirect_uri: str = MISSING,
    scopes: Iterable[str] = MISSING,
    disable_guild_select: bool = False,
) -> str:
    """A helper function that returns the OAuth2 URL for inviting the bot
    into guilds.

    Parameters
    ----------
    client_id: Union[:class:`int`, :class:`str`]
        The client ID for your bot.
    permissions: :class:`~nextcord.Permissions`
        The permissions you're requesting. If not given then you won't be requesting any
        permissions.
    guild: :class:`~nextcord.abc.Snowflake`
        The guild to pre-select in the authorization screen, if available.
    redirect_uri: :class:`str`
        An optional valid redirect URI.
    scopes: Iterable[:class:`str`]
        An optional valid list of scopes. Defaults to ``('bot',)``.

        .. versionadded:: 1.7
    disable_guild_select: :class:`bool`
        Whether to disallow the user from changing the guild dropdown.

        .. versionadded:: 2.0

    Returns
    -------
    :class:`str`
        The OAuth2 URL for inviting the bot into guilds.
    """
    url = f"https://discord.com/oauth2/authorize?client_id={client_id}"
    url += "&scope=" + "+".join(scopes or ("bot",))
    if permissions is not MISSING:
        url += f"&permissions={permissions.value}"
    if guild is not MISSING:
        url += f"&guild_id={guild.id}"
    if redirect_uri is not MISSING:
        from urllib.parse import urlencode

        url += "&response_type=code&" + urlencode({"redirect_uri": redirect_uri})
    if disable_guild_select:
        url += "&disable_guild_select=true"
    return url


def snowflake_time(id: int) -> datetime.datetime:
    """
    Parameters
    ----------
    id: :class:`int`
        The snowflake ID.

    Returns
    -------
    :class:`datetime.datetime`
        An aware datetime in UTC representing the creation time of the snowflake.
    """
    timestamp = ((id >> 22) + DISCORD_EPOCH) / 1000
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)


def time_snowflake(dt: datetime.datetime, high: bool = False) -> int:
    """Returns a numeric snowflake pretending to be created at the given date.

    When using as the lower end of a range, use ``time_snowflake(high=False) - 1``
    to be inclusive, ``high=True`` to be exclusive.

    When using as the higher end of a range, use ``time_snowflake(high=True) + 1``
    to be inclusive, ``high=False`` to be exclusive

    Parameters
    ----------
    dt: :class:`datetime.datetime`
        A datetime object to convert to a snowflake.
        If naive, the timezone is assumed to be local time.
    high: :class:`bool`
        Whether or not to set the lower 22 bit to high or low.

    Returns
    -------
    :class:`int`
        The snowflake representing the time given.
    """
    discord_millis = int(dt.timestamp() * 1000 - DISCORD_EPOCH)
    return (discord_millis << 22) + (2**22 - 1 if high else 0)


def find(predicate: Callable[[T], Any], seq: Iterable[T]) -> Optional[T]:
    """A helper to return the first element found in the sequence
    that meets the predicate. For example: ::

        member = nextcord.utils.find(lambda m: m.name == 'Mighty', channel.guild.members)

    would find the first :class:`~nextcord.Member` whose name is 'Mighty' and return it.
    If an entry is not found, then ``None`` is returned.

    This is different from :func:`py:filter` due to the fact it stops the moment it finds
    a valid entry.

    Parameters
    ----------
    predicate
        A function that returns a boolean-like result.
    seq: :class:`collections.abc.Iterable`
        The iterable to search through.
    """

    for element in seq:
        if predicate(element):
            return element
    return None


def _key_fmt(key: str) -> str:
    # Private helper for `nextcord.utils.get`. Formats the attribute
    # names in a content aware manner. When special variables are
    # provided, double trailing and leading underscores are ignored.
    # ex. "__class______name__" -> "__class__.__name__"
    # In case of underscore conflicts, it will assume trailing underscores.
    # ex. "_privateattr___subattr" -> "_privateattr_.subattr"

    if key.startswith("__") and key.endswith("__"):
        return re.sub(r"_{6}", "__.__", key)
    return re.sub(r"__(?!_)", ".", key)


def get(iterable: Iterable[T], **attrs: Any) -> Optional[T]:
    r"""A helper that returns the first element in the iterable that meets
    all the traits passed in ``attrs``. This is an alternative for
    :func:`~nextcord.utils.find`.

    When multiple attributes are specified, they are checked using
    logical AND, not logical OR. Meaning they have to meet every
    attribute passed in and not one of them.

    To have a nested attribute search (i.e. search by ``x.y``) then
    pass in ``x__y`` as the keyword argument.

    If nothing is found that matches the attributes passed, then
    ``None`` is returned.

    Examples
    --------

    Basic usage:

    .. code-block:: python3

        member = nextcord.utils.get(message.guild.members, name='Foo')

    Multiple attribute matching:

    .. code-block:: python3

        channel = nextcord.utils.get(guild.voice_channels, name='Foo', bitrate=64000)

    Nested attribute matching:

    .. code-block:: python3

        channel = nextcord.utils.get(client.get_all_channels(), guild__name='Cool', name='general')

    Parameters
    ----------
    iterable
        An iterable to search through.
    \*\*attrs
        Keyword arguments that denote attributes to search with.
    """

    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(_key_fmt(k))
        for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [(attrget(_key_fmt(attr)), value) for attr, value in attrs.items()]

    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None


def unique(iterable: Iterable[T]) -> List[T]:
    return list(dict.fromkeys(iterable))


def get_as_snowflake(data: Any, key: str) -> Optional[int]:
    try:
        value = data[key]
    except KeyError:
        return None
    else:
        return value and int(value)


def _get_mime_type_for_image(data: bytes) -> str:
    if data.startswith(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"):
        return "image/png"
    if data[0:3] == b"\xff\xd8\xff" or data[6:10] in (b"JFIF", b"Exif"):
        return "image/jpeg"
    if data.startswith((b"\x47\x49\x46\x38\x37\x61", b"\x47\x49\x46\x38\x39\x61")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"

    raise InvalidArgument("Unsupported image type given")


def _bytes_to_base64_data(data: bytes) -> str:
    fmt = "data:{mime};base64,{data}"
    mime = _get_mime_type_for_image(data)
    b64 = b64encode(data).decode("ascii")
    return fmt.format(mime=mime, data=b64)


async def obj_to_base64_data(obj: Optional[Union[bytes, Attachment, Asset, File]]) -> Optional[str]:
    if obj is None:
        return obj
    if isinstance(obj, bytes):
        return _bytes_to_base64_data(obj)
    if isinstance(obj, File):
        return _bytes_to_base64_data(obj.fp.read())
    return _bytes_to_base64_data(await obj.read())


def parse_ratelimit_header(request: Any, *, use_clock: bool = False) -> float:
    reset_after: Optional[str] = request.headers.get("X-Ratelimit-Reset-After")
    if use_clock or not reset_after:
        utc = datetime.timezone.utc
        now = datetime.datetime.now(utc)
        reset = datetime.datetime.fromtimestamp(float(request.headers["X-Ratelimit-Reset"]), utc)
        return (reset - now).total_seconds()
    return float(reset_after)


async def maybe_coroutine(
    f: Callable[P, Union[T, Awaitable[T]]], *args: P.args, **kwargs: P.kwargs
) -> T:
    value = f(*args, **kwargs)
    if _isawaitable(value):
        return await value
    return value  # type: ignore
    # type ignored as `_isawaitable` provides `TypeGuard[Awaitable[Any]]`
    # yet we need a more specific type guard


async def async_all(
    gen: Iterable[Awaitable[T]], *, check: Callable[[Awaitable[T]], bool] = _isawaitable
) -> bool:
    for elem in gen:
        if check(elem):
            elem = await elem
        if not elem:
            return False
    return True


async def sane_wait_for(
    futures: Iterable[Awaitable[T]], *, timeout: Optional[float]
) -> Set[asyncio.Task[T]]:
    ensured = [asyncio.ensure_future(fut) for fut in futures]
    done, pending = await asyncio.wait(ensured, timeout=timeout, return_when=asyncio.ALL_COMPLETED)

    if len(pending) != 0:
        raise asyncio.TimeoutError

    return done


def get_slots(cls: Type[Any]) -> Iterator[str]:
    for mro in reversed(cls.__mro__):
        try:
            yield from mro.__slots__  # type: ignore # handled below
        except AttributeError:
            continue


def compute_timedelta(dt: datetime.datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.astimezone()
    now = datetime.datetime.now(datetime.timezone.utc)
    return max((dt - now).total_seconds(), 0)


async def sleep_until(when: datetime.datetime, result: Optional[T] = None) -> Optional[T]:
    """|coro|

    Sleep until a specified time.

    If the time supplied is in the past this function will yield instantly.

    .. versionadded:: 1.3

    Parameters
    ----------
    when: :class:`datetime.datetime`
        The timestamp in which to sleep until. If the datetime is naive then
        it is assumed to be local time.
    result: Any
        If provided is returned to the caller when the coroutine completes.
    """
    delta = compute_timedelta(when)
    return await asyncio.sleep(delta, result)


def utcnow() -> datetime.datetime:
    """A helper function to return an aware UTC datetime representing the current time.

    This should be preferred to :meth:`datetime.datetime.utcnow` since it is an aware
    datetime, compared to the naive datetime in the standard library.

    .. versionadded:: 2.0

    Returns
    -------
    :class:`datetime.datetime`
        The current aware datetime in UTC.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def valid_icon_size(size: int) -> bool:
    """Icons must be power of 2 within [16, 4096]."""
    return not size & (size - 1) and 4096 >= size >= 16


# Uncomment when https://github.com/python/cpython/issues/98658 is fixed.
# class SnowflakeList(array.array[ArrayT], Generic[ArrayT]):
class SnowflakeList(array.array):  # pyright: ignore[reportMissingTypeArgument]
    """Internal data storage class to efficiently store a list of snowflakes.

    This should have the following characteristics:

    - Low memory usage
    - O(n) iteration (obviously)
    - O(n log n) initial creation if data is unsorted
    - O(log n) search and indexing
    - O(n) insertion
    """

    __slots__ = ()

    if TYPE_CHECKING:

        def __init__(self, data: Iterable[int], *, is_sorted: bool = False) -> None:
            ...

    def __new__(cls, data: Iterable[int], *, is_sorted: bool = False) -> Self:
        return array.array.__new__(cls, "Q", data if is_sorted else sorted(data))  # type: ignore

    def add(self, element: int) -> None:
        i = bisect_left(self, element)
        self.insert(i, element)

    def get(self, element: int) -> Optional[int]:
        i = bisect_left(self, element)
        return self[i] if i != len(self) and self[i] == element else None

    def has(self, element: int) -> bool:
        i = bisect_left(self, element)
        return i != len(self) and self[i] == element


_IS_ASCII = re.compile(r"^[\x00-\x7f]+$")


def string_width(string: str) -> int:
    """Returns string's width."""
    match = _IS_ASCII.match(string)
    if match:
        return match.endpos

    UNICODE_WIDE_CHAR_TYPE = "WFA"
    func = unicodedata.east_asian_width
    return sum(2 if func(char) in UNICODE_WIDE_CHAR_TYPE else 1 for char in string)


def resolve_invite(invite: Union[Invite, str]) -> str:
    """
    Resolves an invite from a :class:`~nextcord.Invite`, URL or code.

    Parameters
    ----------
    invite: Union[:class:`~nextcord.Invite`, :class:`str`]
        The invite.

    Returns
    -------
    :class:`str`
        The invite code.
    """
    from .invite import Invite  # circular import

    if isinstance(invite, Invite):
        if not invite.code:
            raise NotImplementedError("Can not resolve the invite if the code is `None`")

        return invite.code

    rx = r"(?:https?\:\/\/)?discord(?:\.gg|(?:app)?\.com\/invite)\/(.+)"
    m = re.match(rx, invite)
    if m:
        return m.group(1)

    return invite


def resolve_template(code: Union[Template, str]) -> str:
    """
    Resolves a template code from a :class:`~nextcord.Template`, URL or code.

    .. versionadded:: 1.4

    Parameters
    ----------
    code: Union[:class:`~nextcord.Template`, :class:`str`]
        The code.

    Returns
    -------
    :class:`str`
        The template code.
    """
    from .template import Template  # circular import

    if isinstance(code, Template):
        return code.code
    rx = r"(?:https?\:\/\/)?discord(?:\.new|(?:app)?\.com\/template)\/(.+)"
    m = re.match(rx, code)
    if m:
        return m.group(1)
    return code


_MARKDOWN_ESCAPE_SUBREGEX = "|".join(
    r"\{0}(?=([\s\S]*((?<!\{0})\{0})))".format(c) for c in ("*", "`", "_", "~", "|")
)

_MARKDOWN_ESCAPE_COMMON = r"^>(?:>>)?\s|\[.+\]\(.+\)"

_MARKDOWN_ESCAPE_REGEX = re.compile(
    rf"(?P<markdown>{_MARKDOWN_ESCAPE_SUBREGEX}|{_MARKDOWN_ESCAPE_COMMON})",
    re.MULTILINE,
)

_URL_REGEX = r"(?P<url><[^: >]+:\/[^ >]+>|(?:https?|steam):\/\/[^\s<]+[^<.,:;\"\'\]\s])"

_MARKDOWN_STOCK_REGEX = rf"(?P<markdown>[_\\~|\*`]|{_MARKDOWN_ESCAPE_COMMON})"


def remove_markdown(text: str, *, ignore_links: bool = True) -> str:
    """A helper function that removes markdown characters.

    .. versionadded:: 1.7

    .. note::
            This function is not markdown aware and may remove meaning from the original text. For example,
            if the input contains ``10 * 5`` then it will be converted into ``10  5``.

    Parameters
    ----------
    text: :class:`str`
        The text to remove markdown from.
    ignore_links: :class:`bool`
        Whether to leave links alone when removing markdown. For example,
        if a URL in the text contains characters such as ``_`` then it will
        be left alone. Defaults to ``True``.

    Returns
    -------
    :class:`str`
        The text with the markdown special characters removed.
    """

    def replacement(match: re.Match[str]):
        groupdict = match.groupdict()
        return groupdict.get("url", "")

    regex = _MARKDOWN_STOCK_REGEX
    if ignore_links:
        regex = f"(?:{_URL_REGEX}|{regex})"
    return re.sub(regex, replacement, text, count=0, flags=re.MULTILINE)


def escape_markdown(text: str, *, as_needed: bool = False, ignore_links: bool = True) -> str:
    r"""A helper function that escapes Discord's markdown.

    Parameters
    ----------
    text: :class:`str`
        The text to escape markdown from.
    as_needed: :class:`bool`
        Whether to escape the markdown characters as needed. This
        means that it does not escape extraneous characters if it's
        not necessary, e.g. ``**hello**`` is escaped into ``\*\*hello**``
        instead of ``\*\*hello\*\*``. Note however that this can open
        you up to some clever syntax abuse. Defaults to ``False``.
    ignore_links: :class:`bool`
        Whether to leave links alone when escaping markdown. For example,
        if a URL in the text contains characters such as ``_`` then it will
        be left alone. This option is not supported with ``as_needed``.
        Defaults to ``True``.

    Returns
    -------
    :class:`str`
        The text with the markdown special characters escaped with a slash.
    """

    if not as_needed:

        def replacement(match: re.Match[str]):
            groupdict = match.groupdict()
            is_url = groupdict.get("url")
            if is_url:
                return is_url
            return "\\" + groupdict["markdown"]

        regex = _MARKDOWN_STOCK_REGEX
        if ignore_links:
            regex = f"(?:{_URL_REGEX}|{regex})"
        return re.sub(regex, replacement, text, count=0, flags=re.MULTILINE)

    text = re.sub(r"\\", r"\\\\", text)
    return _MARKDOWN_ESCAPE_REGEX.sub(r"\\\1", text)


def escape_mentions(text: str) -> str:
    """A helper function that escapes everyone, here, role, and user mentions.

    .. note::

        This does not include channel mentions.

    .. note::

        For more granular control over what mentions should be escaped
        within messages, refer to the :class:`~nextcord.AllowedMentions`
        class.

    Parameters
    ----------
    text: :class:`str`
        The text to escape mentions from.

    Returns
    -------
    :class:`str`
        The text with the mentions removed.
    """
    return re.sub(r"@(everyone|here|[!&]?[0-9]{17,20})", "@\u200b\\1", text)


def parse_raw_mentions(text: str) -> List[int]:
    """A helper function that parses mentions from a string as an array of :class:`~nextcord.User` IDs
    matched with the syntax of ``<@user_id>`` or ``<@!user_id>``.

    .. note::

        This does not include role or channel mentions. See :func:`parse_raw_role_mentions`
        and :func:`parse_raw_channel_mentions` for those.

    .. versionadded:: 2.2

    Parameters
    ----------
    text: :class:`str`
        The text to parse mentions from.

    Returns
    -------
    List[:class:`int`]
        A list of user IDs that were mentioned.
    """
    return [int(x) for x in re.findall(r"<@!?(\d{15,20})>", text)]


def parse_raw_role_mentions(text: str) -> List[int]:
    """A helper function that parses mentions from a string as an array of :class:`~nextcord.Role` IDs
    matched with the syntax of ``<@&role_id>``.

    .. versionadded:: 2.2

    Parameters
    ----------
    text: :class:`str`
        The text to parse mentions from.

    Returns
    -------
    List[:class:`int`]
        A list of role IDs that were mentioned.
    """
    return [int(x) for x in re.findall(r"<@&(\d{15,20})>", text)]


def parse_raw_channel_mentions(text: str) -> List[int]:
    """A helper function that parses mentions from a string as an array of :class:`~nextcord.abc.GuildChannel` IDs
    matched with the syntax of ``<#channel_id>``.

    .. versionadded:: 2.2

    Parameters
    ----------
    text: :class:`str`
        The text to parse mentions from.

    Returns
    -------
    List[:class:`int`]
        A list of channel IDs that were mentioned.
    """
    return [int(x) for x in re.findall(r"<#(\d{15,20})>", text)]


def _chunk(iterator: Iterator[T], max_size: int) -> Iterator[List[T]]:
    ret = []
    n = 0
    for item in iterator:
        ret.append(item)
        n += 1
        if n == max_size:
            yield ret
            ret = []
            n = 0
    if ret:
        yield ret


async def _achunk(iterator: AsyncIterator[T], max_size: int) -> AsyncIterator[List[T]]:
    ret = []
    n = 0
    async for item in iterator:
        ret.append(item)
        n += 1
        if n == max_size:
            yield ret
            ret = []
            n = 0
    if ret:
        yield ret


@overload
def as_chunks(iterator: Iterator[T], max_size: int) -> Iterator[List[T]]:
    ...


@overload
def as_chunks(iterator: AsyncIterator[T], max_size: int) -> AsyncIterator[List[T]]:
    ...


def as_chunks(iterator: _Iter[T], max_size: int) -> _Iter[List[T]]:
    """A helper function that collects an iterator into chunks of a given size.

    .. versionadded:: 2.0

    Parameters
    ----------
    iterator: Union[:class:`collections.abc.Iterator`, :class:`collections.abc.AsyncIterator`]
        The iterator to chunk, can be sync or async.
    max_size: :class:`int`
        The maximum chunk size.


    .. warning::

        The last chunk collected may not be as large as ``max_size``.

    Returns
    -------
    Union[:class:`Iterator`, :class:`AsyncIterator`]
        A new iterator which yields chunks of a given size.
    """
    if max_size <= 0:
        raise ValueError("Chunk sizes must be greater than 0.")

    if isinstance(iterator, AsyncIterator):
        return _achunk(iterator, max_size)
    return _chunk(iterator, max_size)


def flatten_literal_params(parameters: Iterable[Any]) -> Tuple[Any, ...]:
    params = []
    literal_cls = type(Literal[0])
    for p in parameters:
        if isinstance(p, literal_cls):
            params.extend(p.__args__)
        else:
            params.append(p)
    return tuple(params)


def normalise_optional_params(parameters: Iterable[Any]) -> Tuple[Any, ...]:
    none_cls = type(None)
    return (*tuple(p for p in parameters if p is not none_cls), none_cls)


def evaluate_annotation(
    tp: Any,
    globals: Dict[str, Any],
    locals: Dict[str, Any],
    cache: Dict[str, Any],
    *,
    implicit_str: bool = True,
) -> Any:
    if isinstance(tp, ForwardRef):
        tp = tp.__forward_arg__
        # ForwardRefs always evaluate their internals
        implicit_str = True

    if implicit_str and isinstance(tp, str):
        if tp in cache:
            return cache[tp]
        evaluated = eval(tp, globals, locals)  # noqa: PGH001, S307
        # eval() here uses the type annotation from the user, eval is all under control.
        cache[tp] = evaluated
        return evaluate_annotation(evaluated, globals, locals, cache)

    if hasattr(tp, "__args__"):
        implicit_str = True
        is_literal = False
        args = tp.__args__
        if not hasattr(tp, "__origin__"):
            if PY_310 and tp.__class__ is UnionType:
                converted = Union[args]  # type: ignore
                return evaluate_annotation(converted, globals, locals, cache)

            return tp
        if tp.__origin__ is Union:
            try:
                if args.index(type(None)) != len(args) - 1:
                    args = normalise_optional_params(tp.__args__)
            except ValueError:
                pass
        if tp.__origin__ is Literal:
            if not PY_310:
                args = flatten_literal_params(tp.__args__)
            implicit_str = False
            is_literal = True

        evaluated_args = tuple(
            evaluate_annotation(arg, globals, locals, cache, implicit_str=implicit_str)
            for arg in args
        )

        if is_literal and not all(
            isinstance(x, (str, int, bool, type(None))) for x in evaluated_args
        ):
            raise TypeError("Literal arguments must be of type str, int, bool, or NoneType.")

        if evaluated_args == args:
            return tp

        try:
            return tp.copy_with(evaluated_args)
        except AttributeError:
            return tp.__origin__[evaluated_args]

    return tp


def resolve_annotation(
    annotation: Any,
    globalns: Dict[str, Any],
    localns: Optional[Dict[str, Any]],
    cache: Optional[Dict[str, Any]],
) -> Any:
    if annotation is None:
        return type(None)
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)

    locals = globalns if localns is None else localns
    if cache is None:
        cache = {}
    return evaluate_annotation(annotation, globalns, locals, cache)


TimestampStyle = Literal["f", "F", "d", "D", "t", "T", "R"]


def format_dt(dt: datetime.datetime, /, style: Optional[TimestampStyle] = None) -> str:
    """A helper function to format a :class:`datetime.datetime` for presentation within Discord.

    This allows for a locale-independent way of presenting data using Discord specific Markdown.

    +-------------+----------------------------+-----------------+
    |    Style    |       Example Output       |   Description   |
    +=============+============================+=================+
    | t           | 22:57                      | Short Time      |
    +-------------+----------------------------+-----------------+
    | T           | 22:57:58                   | Long Time       |
    +-------------+----------------------------+-----------------+
    | d           | 17/05/2016                 | Short Date      |
    +-------------+----------------------------+-----------------+
    | D           | 17 May 2016                | Long Date       |
    +-------------+----------------------------+-----------------+
    | f (default) | 17 May 2016 22:57          | Short Date Time |
    +-------------+----------------------------+-----------------+
    | F           | Tuesday, 17 May 2016 22:57 | Long Date Time  |
    +-------------+----------------------------+-----------------+
    | R           | 5 years ago                | Relative Time   |
    +-------------+----------------------------+-----------------+

    Note that the exact output depends on the user's locale setting in the client. The example output
    presented is using the ``en-GB`` locale.

    .. versionadded:: 2.0

    Parameters
    ----------
    dt: :class:`datetime.datetime`
        The datetime to format.
    style: :class:`str`
        The style to format the datetime with.

    Returns
    -------
    :class:`str`
        The formatted string.
    """
    if not isinstance(dt, datetime.datetime):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise InvalidArgument("'dt' must be of type 'datetime.datetime'")
    return format_ts(int(dt.timestamp()), style=style)


def format_ts(ts: int, /, style: Optional[TimestampStyle] = None) -> str:
    """A helper function to format a Unix timestamp as an :class:`int` for presentation within Discord.

    This allows for a locale-independent way of presenting data using Discord specific Markdown.

    +-------------+----------------------------+-----------------+
    |    Style    |       Example Output       |   Description   |
    +=============+============================+=================+
    | t           | 22:57                      | Short Time      |
    +-------------+----------------------------+-----------------+
    | T           | 22:57:58                   | Long Time       |
    +-------------+----------------------------+-----------------+
    | d           | 17/05/2016                 | Short Date      |
    +-------------+----------------------------+-----------------+
    | D           | 17 May 2016                | Long Date       |
    +-------------+----------------------------+-----------------+
    | f (default) | 17 May 2016 22:57          | Short Date Time |
    +-------------+----------------------------+-----------------+
    | F           | Tuesday, 17 May 2016 22:57 | Long Date Time  |
    +-------------+----------------------------+-----------------+
    | R           | 5 years ago                | Relative Time   |
    +-------------+----------------------------+-----------------+

    Note that the exact output depends on the user's locale setting in the client. The example output
    presented is using the ``en-GB`` locale.

    .. versionadded:: 2.6

    Parameters
    ----------
    ts: :class:`int`
        The Unix timestamp to format.
    style: :class:`str`
        The style to format the timestamp with.

    Returns
    -------
    :class:`str`
        The formatted string.
    """
    if not isinstance(ts, int):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise InvalidArgument("'ts' must be of type 'int'")
    if style is None:
        return f"<t:{ts}>"
    return f"<t:{ts}:{style}>"


_FUNCTION_DESCRIPTION_REGEX = re.compile(r"\A(?:.|\n)+?(?=\Z|\r?\n\r?\n)", re.MULTILINE)

_ARG_NAME_SUBREGEX = r"(?:\\?\*)*(?P<name>[^\s:\-]+)"

_ARG_DESCRIPTION_SUBREGEX = r"(?P<description>(?:.|\n)+?(?:\Z|\r?\n(?=[\S\r\n])))"

_ARG_TYPE_SUBREGEX = r"(?P<type>.+)"

_GOOGLE_DOCSTRING_ARG_REGEX = re.compile(
    rf"^{_ARG_NAME_SUBREGEX}[ \t]*(?:\({_ARG_TYPE_SUBREGEX}\))?[ \t]*:[ \t]*{_ARG_DESCRIPTION_SUBREGEX}",
    re.MULTILINE,
)

_SPHINX_DOCSTRING_ARG_REGEX = re.compile(
    rf"^:param {_ARG_NAME_SUBREGEX}:[ \t]+{_ARG_DESCRIPTION_SUBREGEX}[ \t]*(?::type [^\s:]+:[ \t]+{_ARG_TYPE_SUBREGEX})?",
    re.MULTILINE,
)

_NUMPY_DOCSTRING_ARG_REGEX = re.compile(
    rf"^{_ARG_NAME_SUBREGEX}(?:[ \t]*:)?(?:[ \t]+{_ARG_TYPE_SUBREGEX})?[ \t]*\r?\n[ \t]+{_ARG_DESCRIPTION_SUBREGEX}",
    re.MULTILINE,
)


def _trim_text(text: str, max_chars: int) -> str:
    """Trims a string and adds an ellpsis if it exceeds the maximum length.

    Parameters
    ----------
    text: :class:`str`
        The string to trim.
    max_chars: :class:`int`
        The maximum number of characters to allow.

    Returns
    -------
    :class:`str`
        The trimmed string.
    """
    if len(text) > max_chars:
        # \u2026 = ellipsis
        return text[: max_chars - 1] + "\u2026"
    return text


def parse_docstring(func: Callable[..., Any], max_chars: int = MISSING) -> Dict[str, Any]:
    """Parses the docstring of a function into a dictionary.

    Parameters
    ----------
    func: :data:`~typing.Callable`
        The function to parse the docstring of.
    max_chars: :class:`int`
        The maximum number of characters to allow in the descriptions.
        If MISSING, then there is no maximum.

    Returns
    -------
    :class:`Dict[str, Any]`
        The parsed docstring including the function description and
        descriptions of arguments.
    """
    description = ""
    args = {}

    if docstring := inspect.cleandoc(inspect.getdoc(func) or "").strip():
        # Extract the function description
        description_match = _FUNCTION_DESCRIPTION_REGEX.search(docstring)
        if description_match:
            description = re.sub(r"\n\s*", " ", description_match.group(0)).strip()
        if max_chars is not MISSING:
            description = _trim_text(description, max_chars)

        # Extract the arguments
        # For Google-style, look only at the lines that are indented
        section_lines = inspect.cleandoc(
            "\n".join(line for line in docstring.splitlines() if line.startswith(("\t", "  ")))
        )
        docstring_styles = [
            _GOOGLE_DOCSTRING_ARG_REGEX.finditer(section_lines),
            _SPHINX_DOCSTRING_ARG_REGEX.finditer(docstring),
            _NUMPY_DOCSTRING_ARG_REGEX.finditer(docstring),
        ]

        # choose the style with the largest number of arguments matched
        matched_args = []
        actual_args = inspect.signature(func).parameters.keys()
        for matches in docstring_styles:
            style_matched_args = [match for match in matches if match.group("name") in actual_args]
            if len(style_matched_args) > len(matched_args):
                matched_args = style_matched_args

        for arg in matched_args:
            arg_description = re.sub(r"\n\s*", " ", arg.group("description")).strip()
            if max_chars is not MISSING:
                arg_description = _trim_text(arg_description, max_chars)
            args[arg.group("name")] = arg_description

    return {"description": description, "args": args}
