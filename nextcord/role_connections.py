# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Dict, Optional

from typing_extensions import Self

from .enums import RoleConnectionMetadataType, try_enum
from .types.role_connections import (
    ApplicationRoleConnectionMetadata as RoleConnectionMetadataPayload,
)

__all__ = ("RoleConnectionMetadata",)


class RoleConnectionMetadata:
    """Represents a role connection metadata object.

    .. versionadded:: 2.4

    Attributes
    ----------
    type: :class:`RoleConnectionMetadataType`
        The type of metadata value.
    key: :class:`str`
        The dictionary key for the metadata field.
    name: :class:`str`
        The name of the metadata field.
    name_localizations: Optional[:class:`dict`]
        The translations of the name.
    description: :class:`str`
        The description of the metadata field.
    description_localizations: Optional[:class:`dict`]
        The translations of the description.
    """

    __slots__ = (
        "type",
        "key",
        "name",
        "name_localizations",
        "description",
        "description_localizations",
    )

    def __init__(
        self,
        *,
        type: RoleConnectionMetadataType,
        key: str,
        name: str,
        name_localizations: Optional[Dict[str, str]],
        description: str,
        description_localizations: Optional[Dict[str, str]],
    ) -> None:
        self.type: RoleConnectionMetadataType = type
        self.key: str = key
        self.name: str = name
        self.name_localizations: Optional[Dict[str, str]] = name_localizations
        self.description: str = description
        self.description_localizations: Optional[Dict[str, str]] = description_localizations

    @classmethod
    def from_data(cls, data: RoleConnectionMetadataPayload) -> Self:
        return cls(
            type=try_enum(RoleConnectionMetadataType, data["type"]),
            key=data["key"],
            name=data["name"],
            name_localizations=data.get("name_localizations"),
            description=data["description"],
            description_localizations=data.get("description_localizations"),
        )

    def __repr__(self) -> str:
        attrs = (
            ("type", self.type),
            ("key", self.key),
            ("name", self.name),
            ("name_localizations", self.name_localizations),
            ("description", self.description),
            ("description_localizations", self.description_localizations),
        )
        resolved = " ".join(f"{name}={value!r}" for name, value in attrs)
        return f"{type(self).__name__} {resolved}"
