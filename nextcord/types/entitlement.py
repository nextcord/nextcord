from typing import Literal, TypedDict

from typing_extensions import NotRequired

from .snowflake import Snowflake


EntitlementType = Literal[8]


class Entitlement(TypedDict):
    id: Snowflake
    sku_id: Snowflake
    application_id: Snowflake
    user_id: NotRequired[Snowflake]
    type: EntitlementType
    deleted: bool
    starts_at: NotRequired[str]
    ends_at: NotRequired[str]
    guild_id: NotRequired[Snowflake]


SKUType = Literal[5, 6]


class SKU(TypedDict):
    id: Snowflake
    type: SKUType
    application_id: Snowflake
    name: str
    slug: str
    flags: int
