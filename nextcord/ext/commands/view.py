# SPDX-License-Identifier: MIT

from typing import Optional, Tuple, Type, overload

from typing_extensions import Self

import nextcord

from .errors import ExpectedClosingQuoteError, InvalidEndOfQuotedStringError, UnexpectedQuoteError

__all__ = (
    "Separator",
    "Quotation",
)


class Separator:
    """An argument delimiter.

    Attributes
    ----------
    value: Optional[:class:`str`]
        The value for the argument delimiter. By default, this is a space.
    strip_ws: bool
        Whether to strip surrounding whitespace
    """

    __slots__ = ("value", "strip_ws")

    def __init__(self, value: Optional[str] = None, *, strip_ws: bool = True) -> None:
        if value == "":
            raise ValueError("Separators must be a non-empty string or None.")

        self.value: str = value or " "
        self.strip_ws: bool = strip_ws

    def validate(self, character: str) -> bool:
        """Validates a given character against a separator.

        If the separator is any whitespace, then the character is checked to be whitespace
        via :func:`str.isspace`.

        Parameters
        ----------
        character: :class:`str`
            The character to check this separator against.
        """
        if self.value.isspace():
            return character.isspace()

        return self.value == character

    def __repr__(self) -> str:
        return f"<Separator value={self.value!r} strip_ws={self.strip_ws}>"


class Quotation:
    """Delimiters for a quoted argument.

    Parameters
    ----------
    start: :class:`str`
        The character that starts a quotation.
    end: Optional[:class:`str`]
        The character that ends a quotation. By default, this is set to the start.
    """

    __slots__ = ("_values", "_is_default", "_cs_all_values", "_cs_initial_quotations")

    @overload
    def __init__(self, start: str, /) -> None:
        ...

    @overload
    def __init__(self, start: str, end: str, /) -> None:
        ...

    def __init__(self, start: str, end: Optional[str] = None) -> None:
        if start == "" or end == "":
            raise ValueError("Quotations must be an non-empty string.")

        self._values: dict[str, str] = {start: end or start}
        self._is_default: bool = False

    @classmethod
    def from_pairs(cls: Type[Self], *pairs: Tuple[str, str]) -> Self:
        """Creates a quotation from a pair from quotations.

        Example
        -------

        .. code-block:: python3

            @bot.command(quotation=Quotation.from_pairs(("'", "'"), ('"', '"'), (">", "<")))
            async def foo(ctx, *c):
                await ctx.send(",".join(c))

        """
        if not pairs:
            raise ValueError("Pairs must be provided.")

        pair = pairs[0]
        pairs = pairs[1:]

        self = cls(pair[0], pair[1])
        for start, end in pairs:
            if start == "" or end == "":
                raise ValueError("Quotations must be an non-empty string.")

            self._values[start] = end

        return self

    @classmethod
    def defaults(cls: Type[Self]) -> Self:
        """Creates a quotation from the default recognized pair of quotations.

        The following are the defaults:
            * ``''``
            * ``""``
            * ``‘‘``
            * ``‚‛``
            * ``“”``
            * ``„‟``
            * ``⹂⹂``
            * ``「」``
            * ``『』``
            * ``〝〞``
            * ``﹁﹂``
            * ``﹃﹄``
            * ``＂＂``
            * ``｢｣``
            * ``«»``
            * ``‹›``
            * ``《》``
            * ``〈〉``
        """
        pairs = [
            ("'", "'"),
            ('"', '"'),
            ("‘", "’"),
            ("‚", "‛"),
            ("“", "”"),
            ("„", "‟"),
            ("⹂", "⹂"),
            ("「", "」"),
            ("『", "』"),
            ("〝", "〞"),
            ("﹁", "﹂"),
            ("﹃", "﹄"),
            ("＂", "＂"),
            ("｢", "｣"),
            ("«", "»"),
            ("‹", "›"),
            ("《", "》"),
            ("〈", "〉"),
        ]

        self = cls.from_pairs(*pairs)
        self._is_default = True
        return self

    @nextcord.utils.cached_slot_property("_cs_all_values")
    def all_values(self):
        """Set[:class:`str`] All of the possible values for a quotation."""
        return set(self._values.keys()) | set(self._values.values())

    @nextcord.utils.cached_slot_property("_cs_initial_quotations")
    def initial_quotations(self):
        """Tuple[:class:`str`\, :class:`str`] The first quotation mapping provided."""
        return tuple(self._values.items())[0]

    @property
    def is_default(self):
        ":class:`bool` Whether this quotation contains the default values."
        return self._is_default

    def get(self, key: str) -> Optional[str]:
        return self._values.get(key)

    def __contains__(self, item: str) -> bool:
        return item in self._values

    def __repr__(self) -> str:
        return f"<Quotation values={self.all_values!r}>"


