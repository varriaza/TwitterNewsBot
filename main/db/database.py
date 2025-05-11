import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TypeVar, Generic, Type

T = TypeVar('T')

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
        
        # Create ranks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ranks (
            rank_id TEXT PRIMARY KEY,
            tweet_id TEXT NOT NULL,
            run_time TIMESTAMP NOT NULL,
            reason TEXT NOT NULL,
            score INTEGER NOT NULL,
            model TEXT,
            prompt TEXT,
            FOREIGN KEY (tweet_id) REFERENCES tweets (tweet_id)
        )
        ''')
        
        # Create an index on tweet_id for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_ranks_tweet_id
        ON ranks (tweet_id)
        ''')
        
        # Create articles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            article_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
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
    
    def rank_exists(self, rank_id: str) -> bool:
        """Check if a rank already exists in the database based on rank_id"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM ranks WHERE rank_id = ?", (rank_id,))
        
        exists = cursor.fetchone() is not None
        self.close()
        return exists
    
    def save_rank(self, rank_id: str, tweet_id: str, run_time: datetime, 
                  reason: str, score: int, model: Optional[str] = None, 
                  prompt: Optional[str] = None) -> str:
        """
        Save a rank to the database
        Returns the rank_id of the saved rank
        """
        # Check if rank already exists
        if self.rank_exists(rank_id):
            return rank_id
            
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO ranks (
            rank_id, tweet_id, run_time, reason, score, model, prompt
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            rank_id, tweet_id, run_time, reason, score, model, prompt
        ))
        
        conn.commit()
        self.close()
        return rank_id
    
    def save_rank_object(self, rank):
        """
        Save a Rank object to the database
        Returns the rank_id of the saved rank
        """
        return self.save_rank(
            rank_id=rank.rank_id,
            tweet_id=rank.tweet_id,
            run_time=rank.run_time,
            reason=rank.reason,
            score=rank.score,
            model=rank.model,
            prompt=rank.prompt
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
    
    def execute_query(self, query: str, params: tuple = (), return_type: Type[T] = None) -> List[T]:
        """
        Execute a SQL query and map results to objects of the specified type
        
        Args:
            query: SQL query string
            params: Parameters for the query
            return_type: Class type to map results to
            
        Returns:
            List of objects of the specified type
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        if return_type:
            for row in rows:
                # Convert row to dict
                row_dict = dict(row)
                # Create an instance of the return type with the row data
                obj = return_type(**row_dict)
                results.append(obj)
        else:
            # If no return type specified, return dictionaries
            results = [dict(row) for row in rows]
            
        self.close()
        return results 
    
    def article_exists(self, article_id: str) -> bool:
        """Check if an article already exists in the database based on article_id"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM articles WHERE article_id = ?", (article_id,))
        
        exists = cursor.fetchone() is not None
        self.close()
        return exists
    
    def save_article(self, article_id: str, title: str, content: str, 
                    summary: str, created_at: datetime = None) -> str:
        """
        Save an article to the database
        Returns the article_id of the saved article
        """
        # If no creation time provided, use current time
        if created_at is None:
            created_at = datetime.now()
            
        # Check if article already exists
        if self.article_exists(article_id):
            return article_id
            
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO articles (
            article_id, title, content, summary, created_at
        ) VALUES (?, ?, ?, ?, ?)
        ''', (
            article_id, title, content, summary, created_at
        ))
        
        conn.commit()
        self.close()
        return article_id
    
    def save_article_object(self, article):
        """
        Save an Article object to the database
        Returns the article_id of the saved article
        """
        # Generate a new UUID for the article if it doesn't have one
        if not hasattr(article, 'article_id') or not article.article_id:
            article_id = str(uuid.uuid4())
        else:
            article_id = article.article_id
            
        return self.save_article(
            article_id=article_id,
            title=article.title,
            content=article.content,
            summary=article.summary,
            created_at=article.created_at
        ) 