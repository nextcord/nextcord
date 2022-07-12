"""
The MIT License (MIT)

Copyright (c) 2022-present tag-epic

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from .enums import KeywordPresetType, try_enum

if TYPE_CHECKING:
    from .types.auto_moderation import (
        AutoModerationTriggerMetadata as AutoModerationTriggerMetadataPayload,
    )

__all__ = ("AutoModerationTriggerMetadata",)


class AutoModerationTriggerMetadata:
    """Represents data about an auto moderation trigger rule.

    .. versionadded:: 2.1

    Attributes
    ----------
    keyword_filter: List[:class:`str`]
        A list of substrings which will be searched for in content.
    presets: List[:class:`KeywordPresetType`]
        A list of Discord pre-defined wordsets which will be searched for in content.
    """

    def __init__(self, data: AutoModerationTriggerMetadataPayload) -> None:
        self.keyword_filter: List[str] = data["keyword_filter"]
        self.presets: List[KeywordPresetType] = [
            try_enum(KeywordPresetType, preset) for preset in data["presets"]
        ]
