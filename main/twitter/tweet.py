from datetime import datetime
from typing import Optional, List, Dict, Any


class Tweet:
    def __init__(
        self,
        tweet_id: str,
        username: str,
        created_at: datetime,
        text: str,
        url: Optional[str] = None,
        tweet_type: str = "regular",
        linked_tweet_id: Optional[str] = None,
        retweet_count: int = 0,
        reply_count: int = 0,
        like_count: int = 0,
        quote_count: int = 0,
        view_count: int = 0,
        bookmark_count: int = 0
    ):
        self.tweet_id = tweet_id
        self.username = username
        self.url = url
        self.created_at = created_at
        self.text = text
        self.tweet_type = tweet_type
        self.linked_tweet_id = linked_tweet_id
        self.retweet_count = retweet_count
        self.reply_count = reply_count
        self.like_count = like_count
        self.quote_count = quote_count
        self.view_count = view_count
        self.bookmark_count = bookmark_count
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Tweet':
        """Create a Tweet object from a database row dictionary"""
        return cls(
            tweet_id=row['tweet_id'],
            username=row['username'],
            url=row['url'],
            created_at=row['created_at'],
            text=row['text'],
            tweet_type=row['tweet_type'],
            linked_tweet_id=row['linked_tweet_id'],
            retweet_count=row['retweet_count'],
            reply_count=row['reply_count'],
            like_count=row['like_count'],
            quote_count=row['quote_count'],
            view_count=row['view_count'],
            bookmark_count=row['bookmark_count']
        )
    
    @classmethod
    def from_data(cls, username: str, created_at: datetime, text: str, **kwargs) -> 'Tweet':
        """Create a Tweet object from individual data fields with sensible defaults for optional fields"""
        import uuid
        
        # Set default tweet_id if not provided
        if 'tweet_id' not in kwargs:
            kwargs['tweet_id'] = str(uuid.uuid4())
            
        return cls(
            username=username,
            created_at=created_at,
            text=text,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the Tweet object to a dictionary"""
        return {
            'tweet_id': self.tweet_id,
            'username': self.username,
            'url': self.url,
            'created_at': self.created_at,
            'text': self.text,
            'tweet_type': self.tweet_type,
            'linked_tweet_id': self.linked_tweet_id,
            'retweet_count': self.retweet_count,
            'reply_count': self.reply_count,
            'like_count': self.like_count,
            'quote_count': self.quote_count,
            'view_count': self.view_count,
            'bookmark_count': self.bookmark_count
        }
    
    def __str__(self) -> str:
        """String representation of the Tweet"""
        return f"Tweet(id={self.tweet_id}, user={self.username}, created_at={self.created_at})" 