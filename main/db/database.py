import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

class NewsDatabase:
    def __init__(self, db_path: str = "news_data.db"):
        """Initialize the database connection"""
        self.db_path = db_path
        self.connection = None
        self.create_tables()
    
    def connect(self):
        """Create a connection to the SQLite database"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def create_tables(self):
        """Create the necessary tables if they don't exist"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Create tweets table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tweets (
            tweet_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            url TEXT,
            created_at TIMESTAMP NOT NULL,
            text TEXT NOT NULL,
            tweet_type TEXT NOT NULL,
            linked_tweet_id TEXT,
            retweet_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            quote_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            bookmark_count INTEGER DEFAULT 0,
            FOREIGN KEY (linked_tweet_id) REFERENCES tweets (tweet_id)
        )
        ''')
        
        # Create an index on username and created_at for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_username_created 
        ON tweets (username, created_at)
        ''')
        
        conn.commit()
        self.close()
    
    def tweet_exists(self, username: str, created_at: datetime) -> bool:
        """Check if a tweet already exists in the database based on username and creation time"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM tweets WHERE username = ? AND created_at = ?",
            (username, created_at)
        )
        
        exists = cursor.fetchone() is not None
        self.close()
        return exists
    
    def save_tweet(self, 
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
                  bookmark_count: int = 0) -> str:
        """
        Save a tweet to the database
        Returns the tweet_id (UUID) of the saved tweet
        """
        # Check if tweet already exists
        if self.tweet_exists(username, created_at):
            # Find the existing tweet ID
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT tweet_id FROM tweets WHERE username = ? AND created_at = ?",
                (username, created_at)
            )
            result = cursor.fetchone()
            self.close()
            if result:
                return result[0]
            
        # Generate a new UUID for the tweet
        tweet_id = str(uuid.uuid4())
        
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO tweets (
            tweet_id, username, url, created_at, text, tweet_type, 
            linked_tweet_id, retweet_count, reply_count, like_count, 
            quote_count, view_count, bookmark_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tweet_id, username, url, created_at, text, tweet_type,
            linked_tweet_id, retweet_count, reply_count, like_count,
            quote_count, view_count, bookmark_count
        ))
        
        conn.commit()
        self.close()
        return tweet_id
    
    def save_tweet_object(self, tweet):
        """
        Save a Tweet object to the database
        Returns the tweet_id of the saved tweet
        """
        return self.save_tweet(
            username=tweet.username,
            created_at=tweet.created_at,
            text=tweet.text,
            url=tweet.url,
            tweet_type=tweet.tweet_type,
            linked_tweet_id=tweet.linked_tweet_id,
            retweet_count=tweet.retweet_count,
            reply_count=tweet.reply_count,
            like_count=tweet.like_count,
            quote_count=tweet.quote_count,
            view_count=tweet.view_count,
            bookmark_count=tweet.bookmark_count
        )
    
    def get_tweets_by_username(self, username: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tweets by username, ordered by creation date descending"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM tweets WHERE username = ? ORDER BY created_at DESC LIMIT ?",
            (username, limit)
        )
        
        results = [dict(row) for row in cursor.fetchall()]
        self.close()
        return results 