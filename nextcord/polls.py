# SPDX-License-Identifier: MIT

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, AsyncIterator, List, Optional, Union, cast

from .emoji import Emoji
from .enums import PollLayoutType, try_enum
from .errors import InvalidArgument
from .iterators import answer_voters_iterator
from .partial_emoji import PartialEmoji
from .types.emoji import PartialEmoji as PartialEmojiPayload
from .utils import MISSING, utcnow

if TYPE_CHECKING:
    from typing_extensions import Self

    from .abc import Snowflake
    from .member import Member
    from .message import Message
    from .state import ConnectionState
    from .types.polls import (
        DAPIPollAnswer as DAPIPollAnswerPayload,
        Poll as PollData,
        PollAnswer as PollAnswerPayload,
        PollAnswerCount as PollAnswerCountPayload,
        PollCreateRequest as PollCreateRequestPayload,
        PollMedia as PollMediaPayload,
        PollResults as PollResultsPayload,
    )
    from .user import User

    EmojiInputType = Union[Emoji, PartialEmoji, str]

__all__ = (
    "PollResults",
    "PollMedia",
    "Poll",
    "PollAnswerCount",
    "PollCreateRequest",
    "PollAnswer",
)


def resolve_emoji(emoji: Union[Emoji, PartialEmoji]) -> PartialEmojiPayload:
    if isinstance(emoji, Emoji):
        return cast(PartialEmojiPayload, emoji._to_partial().to_dict())

    if isinstance(emoji, PartialEmoji):
        return cast(PartialEmojiPayload, emoji.to_dict())

    raise InvalidArgument(f"Cannot parse `{emoji}` into an emoji to send.")


class PollMedia:
    """A common object that backs both the question and answer.

    .. versionadded:: 3.0

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
        self.emoji: Optional[PartialEmoji | Emoji]
        if isinstance(emoji, str):
            self.emoji = PartialEmoji.from_str(emoji)
        else:
            self.emoji = emoji

    def __repr__(self) -> str:
        return f"<PollMedia text={self.text} emoji={self.emoji}>"

    def to_dict(self) -> PollMediaPayload:
        payload: PollMediaPayload = {"text": self.text}
        if self.emoji:
            payload["emoji"] = resolve_emoji(self.emoji)

        return payload

    @classmethod
    def from_dict(cls, data: PollMediaPayload) -> Self:
        emoji = PartialEmoji.from_dict(data["emoji"]) if "emoji" in data else None

        return cls(text=data["text"], emoji=emoji)


class PollAnswer:
    """A choice to answer in a poll.

    .. versionadded:: 3.0

    Attributes
    ----------
    answer_id: Optional[:class:`int`]
        The answer ID of the answer.
    media: Optional[:class:`PollMedia`]
        The poll media of the answer.
    """

    __slots__ = (
        "answer_id",
        "media",
    )

    def __init__(self, *, answer_id: Optional[int] = None, poll_media: PollMedia) -> None:
        self.answer_id: Optional[int] = answer_id
        self.media: PollMedia = poll_media

    def __repr__(self) -> str:
        return f"<PollAnswer answer_id={self.answer_id!r} poll_media={self.media!r}>"

    def to_dict(self) -> PollAnswerPayload:
        payload: PollAnswerPayload = {"poll_media": self.media.to_dict()}
        return payload

    @classmethod
    def from_dict(cls, data: DAPIPollAnswerPayload) -> Self:
        return cls(answer_id=data["answer_id"], poll_media=PollMedia.from_dict(data["poll_media"]))


class PollAnswerCount:
    """The answer count for an answer in a poll.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the answer in question.
    me_voted: :class:`bool`
        Whether the bot has voted for this option.
    count: :class:`int`
        The number of users who have voted for this option.
    poll: :class:`Poll`
        The poll this answer count object represents.
    """

    __slots__ = ("id", "me_voted", "count", "poll")

    def __init__(self, data: PollAnswerCountPayload, poll: Poll) -> None:
        self.poll: Poll = poll
        self.id: int = data["id"]
        self.me_voted: bool = data["me_voted"]
        self.count: int = data["count"]

    def __repr__(self) -> str:
        return (
            "<PollAnswerCount "
            f"id={self.id!r} "
            f"me_voted={self.me_voted!r} "
            f"count={self.count!r} "
            ">"
        )

    def voters(
        self, *, limit: Optional[int] = None, after: Optional[Snowflake] = None
    ) -> AsyncIterator[Union[User, Member]]:
        """|asynciter|

        Returns an async iterator representing the users who have voted for this option.

        The ``after`` parameter must represent an user
        and meet the :class:`abc.Snowflake` abc.

        Examples
        --------
        Usage ::

            # I do not actually recommend doing this.

            async for voter in count.voters():
                await channel.send(f"{voter} has voted with choice number {count.id}!")

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The maximum number of results to return.
            If not provided, return all users who voted for the choice.
        after: Optional[:class:`abc.Snowflake`]
            For pagination, votes are sorted by member.
        """
        if limit is None:
            limit = self.count

        return answer_voters_iterator(
            self.poll.message, answer_id=self.id, limit=limit, after=after
        )

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

    .. versionadded:: 3.0

    Attributes
    ----------
    is_finalized: :class:`bool`
        Whether the votes has been precisely counted.
    answer_counts: List[:class:`PollAnswerCount`]
        The counts for each answer.
    poll: :class:`Poll`
        The poll associated with this result.
    """

    __slots__ = (
        "is_finalized",
        "answer_counts",
        "poll",
    )

    def __init__(self, data: PollResultsPayload, poll: Poll) -> None:
        self.is_finalized: bool = data["is_finalized"]
        self.answer_counts: List[PollAnswerCount] = [
            PollAnswerCount(answer_count, poll) for answer_count in data["answer_counts"]
        ]
        self.poll: Poll = poll

    def __repr__(self) -> str:
        return (
            "<PollResults "
            f"is_finalized={self.is_finalized!r} "
            f"answer_counts={self.answer_counts!r} "
            ">"
        )

    def to_dict(self) -> PollResultsPayload:
        payload: PollResultsPayload = {
            "is_finalized": self.is_finalized,
            "answer_counts": [answer_count.to_dict() for answer_count in self.answer_counts],
        }
        return payload


