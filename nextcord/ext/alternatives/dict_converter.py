"""An experiment that allows you to use a dict converter using **kwarg
notation.

.. note::
    This uses key, value pairs for construction

Specificy key and value types can be set using typing.Dict[key_type, value_type],
this defaults to Dict[str, str] the builtin dict type can also be used (that will default
to [str, str] aswell).

Example:
```py
import typing

@bot.command()
async def ban(ctx, **users_reasons_mapping: typing.Dict[nextcord.Member, str]):
    for (member, reason) in users_reasons_mapping['users_reasons_mapping'].items():  # this is necessary unfortunately
        await member.ban(reason=reason)
    await ctx.send(f'Banned {len(users_reasons_mapping["users_reasons_mapping"])} members')
```
"""

import inspect
from typing import Dict

import nextcord
from nextcord.ext.commands import Command, TooManyArguments, view as _view


class DictStringView(_view.StringView):
    def get_quoted_word(self):
        current = self.current
        if current is None:
            return None

        close_quote = _view._quotes.get(current)
        is_quoted = bool(close_quote)
        if is_quoted:
            result = []
            _escaped_quotes = (current, close_quote)
        else:
            result = [current]
            _escaped_quotes = _view._all_quotes

        while not self.eof:
            current = self.get()
            if not current:
                if is_quoted:
                    # unexpected EOF
                    raise _view.ExpectedClosingQuoteError(close_quote)
                return "".join(result)

            # currently we accept strings in the format of "hello world"
            # to embed a quote inside the string you must escape it: "a \"world\""
            if current == "\\":
                next_char = self.get()
                if not next_char:
                    # string ends with \ and no character after it
                    if is_quoted:
                        # if we're quoted then we're expecting a closing quote
                        raise _view.ExpectedClosingQuoteError(close_quote)
                    # if we aren't then we just let it through
                    return "".join(result)

                if next_char in _escaped_quotes:
                    # escaped quote
                    result.append(next_char)
                else:
                    # different escape character, ignore it
                    self.undo()
                    result.append(current)
                continue

            if not is_quoted and current in _view._all_quotes:
                # we aren't quoted
                try:
                    return self.get_quoted_word()
                except _view.UnexpectedQuoteError:
                    raise

            # closing quote
            if is_quoted and current == close_quote:
                next_char = self.get()
                # all this for that
                valid_eof = not next_char or next_char.isspace() or next_char == "="
                if not valid_eof:
                    raise _view.InvalidEndOfQuotedStringError(next_char)

                # we're quoted so it's okay
                return "".join(result)

            if current.isspace() and not is_quoted:
                # end of word found
                return "".join(result)

            result.append(current)


async def _parse_arguments(self, ctx):
    ctx.args = [ctx] if self.cog is None else [self.cog, ctx]
    ctx.kwargs = {}
    args = ctx.args
    kwargs = ctx.kwargs

    view = ctx.view
    iterator = iter(self.params.items())

    if self.cog is not None:
        # we have 'self' as the first parameter so just advance
        # the iterator and resume parsing
        try:
            next(iterator)
        except StopIteration:
            fmt = 'Callback for {0.name} command is missing "self" parameter.'
            raise nextcord.ClientException(fmt.format(self))

    # next we have the 'ctx' as the next parameter
    try:
        next(iterator)
    except StopIteration:
        fmt = 'Callback for {0.name} command is missing "ctx" parameter.'
        raise nextcord.ClientException(fmt.format(self))

    for name, param in iterator:
        if param.kind == param.POSITIONAL_OR_KEYWORD:
            transformed = await self.transform(ctx, param)
            args.append(transformed)
        elif param.kind == param.KEYWORD_ONLY:
            # kwarg only param denotes "consume rest" semantics
            if self.rest_is_raw:
                converter = self._get_converter(param)
                argument = view.read_rest()
                kwargs[name] = await self.do_conversion(ctx, converter, argument, param)
            else:
                kwargs[name] = await self.transform(ctx, param)
            break
        elif param.kind == param.VAR_POSITIONAL:
            while not view.eof:
                try:
                    transformed = await self.transform(ctx, param)
                    args.append(transformed)
                except RuntimeError:
                    break
        elif param.kind == param.VAR_KEYWORD:
            # we have received **kwargs
            annotation = param.annotation
            if annotation == param.empty or annotation is dict:
                annotation = Dict[str, str]  # default to {str: str}

            key_converter = annotation.__args__[0]
            value_converter = annotation.__args__[1]
            argument = view.read_rest()
            view = DictStringView(argument)
            kv_list = []

            while 1:
                kv = view.get_quoted_word()
                if kv is None:
                    break
                else:
                    kv_list.append(kv.strip())
            kv_pairs = []
            for current in kv_list:
                if current[0] == "=":
                    kv_pairs.remove([previous])
                    kv_pairs.append([previous, current[1:]])
                else:
                    kv_pairs.append(current.split("="))
                previous = current
            kwargs[name] = {
                await self.do_conversion(ctx, key_converter, key, param): await self.do_conversion(
                    ctx, value_converter, value, param
                )
                for (key, value) in kv_pairs
            }
            break

    if not self.ignore_extra:
        if not view.eof:
            raise TooManyArguments("Too many arguments passed to " + self.qualified_name)


Command._parse_arguments = _parse_arguments
