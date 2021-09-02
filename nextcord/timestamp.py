from dataclasses import dataclass
from datetime import datetime as dt


@dataclass
class Timestamp:
    time: int

    @property
    def datetime(self) -> dt:
        """The datetime object of the timestamp."""

        return dt.fromtimestamp(self.time)

    @property
    def short_time(self) -> str:
        """The timestamp in short time format."""

        return f"<t:{self.time}:t>"

    @property
    def long_time(self) -> str:
        """The timestamp in long time format."""

        return f"<t:{self.time}:T>"

    @property
    def short_date(self) -> str:
        """The timestamp in short date format."""

        return f"<t:{self.time}:d>"

    @property
    def long_date(self) -> str:
        """The timestamp in long date format."""

        return f"<t:{self.time}:D>"

    @property
    def short_date_time(self) -> str:
        """The timestamp in short date/time format."""

        return f"<t:{self.time}:f>"

    @property
    def long_date_time(self) -> str:
        """The timestamp in long date/time format."""

        return f"<t:{self.time}:F>"

    @property
    def relative_time(self) -> str:
        """The timestamp in relative time format."""

        return f"<t:{self.time}:R>"

    @classmethod
    def from_datetime(cls, datetime: dt) -> "Timestamp":
        """Generate a timestamp from a datetime object."""

        return cls(round(datetime.timestamp()))

    @classmethod
    def utcnow(cls) -> "Timestamp":
        """Generate a timestamp from the current UNIX time."""

        return cls(round(dt.utcnow().timestamp()))

    def __repr__(self) -> str:
        return f"<Timestamp time={self.time}>"
