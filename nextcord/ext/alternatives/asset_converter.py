"""An experiment that allows for conversion of ``Asset`` 
arguments for commands.

It first detects if there's an attachment available or a URL in the 
message content, it will return it as an ``Asset``. If not, 
it will default onto a "null" ``Asset`` (one with no URL).

Example:
```py
@commands.command()
async def test(ctx, image: Asset):
    asset_bytes = io.BytesIO()
    await image.save(asset_bytes)
    do_some_cool_image_manipulation(asset_bytes)

    await ctx.send(file=nextcord.File(asset_bytes, 'cool_image.png'))
```
"""

from nextcord.ext.commands import converter, Context, errors, Command
from inspect import Parameter
from nextcord import Asset, nextcordException
import typing

from ._common import _ALL

# Basic Asset Converter


class _AssetConverter(converter.Converter):
    async def convert(self, ctx: Context, argument: str):
        if argument.startswith("http"):
            return Asset(ctx.bot._connection, argument)

        raise errors.BadArgument("No image found!")


converter.AssetConverter = _AssetConverter

_ALL[Asset] = _AssetConverter

Asset.__str__ = (
    lambda s: "" if s._url is None else (s._url if s._url.startswith("http") else s.BASE + s._url)
)


async def _read(self):
    if not self._url:
        raise nextcordException("Invalid asset (no URL provided)")

    if self._state is None:
        raise nextcordException("Invalid state (no ConnectionState provided)")

    return await self._state.http.get_from_cdn(str(self))


Asset.read = _read

# "Hijack" transform to set default for Asset to preprocess possibility of attachment

_old_transform = Command.transform


def _transform(self, ctx, param):
    if param.annotation is Asset and param.default is param.empty:
        if ctx.message.attachments:
            default = Asset(ctx.bot._connection, ctx.message.attachments[0].url)
            param = Parameter(
                param.name,
                param.kind,
                default=default,
                annotation=typing.Optional[param.annotation],
            )
        else:
            default = Asset(ctx.bot._connection, "")
            param = Parameter(param.name, param.kind, default=default, annotation=param.annotation)

    return _old_transform(self, ctx, param)


Command.transform = _transform
