"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present tag-epic

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

from typing import List, Literal, TypedDict

class _EmbedFooterOptional(TypedDict, total=False):
    icon_url: str
    proxy_icon_url: str

class EmbedFooter(_EmbedFooterOptional):
    text: str

class _EmbedFieldOptional(TypedDict, total=False):
    inline: bool

class EmbedField(_EmbedFieldOptional):
    name: str
    value: str

class EmbedThumbnail(TypedDict, total=False):
    url: str
    proxy_url: str
    height: int
    width: int

class EmbedVideo(TypedDict, total=False):
    url: str
    proxy_url: str
    height: int
    width: int

class EmbedImage(TypedDict, total=False):
    url: str
    proxy_url: str
    height: int
    width: int

class EmbedProvider(TypedDict, total=False):
    name: str
    url: str

class EmbedAuthor(TypedDict, total=False):
    name: str
    url: str
    icon_url: str
    proxy_icon_url: str

EmbedType = Literal['rich', 'image', 'video', 'gifv', 'article', 'link']

class Embed(TypedDict, total=False):
    title: str
    type: EmbedType
    description: str
    url: str
    timestamp: str
    color: int
    footer: EmbedFooter
    image: EmbedImage
    thumbnail: EmbedThumbnail
    video: EmbedVideo
    provider: EmbedProvider
    author: EmbedAuthor
    fields: List[EmbedField]
