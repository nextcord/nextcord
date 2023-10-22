from datetime import datetime
from typing import Optional

from enums import EntitlementType, SKUType
from flags import SKUFlags
from object import Object
from utils import parse_time
from types.entitlement import (
    Entitlement as EntitlementPayload,
    SKU as SKUPayload
)


class Entitlement(Object):
    """Represents a Discord premium entitlement. This class should not be initialized manually.
    
    Attributes
    ----------
    id: :class:`int`
        The ID of this entitlement.
    SKU_id: :class:`int`
        The ID of the SKU this entitlement is for.
    application_id: :class:`int`
        The ID of the application this entitlement is for.
    user_id: Optional[:class:`int`]
        The ID of the user this entitlement is for.
    type: :class:`EntitlementType`
        The type of this entitlement.
    deleted: :class:`bool`
        Whether this entitlement has been deleted.
    starts_at: Optional[:class:`datetime.datetime`]
        When this entitlement starts.
    ends_at: Optional[:class:`datetime.datetime`]
        When this entitlement ends.
    guild_id: Optional[:class:`int`]
        The ID of the guild this entitlement is for.

    .. versionadded:: 3.0
    """

    __slots__ = (
        "id",
        "sku_id",
        "application_id",
        "user_id",
        "type",
        "deleted",
        "starts_at",
        "ends_at",
        "guild_id",
    )

    def __init__(self, payload: EntitlementPayload) -> None:
        self.id: int = int(payload["id"])
        self.sku_id: int = int(payload["sku_id"])
        self.application_id: int = int(payload["application_id"])
        self.user_id: Optional[int] = int(payload.get("user_id") or 0) or None
        self.type: EntitlementType = EntitlementType(payload["type"])
        self.deleted: bool = payload["deleted"]
        self.starts_at: Optional[datetime] = parse_time(payload.get("starts_at"))
        self.ends_at: Optional[datetime] = parse_time(payload.get("ends_at"))
        self.guild_id: Optional[int] = int(payload.get("guild_id") or 0) or None

    def __repr__(self) -> str:
        return f"<Entitlement id={self.id!r} sku_id={self.sku_id!r} application_id={self.application_id!r} user_id={self.user_id!r} guild_id={self.guild_id!r}"


class SKU(Object):
    """Represents a Discord premium SKU. This class should not be initialized manually.
    
    Attributes
    ----------
    id: :class:`int`
        The ID of this SKU.
    type: :class:`SKUType`
        The type of this SKU.
    application_id: :class:`int`
        The ID of the application this SKU is for.
    name: :class:`str`
        The name of this SKU.
    slug: :class:`str`
        The slug of this SKU.
    flags: :class:`.SKUFlags`
        The flags of this SKU.

    .. versionadded:: 3.0
    """

    __slots__ = ("id", "type", "application_id", "name", "slug", "flags")

    def __init__(self, payload: SKUPayload) -> None:
        self.id: int = int(payload["id"])
        self.type: SKUType = SKUType(payload["type"])
        self.application_id: int = int(payload["application_id"])
        self.name: str = payload["name"]
        self.slug: str = payload["slug"]
        self.flags: SKUFlags = SKUFlags._from_value(payload["flags"])

    def __repr__(self) -> str:
        return f"<SKU id={self.id!r} type={self.type!r} application_id={self.application_id!r} slug={self.slug!r}"
    