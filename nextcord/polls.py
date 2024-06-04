from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Union

from .enums import PollLayoutType, try_enum
from .errors import InvalidArgument
from .partial_emoji import PartialEmoji
from .user import User
from .utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .emoji import Emoji
    from .message import Message
    from .state import ConnectionState
    from .types.polls import (
        Poll as PollData,
        PollAnswer as PollAnswerPayload,
        PollAnswerCount as PollAnswerCountPayload,
        PollCreateRequest as PollCreateRequestPayload,
        PollMedia as PollMediaPayload,
        PollResults as PollResultsPayload,
    )

    # for reviewers: this typehint type is precedent in the nextcord codebase i.e.
    # https://github.com/nextcord/nextcord/blob/master/nextcord/message.py#L68
    EmojiInputType = Union[Emoji, PartialEmoji, str]


def resolve_emoji(emoji: EmojiInputType) -> str:
    if isinstance(emoji, Emoji):
        return str(emoji.id)

    if isinstance(emoji, PartialEmoji):
        # if this partial emoji has an ID, then it is a custom emoji. else it's an unicode emoji.
        return str(emoji.id) if emoji.id else emoji.name
    if isinstance(emoji, str):
        return emoji

    raise InvalidArgument(f"Cannot parse `{emoji}` into an emoji to send.")


class PollMedia:
    """
    A common object that backs both the question and answer.

    Attributes
    ----------
    text: Optional[:class:`str`]
        The text of the media.
    emoji: Optional[Union[:class:`PartialEmoji`, :class:`Emoji`]]
        The emoji of the media.

    """

    __slots__ = (
        "text",
        "emoji",
    )

    def __init__(self, text: str, emoji: Optional[EmojiInputType] = None) -> None:
        self.text: str = text
        self.emoji: Optional[PartialEmoji | Emoji] = emoji  # type: ignore[reportAttributeAccessIssue]
        if isinstance(emoji, str):
            self.emoji: Optional[PartialEmoji | Emoji] = PartialEmoji.from_str(emoji)

    def to_dict(self) -> PollMediaPayload:
        payload: PollMediaPayload = {"text": self.text}
        if self.emoji:
            payload["emoji"] = resolve_emoji(self.emoji)

        return payload

    @classmethod
    def from_dict(cls, data: PollMediaPayload) -> Self:
        # a PollMedia when sent will have emoji as a string.
        # however when received it will be a raw PartialEmoji.

        emoji = PartialEmoji.from_dict(data["emoji"]) if "emoji" in data else None  # type: ignore[reportArgumentType]

        return cls(text=data["text"], emoji=emoji)


class PollAnswer:
    """
    A choice to answer in a poll.

    Attributes
    ----------
    answer_id: Optional[:class:`str`]
        The answer ID of the answer.
    poll_media: Optional[:class:`PollMedia`]
        The poll media of the answer.
    """

    __slots__ = (
        "answer_id",
        "poll_media",
    )

    def __init__(self, *, answer_id: Optional[int] = None, poll_media: PollMedia) -> None:
        self.answer_id: Optional[int] = answer_id
        self.poll_media: PollMedia = poll_media

    def to_dict(self) -> PollAnswerPayload:
        payload: PollAnswerPayload = {"poll_media": self.poll_media.to_dict()}
        if self.answer_id:
            payload["answer_id"] = self.answer_id

        return payload

    @classmethod
    def from_dict(cls, data: PollAnswerPayload) -> Self:
        # data['answer_id'] is always sent as part of Discord's HTTP/Gateway
        return cls(answer_id=data["answer_id"], poll_media=PollMedia.from_dict(data["poll_media"]))  # type: ignore[reportTypedDictNotRequiredAccess]


class PollAnswerCount:
    """The answer count for a poll.
    Attributes
    ----------
    id: :class:`int`
        The ID of the answer in question.
    me_voted: :class:`int`
        Whether the bot has voted for this option.
    count: :class:`int`
        The number of users who have voted for this option.
    """

    __slots__ = ("id", "me_voted", "count")

    def __init__(self, data: PollAnswerCountPayload) -> None:
        self.id: int = data["id"]
        self.me_voted: bool = data["me_voted"]
        self.count: int = data["count"]

    def to_dict(self) -> PollAnswerCountPayload:
        payload: PollAnswerCountPayload = {
            "id": self.id,
            "me_voted": self.me_voted,
            "count": self.count,
        }
        return payload


