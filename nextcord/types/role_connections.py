# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Dict, Literal, TypedDict

from typing_extensions import NotRequired

ApplicationRoleConnectionMetadataType = Literal[1, 2, 3, 4, 5, 6, 7, 8]


class ApplicationRoleConnectionMetadata(TypedDict):
    type: ApplicationRoleConnectionMetadataType
    key: str
    name: str
    name_localizations: NotRequired[Dict[str, str]]
    description: str
    description_localizations: NotRequired[Dict[str, str]]