class StringView:
    def __init__(self, buffer) -> None:
        self.index = 0
        self.buffer = buffer
        self.end = len(buffer)
        self.previous = 0
        self.separator: Separator = Separator()
        self.quotation: Quotation = Quotation.defaults()

    @property
    def current(self):
        return None if self.eof else self.buffer[self.index]

    @property
    def eof(self):
        return self.index >= self.end

    def undo(self) -> None:
        self.index = self.previous

    def skip_ws(self):
        pos = 0
        while not self.eof:
            try:
                current = self.buffer[self.index + pos]
                if not self.separator.validate(current) and not current.isspace():
                    break
                pos += 1
            except IndexError:
                break

        self.previous = self.index
        self.index += pos
        return self.previous != self.index

    def skip_string(self, string) -> bool:
        strlen = len(string)
        if self.buffer[self.index : self.index + strlen] == string:
            self.previous = self.index
            self.index += strlen
            return True
        return False

    def read_rest(self):
        result = self.buffer[self.index :]
        self.previous = self.index
        self.index = self.end
        return result

    def read(self, n):
        result = self.buffer[self.index : self.index + n]
        self.previous = self.index
        self.index += n
        return result

    def get(self):
        try:
            result = self.buffer[self.index + 1]
        except IndexError:
            result = None

        self.previous = self.index
        self.index += 1
        return result

    def get_word(self):
        pos = 0
        while not self.eof:
            try:
                current = self.buffer[self.index + pos]
                if self.separator.validate(current):
                    break
                pos += 1
            except IndexError:
                break
        self.previous = self.index
        result = self.buffer[self.index : self.index + pos]
        self.index += pos
        return result

    def get_quoted_word(self):
        current = self.current
        if current is None:
            return None

        close_quote = self.quotation.get(current)

        is_quoted = bool(close_quote)
        if is_quoted:
            result = []
            _escaped_quotes = (current, close_quote)
        else:
            result = [current]
            # TODO: should this include globally recognized quotes or only the custom ones?
            _escaped_quotes = self.quotation.all_values

        while not self.eof:
            current = self.get()
            if not current:
                if is_quoted:
                    # unexpected EOF
                    raise ExpectedClosingQuoteError(close_quote)

                r = "".join(result)
                if self.separator.strip_ws:
                    r = r.strip()

                return r

            # currently we accept strings in the format of "hello world"
            # to embed a quote inside the string you must escape it: "a \"world\""
            if current == "\\":
                next_char = self.get()
                if not next_char:
                    # string ends with \ and no character after it
                    if is_quoted:
                        # if we're quoted then we're expecting a closing quote
                        raise ExpectedClosingQuoteError(close_quote)
                    # if we aren't then we just let it through
                    return "".join(result)

                if next_char in _escaped_quotes or self.separator.validate(next_char):
                    # escaped quote or separator
                    result.append(next_char)
                else:
                    # different escape character, ignore it
                    self.undo()
                    result.append(current)
                continue

            if not is_quoted and current in self.quotation:
                # we aren't quoted
                raise UnexpectedQuoteError(current)

            # closing quote
            if is_quoted and current == close_quote:
                next_char = self.get()
                valid_eof = not next_char or self.separator.validate(next_char)
                if not valid_eof:
                    raise InvalidEndOfQuotedStringError(next_char or "")

                # we're quoted so it's okay
                return "".join(result)

            if self.separator.validate(current) and not is_quoted:
                # end of word found
                r = "".join(result)
                if self.separator.strip_ws:
                    r = r.strip()

                return r

            result.append(current)

    def __repr__(self) -> str:
        return (
            f"<StringView pos: {self.index} prev: {self.previous} end: {self.end} eof: {self.eof}>"
        )
