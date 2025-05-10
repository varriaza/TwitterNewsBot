from twitter.get_tweets import get_tweets
from db.database import NewsDatabase
import os

db_path = "main/db/news_data.db"

def initialize_database():
    # Initialize database and create tables
    db = NewsDatabase(db_path)
    print(f"Database initialized at {db_path}")
    return db

def main(): 
    # Make sure database is ready
    db = initialize_database()
    
    user_list = [
        "VitalikButerin",
    ] 
    stop_date = "2025-05-07"

    all_tweets = []
    for user in user_list:
        tweets = get_tweets(user, stop_date)
        all_tweets.extend(tweets)
        print(f"Retrieved {len(tweets)} tweets for {user}")
    
    # Save the tweets to the database
    for tweet in all_tweets:
        db.save_tweet_object(tweet)

if __name__ == "__main__":
    main()
