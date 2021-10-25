import inspect
import itertools
from typing import (Any, AsyncIterator, Callable, List, NamedTuple, Optional,
                    Sequence, TypeVar, Union)

from .constants import PageFormatType, SendKwargsType
from .menus import Menu

DataType = TypeVar("DataType")


class PageSource:
    """An interface representing a menu page's data source for the actual menu page.

    Subclasses must implement the backing resource along with the following methods:

    - :meth:`get_page`
    - :meth:`is_paginating`
    - :meth:`format_page`
    """
    async def _prepare_once(self):
        try:
            # Don't feel like formatting hasattr with
            # the proper mangling
            # read this as follows:
            # if hasattr(self, '__prepare')
            # except that it works as you expect
            self.__prepare
        except AttributeError:
            await self.prepare()
            self.__prepare = True

    async def prepare(self):
        """|coro|

        A coroutine that is called after initialisation
        but before anything else to do some asynchronous set up
        as well as the one provided in ``__init__``.

        By default this does nothing.

        This coroutine will only be called once.
        """
        pass

    def is_paginating(self) -> bool:
        """An abstract method that notifies the :class:`MenuPagesBase` whether or not
        to start paginating. This signals whether to add reactions or not.

        Subclasses must implement this.

        Returns
        --------
        :class:`bool`
            Whether to trigger pagination.
        """
        raise NotImplementedError

    def get_max_pages(self) -> Optional[int]:
        """An optional abstract method that retrieves the maximum number of pages
        this page source has. Useful for UX purposes.

        The default implementation returns ``None``.

        Returns
        --------
        Optional[:class:`int`]
            The maximum number of pages required to properly
            paginate the elements, if given.
        """
        return None

    async def get_page(self, page_number: int) -> Any:
        """|coro|

        An abstract method that retrieves an object representing the object to format.

        Subclasses must implement this.

        .. note::

            The page_number is zero-indexed between [0, :meth:`get_max_pages`),
            if there is a maximum number of pages.

        Parameters
        -----------
        page_number: :class:`int`
            The page number to access.

        Returns
        ---------
        Any
            The object represented by that page.
            This is passed into :meth:`format_page`.
        """
        raise NotImplementedError

    async def format_page(self, menu: Menu, page: Any) -> PageFormatType:
        """|maybecoro|

        An abstract method to format the page.

        This method must return one of the following types.

        If this method returns a ``str`` then it is interpreted as returning
        the ``content`` keyword argument in :meth:`nextcord.Message.edit`
        and :meth:`nextcord.abc.Messageable.send`.

        If this method returns a :class:`nextcord.Embed` then it is interpreted
        as returning the ``embed`` keyword argument in :meth:`nextcord.Message.edit`
        and :meth:`nextcord.abc.Messageable.send`.

        If this method returns a ``dict`` then it is interpreted as the
        keyword-arguments that are used in both :meth:`nextcord.Message.edit`
        and :meth:`nextcord.abc.Messageable.send`. The two of interest are
        ``embed`` and ``content``.

        Parameters
        ------------
        menu: :class:`Menu`
            The menu that wants to format this page.
        page: Any
            The page returned by :meth:`PageSource.get_page`.

        Returns
        ---------
        Union[:class:`str`, :class:`nextcord.Embed`, :class:`dict`]
            See above.
        """
        raise NotImplementedError


class ListPageSource(PageSource):
    """A data source for a sequence of items.

    This page source does not handle any sort of formatting, leaving it up
    to the user. To do so, implement the :meth:`format_page` method.

    Attributes
    ------------
    entries: Sequence[Any]
        The sequence of items to paginate.
    per_page: :class:`int`
        How many elements are in a page.
    """

    def __init__(self, entries: Sequence[DataType], *, per_page: int):
        self.entries = entries
        self.per_page = per_page

        pages, left_over = divmod(len(entries), per_page)
        if left_over:
            pages += 1

        self._max_pages = pages

    def is_paginating(self) -> bool:
        """:class:`bool`: Whether pagination is required."""
        return len(self.entries) > self.per_page

    def get_max_pages(self) -> int:
        """:class:`int`: The maximum number of pages required to paginate this sequence."""
        return self._max_pages

    async def get_page(self, page_number: int) -> Union[DataType, List[DataType]]:
        """Returns either a single element of the sequence or
        a slice of the sequence.

        If :attr:`per_page` is set to ``1`` then this returns a single
        element. Otherwise it returns at most :attr:`per_page` elements.

        Returns
        ---------
        Union[Any, List[Any]]
            The data returned.
        """
        if self.per_page == 1:
            return self.entries[page_number]
        else:
            base = page_number * self.per_page
            return self.entries[base:base + self.per_page]


KeyType = TypeVar("KeyType")

KeyFuncType = Callable[[DataType], KeyType]


