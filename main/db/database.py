import sqlite3
from datetime import datetime
from typing import List, TypeVar, Type
from sqlmodel import SQLModel, create_engine, Session, select

# Import the SQLModel classes
from pydantic_models.tweet_model import Tweet
from pydantic_models.rank_model import Rank
from pydantic_models.article_model import Article

# Used for the execute_query method
T = TypeVar("T")


class NewsDatabase:
    def __init__(self, db_path: str = "news_data.db"):
        """Initialize the database connection"""
        self.db_path = db_path
        self.connection = None
        # Create SQLModel engine
        self.engine = create_engine(f"sqlite:///{db_path}")
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
        """Create the necessary tables using SQLModel"""
        SQLModel.metadata.create_all(self.engine)

    def tweet_exists(self, username: str, created_at: datetime) -> bool:
        """Check if a tweet already exists in the database based on username and creation time"""
        with Session(self.engine) as session:
            statement = select(Tweet).where(
                Tweet.username == username, Tweet.created_at == created_at
            )
            result = session.exec(statement).first()
            return result is not None

    def save_tweet_object(self, tweet: Tweet) -> str:
        """
        Save a Tweet object to the database
        Returns the tweet_id of the saved tweet
        """
        # Check if tweet already exists
        if self.tweet_exists(tweet.username, tweet.created_at):
            with Session(self.engine) as session:
                statement = select(Tweet).where(
                    Tweet.username == tweet.username,
                    Tweet.created_at == tweet.created_at,
                )
                existing_tweet = session.exec(statement).first()
                if existing_tweet:
                    return existing_tweet.tweet_id

        with Session(self.engine) as session:
            session.add(tweet)
            session.commit()
            # Get the tweet_id while the session is still active
            tweet_id = tweet.tweet_id

        return tweet_id

    def rank_exists(self, rank_id: str) -> bool:
        """Check if a rank already exists in the database based on rank_id"""
        with Session(self.engine) as session:
            statement = select(Rank).where(Rank.rank_id == rank_id)
            result = session.exec(statement).first()
            return result is not None

    def save_rank_object(self, rank: Rank) -> str:
        """
        Save a Rank object to the database
        Returns the rank_id of the saved rank
        """
        # Check if rank already exists
        if self.rank_exists(rank.rank_id):
            return rank.rank_id

        with Session(self.engine) as session:
            session.add(rank)
            session.commit()
            # Get the rank_id while the session is still active
            rank_id = rank.rank_id

        return rank_id

    def get_tweets_by_username(self, username: str, limit: int = 100) -> List[Tweet]:
        """Get tweets by username, ordered by creation date descending"""
        with Session(self.engine) as session:
            statement = (
                select(Tweet)
                .where(Tweet.username == username)
                .order_by(Tweet.created_at.desc())
                .limit(limit)
            )
            tweets = session.exec(statement).all()
            return list(tweets)

    def _format_sql_with_params(self, query: str, params: tuple) -> str:
        """Helper method to format SQL query with parameters for debugging"""
        if not params:
            return query

        # Replace ? with the actual parameter values
        formatted_query = query
        for param in params:
            # Handle different parameter types
            if isinstance(param, str):
                param = f"'{param}'"
            elif param is None:
                param = "NULL"
            formatted_query = formatted_query.replace("?", str(param), 1)
        return formatted_query

    def get_session(self) -> Session:
        """Get a new SQLModel session"""
        return Session(self.engine)

    def execute_query(
        self, query: str, params: tuple = (), return_type: Type[T] = None
    ) -> List[T]:
        """
        Execute a SQL query and map results to objects of the specified type

        Args:
            query: SQL query string
            params: Parameters for the query
            return_type: Class type to map results to

        Returns:
            List of objects of the specified type
        """
        # For backward compatibility, fall back to raw SQLite for complex queries
        conn = self.connect()
        cursor = conn.cursor()

        # Print the formatted SQL query with parameters
        # print(f"Executing SQL:\n{self._format_sql_with_params(query, params)}")

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
        with Session(self.engine) as session:
            statement = select(Article).where(Article.article_id == article_id)
            result = session.exec(statement).first()
            return result is not None

    def save_article_object(self, article: Article) -> str:
        """
        Save an Article object to the database
        Returns the article_id of the saved article
        """
        # Check if article already exists
        if self.article_exists(article.article_id):
            return article.article_id

        with Session(self.engine) as session:
            session.add(article)
            session.commit()
            # Get the article_id while the session is still active
            article_id = article.article_id

        return article_id