class PollResults:
    """The result of the poll.
    This contains the numbers of vote for each answer.

    Attributes
    ----------
    is_finalized: :class:`bool`
        Whether the votes has been precisely counted.
    answer_counts: List[:class:`PollAnswerCount`]
        The counts for each answer
    """

    __slots__ = (
        "is_finalized",
        "answer_counts",
    )

    def __init__(self, data: PollResultsPayload) -> None:
        self.is_finalized: bool = data["is_finalized"]
        self.answer_counts: List[PollAnswerCount] = [
            PollAnswerCount(answer_count) for answer_count in data["answer_counts"]
        ]

    def to_dict(self) -> PollResultsPayload:
        payload: PollResultsPayload = {
            "is_finalized": self.is_finalized,
            "answer_counts": [answer_count.to_dict() for answer_count in self.answer_counts],
        }
        return payload


class PollCreateRequest:
    __slots__ = (
        "question",
        "answers",
        "duration",
        "allow_multiselect",
        "layout_type",
    )
    """
    A poll create request.
    You must use this to create a poll.

    Attributes
    ----------
    question: :class:`PollMedia`
        The question of the poll. Current only `text` is supported.

    """

    def __init__(
        self,
        question: PollMedia,
        answers: List[PollAnswer],
        duration: int,
        allow_multiselect: bool,
        layout_type: Optional[PollLayoutType] = MISSING,
    ) -> None:
        self.question: PollMedia = question
        self.answers: List[PollAnswer] = answers
        self.duration: int = duration
        self.allow_multiselect: bool = allow_multiselect
        self.layout_type: Optional[PollLayoutType] = layout_type

    def to_dict(self) -> PollCreateRequestPayload:
        payload: PollCreateRequestPayload = {
            "question": self.question.to_dict(),
            "answers": [answer.to_dict() for answer in self.answers],
            "duration": self.duration,
            "allow_multiselect": self.allow_multiselect,
        }
        if self.layout_type:
            payload["layout_type"] = self.layout_type.value
        return payload

    def add_answer(self, text: str, emoji: Optional[EmojiInputType] = None) -> Self:
        """Add a choice i.e. answer to the poll.
        This function returns the class instance to allow for fluent-style chaining.

        Parameters
        ----------
        text: :class:`str`
            The text description of the choice.
        emoji: Optional[Union[:class:`PartialEmoji`, :class:`Emoji`, :class:`str`]]
            The emoji description of the choice.

        Returns
        -------
        The poll create request object.
        """
        self.answers.append(PollAnswer(poll_media=PollMedia(text=text, emoji=emoji)))
        return self


class Poll:
    """A poll object.


    Attributes
    ----------
    message: :class:`Message`
        The message this poll belong to.
    question: :class:`PollMedia`
        The question being asked in a poll.
    answers: List[:class:`PollAnswer`]
        The answers of the poll.
    expiry: :class:`datetime.datetime`
        The expiry of the poll.
    allow_multiselect: :class:`bool`
        Whether this poll allow people to select more than 1 option.
    layout_type: :class:`PollLayoutType`
        The layout type of the poll.
    results: Optional[:class:`PollResults`]
        The results of the poll.
    """

    __slots__ = (
        "message",
        "question",
        "_state",
        "answers",
        "expiry",
        "allow_multiselect",
        "layout_type",
        "results",
    )

    def __eq__(self, other) -> bool:
        return self.message.id == other.message.id

    def __init__(self, data: PollData, *, message: Message, state: ConnectionState) -> None:
        self.message: Message = message
        self._state: ConnectionState = state
        self.question: PollMedia = PollMedia.from_dict(data["question"])
        self.answers: List[PollAnswer] = [
            PollAnswer.from_dict(poll_answer) for poll_answer in data["answers"]
        ]
        self.expiry: datetime = datetime.fromisoformat(data["expiry"])
        self.allow_multiselect: bool = data["allow_multiselect"]
        self.layout_type: PollLayoutType = try_enum(PollLayoutType, data["layout_type"])

        self.results: Optional[PollResults] = (
            PollResults(data["results"]) if "results" in data else None
        )

    # TODO: implement this endpoint when I understand how to create an AsyncIterator propperly

    async def get_answer_voters(self, answer_id: int) -> User:
        ...

    async def expire(self) -> None:
        """
        Immediately ends the poll. You cannot end polls from other users.
        """
        await self._state.http.end_poll(
            channel_id=self.message.channel.id, message_id=self.message.id
        )

    def to_dict(self) -> PollData:
        payload: PollData = {
            "question": self.question.to_dict(),
            "answers": [answer.to_dict() for answer in self.answers],
            "expiry": self.expiry.isoformat(),
            "allow_multiselect": self.allow_multiselect,
            "layout_type": self.layout_type.value,
        }
        if self.results:
            payload["results"] = self.results.to_dict()
        return payload
