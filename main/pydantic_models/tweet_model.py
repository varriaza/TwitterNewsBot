from datetime import datetime
from typing import Dict, Any
from uuid import uuid4
from sqlmodel import SQLModel, Field


class Tweet(SQLModel, table=True):
    tweet_id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    username: str
    url: str | None = None
    created_at: datetime
    text: str
    # TODO: Add allowed values check?
    tweet_type: str = "regular"
    linked_tweet_id: str | None = None
    retweet_count: int = 0
    reply_count: int = 0
    like_count: int = 0
    quote_count: int = 0
    view_count: int = 0
    bookmark_count: int = 0

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> "Tweet":
        """Create a Tweet object from a database row dictionary"""
        return cls(
            tweet_id=row["tweet_id"],
            username=row["username"],
            url=row["url"],
            created_at=row["created_at"],
            text=row["text"],
            tweet_type=row["tweet_type"],
            linked_tweet_id=row["linked_tweet_id"],
            retweet_count=row["retweet_count"],
            reply_count=row["reply_count"],
            like_count=row["like_count"],
            quote_count=row["quote_count"],
            view_count=row["view_count"],
            bookmark_count=row["bookmark_count"],
        )

    @classmethod
    def from_data(
        cls, username: str, created_at: datetime, text: str, **kwargs
    ) -> "Tweet":
        """Create a Tweet object from individual data fields with sensible defaults for optional fields"""
        import uuid

        # Set default tweet_id if not provided
        if "tweet_id" not in kwargs:
            kwargs["tweet_id"] = str(uuid.uuid4())

        return cls(username=username, created_at=created_at, text=text, **kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Tweet object to a dictionary"""
        return {
            "tweet_id": self.tweet_id,
            "username": self.username,
            "url": self.url,
            "created_at": self.created_at,
            "text": self.text,
            "tweet_type": self.tweet_type,
            "linked_tweet_id": self.linked_tweet_id,
            "retweet_count": self.retweet_count,
            "reply_count": self.reply_count,
            "like_count": self.like_count,
            "quote_count": self.quote_count,
            "view_count": self.view_count,
            "bookmark_count": self.bookmark_count,
        }

    def __str__(self) -> str:
        """String representation of the Tweet"""
        return f"Tweet(id={self.tweet_id}, user={self.username}, created_at={self.created_at})"
