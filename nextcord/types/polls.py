# SPDX-License-Identifier: MIT

from typing import List, Literal, Optional, TypedDict

from typing_extensions import NotRequired

from .emoji import PartialEmoji

LayoutType = Literal[1]


class PollMedia(TypedDict):
    text: str
    emoji: NotRequired[PartialEmoji]


class PollAnswer(TypedDict):
    poll_media: PollMedia


class DAPIPollAnswer(TypedDict):
    answer_id: int
    poll_media: PollMedia


class PollCreateRequest(TypedDict):
    question: PollMedia
    answers: List[PollAnswer]
    duration: int
    allow_multiselect: bool
    layout_type: NotRequired[LayoutType]


class PollAnswerCount(TypedDict):
    id: int
    count: int
    me_voted: bool


class PollResults(TypedDict):
    is_finalized: bool
    answer_counts: List[PollAnswerCount]


class Poll(TypedDict):
    question: PollMedia
    answers: List[DAPIPollAnswer]
    expiry: Optional[str]
    allow_multiselect: bool
    layout_type: LayoutType
    results: NotRequired[PollResults]
