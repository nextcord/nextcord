# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List, Literal, TypedDict, Union

from typing_extensions import NotRequired

from .snowflake import Snowflake
from .user import User

StickerFormatType = Literal[1, 2, 3]


class StickerItem(TypedDict):
    id: Snowflake
    name: str
    format_type: StickerFormatType


class BaseSticker(TypedDict):
    id: Snowflake
    name: str
    description: str
    tags: str
    format_type: StickerFormatType


class StandardSticker(BaseSticker):
    type: Literal[1]
    sort_value: int
    pack_id: Snowflake


class GuildSticker(BaseSticker):
    type: Literal[2]
    available: bool
    guild_id: Snowflake
    user: NotRequired[User]


Sticker = Union[BaseSticker, StandardSticker, GuildSticker]


class StickerPack(TypedDict):
    id: Snowflake
    stickers: List[StandardSticker]
    name: str
    sku_id: Snowflake
    cover_sticker_id: Snowflake
    description: str
    banner_asset_id: Snowflake


class CreateGuildSticker(TypedDict):
    name: str
    tags: str
    description: NotRequired[str]


class EditGuildSticker(TypedDict, total=False):
    name: str
    tags: str
    description: str


class ListPremiumStickerPacks(TypedDict):
    sticker_packs: List[StickerPack]