class PollCreateRequest:
    """A poll create request.

    You must use this to create a poll.

    .. versionadded:: 3.0

    Attributes
    ----------
    question: Union[:class:`str`, :class:`PollMedia`]
        The question of the poll. Currently only `text` is supported.
        If a :class:`str` was passed, it automatically converts to a :class:`PollMedia`.
    duration: Optional[:class:`int`]
        The number of hours this poll should be open for. Defaults to ``24``. Max ``768`` (32 days).
    allow_multiselect: Optional[:class:`bool`]
        Whether voters can select more than one choice. Defaults to False.
    answers: Optional[List[:class:`PollAnswer`]]
        The answers to the poll.
        If omitted, answers must be added later with :func:`PollCreateRequest.add_answer`.
    layout_type: Optional[:class:`PollLayoutType`]
        The layout type of the poll. Defaults to :attr:`PollLayoutType.default`
    """

    __slots__ = (
        "question",
        "answers",
        "duration",
        "allow_multiselect",
        "layout_type",
    )

    def __init__(
        self,
        question: Union[str, PollMedia],
        duration: int = 24,
        allow_multiselect: bool = False,
        layout_type: Optional[PollLayoutType] = MISSING,
        answers: Optional[List[PollAnswer]] = None,
    ) -> None:
        self.question: PollMedia = (
            question if isinstance(question, PollMedia) else PollMedia(text=question)
        )
        self.answers: List[PollAnswer] = answers or []
        self.duration: int = duration
        self.allow_multiselect: bool = allow_multiselect
        self.layout_type: Optional[PollLayoutType] = layout_type

    def __repr__(self) -> str:
        return (
            "<PollCreateRequest "
            f"question={self.question!r} "
            f"answers={self.answers!r} "
            f"duration={self.duration!r} "
            f"allow_multiselect={self.allow_multiselect!r} "
            f"layout_type={self.layout_type!r} "
            ">"
        )

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
        """
        self.answers.append(PollAnswer(poll_media=PollMedia(text=text, emoji=emoji)))
        return self


class Poll:
    """A poll object.

    .. versionadded:: 3.0

    Attributes
    ----------
    message: :class:`Message`
        The message this poll belongs to.
    question: :class:`PollMedia`
        The question being asked in this poll.
    answers: List[:class:`PollAnswer`]
        The answers for this poll.
    expiry: :class:`datetime.datetime`
        The expiry of this poll.
    allow_multiselect: :class:`bool`
        Whether this poll allows users to select more than one option.
    layout_type: :class:`PollLayoutType`
        The layout type of this poll.
    results: Optional[:class:`PollResults`]
        The results of this poll.
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
            PollResults(data["results"], self) if "results" in data else None
        )

    def __repr__(self) -> str:
        return (
            "<Poll "
            f"message={self.message!r} "
            f"question={self.question!r} "
            f"answers={self.answers!r} "
            f"expired={self.expired!r}"
            ">"
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and other.message.id == self.message.id

    async def expire(self) -> Message:
        """
        Immediately ends the poll. You cannot end polls from other users.

        Returns
        -------
        :class:`Message`
            The new updated message.
        """
        # circular imports
        from .message import Message

        message = await self._state.http.end_poll(
            channel_id=self.message.channel.id, message_id=self.message.id
        )
        return Message(state=self._state, channel=self.message.channel, data=message)

    @property
    def expired(self) -> bool:
        """:class:`bool`: Returns True if this poll has been closed."""
        return self.expiry < utcnow()