class _GroupByEntry(NamedTuple):
    key: KeyFuncType
    items: DataType


class GroupByPageSource(ListPageSource):
    """A data source for grouped by sequence of items.

    This inherits from :class:`ListPageSource`.

    This page source does not handle any sort of formatting, leaving it up
    to the user. To do so, implement the :meth:`format_page` method.

    Parameters
    ------------
    entries: Sequence[Any]
        The sequence of items to paginate and group.
    key: Callable[[Any], Any]
        A key function to do the grouping with.
    sort: :class:`bool`
        Whether to sort the sequence before grouping it.
        The elements are sorted according to the ``key`` function passed.
    per_page: :class:`int`
        How many elements to have per page of the group.
    """

    def __init__(self, entries: Sequence[DataType], *, key: KeyFuncType, per_page: int, sort: int = True):
        self.__entries = entries if not sort else sorted(entries, key=key)
        nested: List[_GroupByEntry] = []
        self.nested_per_page = per_page
        for key_i, group_i in itertools.groupby(self.__entries, key=key):
            group_i = list(group_i)
            if not group_i:
                continue
            size = len(group_i)

            # Chunk the nested pages
            nested.extend(
                _GroupByEntry(key=key_i, items=group_i[i:i+per_page])
                for i in range(0, size, per_page)
            )

        super().__init__(nested, per_page=1)

    async def get_page(self, page_number: int) -> DataType:
        return self.entries[page_number]

    async def format_page(self, menu: Menu, entry: _GroupByEntry) -> SendKwargsType:
        """An abstract method to format the page.

        This works similar to the :meth:`ListPageSource.format_page` except
        the return type of the ``entry`` parameter is documented.

        Parameters
        ------------
        menu: :class:`Menu`
            The menu that wants to format this page.
        entry
            A namedtuple with ``(key, items)`` representing the key of the
            group by function and a sequence of paginated items within that
            group.

        Returns
        ---------
        :class:`dict`
            A dictionary representing keyword-arguments to pass to
            the message related calls.
        """
        raise NotImplementedError


def _aiter(obj, *, _isasync=inspect.iscoroutinefunction):
    cls = obj.__class__
    try:
        async_iter = cls.__aiter__
    except AttributeError:
        raise TypeError(
            '{0.__name__!r} object is not an async iterable'.format(cls))

    async_iter = async_iter(obj)
    if _isasync(async_iter):
        raise TypeError(
            '{0.__name__!r} object is not an async iterable'.format(cls))
    return async_iter


class AsyncIteratorPageSource(PageSource):
    """A data source for data backed by an asynchronous iterator.

    This page source does not handle any sort of formatting, leaving it up
    to the user. To do so, implement the :meth:`format_page` method.

    Parameters
    ------------
    iterator: AsyncIterator[Any]
        The asynchronous iterator to paginate.
    per_page: :class:`int`
        How many elements to have per page.
    """

    def __init__(self, iterator: AsyncIterator[DataType], *, per_page: int):
        self.iterator = _aiter(iterator)
        self.per_page = per_page
        self._exhausted = False
        self._cache: List[DataType] = []

    async def _iterate(self, n: int):
        it = self.iterator
        cache = self._cache
        for _ in range(0, n):
            try:
                elem = await it.__anext__()
            except StopAsyncIteration:
                self._exhausted = True
                break
            else:
                cache.append(elem)

    async def prepare(self, *, _aiter=_aiter):
        # Iterate until we have at least a bit more single page
        await self._iterate(self.per_page + 1)

    def is_paginating(self) -> bool:
        """:class:`bool`: Whether pagination is required."""
        return len(self._cache) > self.per_page

    async def _get_single_page(self, page_number: int) -> DataType:
        if page_number < 0:
            raise IndexError('Negative page number.')

        if not self._exhausted and len(self._cache) <= page_number:
            await self._iterate((page_number + 1) - len(self._cache))
        return self._cache[page_number]

    async def _get_page_range(self, page_number: int) -> List[DataType]:
        if page_number < 0:
            raise IndexError('Negative page number.')

        base = page_number * self.per_page
        max_base = base + self.per_page
        if not self._exhausted and len(self._cache) <= max_base:
            await self._iterate((max_base + 1) - len(self._cache))

        entries = self._cache[base:max_base]
        if not entries and max_base > len(self._cache):
            raise IndexError('Went too far')
        return entries

    async def get_page(self, page_number: int) -> Union[DataType, List[DataType]]:
        """Returns either a single element of the sequence or
        a slice of the sequence.

        If :attr:`per_page` is set to ``1`` then this returns a single
        element. Otherwise it returns at most :attr:`per_page` elements.

        Returns
        ---------
        Union[Any, List[Any]]
            The data returned.
        """
        if self.per_page == 1:
            return await self._get_single_page(page_number)
        else:
            return await self._get_page_range(page_number)
