from .database import NewsDatabase
from datetime import datetime
import os

def main():
    # Create a test database in the current directory
    db_path = os.path.join(os.path.dirname(__file__), "news_data.db")
        
    # Initialize the database
    db = NewsDatabase(db_path)
    print(f"Created database: {db_path}")
    
    # Add some sample tweets
    tweet1_id = db.save_tweet(
        username="example_user_1",
        created_at=datetime.now(),
        text="This is a test tweet!",
        url="https://twitter.com/example_user/status/123456789",
        tweet_type="regular",
        retweet_count=5,
        reply_count=2,
        like_count=10
    )
    print(f"Added tweet with ID: {tweet1_id}")
    
    # Add a retweet that links to the first tweet
    tweet2_id = db.save_tweet(
        username="example_user_2",
        created_at=datetime.now(),
        text="RT @example_user_1: This is a test tweet!",
        url="https://twitter.com/retweeter/status/987654321",
        tweet_type="retweet",
        linked_tweet_id=tweet1_id,
        retweet_count=1
    )
    print(f"Added retweet with ID: {tweet2_id}")
    
    # Test retrieving tweets
    tweets = db.get_tweets_by_username("example_user_1")
    print(f"\nTweets by example_user_1: {len(tweets)}")
    for tweet in tweets:
        print(f"- {tweet['text']} (created at {tweet['created_at']})")
    
    tweets = db.get_tweets_by_username("example_user_2")
    print(f"\nTweets by example_user_2: {len(tweets)}")
    for tweet in tweets:
        print(f"- {tweet['text']} (created at {tweet['created_at']})")
        print(f"  Links to tweet: {tweet['linked_tweet_id']}")

    # Clean up test data
    conn = db.connect()
    cursor = conn.cursor()
    
    # Delete test tweets - delete the retweet first due to foreign key constraints
    cursor.execute("DELETE FROM tweets WHERE tweet_id = ?", (tweet2_id,))
    cursor.execute("DELETE FROM tweets WHERE tweet_id = ?", (tweet1_id,))
    
    conn.commit()
    db.close()
    
    print("\nTest data has been cleaned up from the database")
    
if __name__ == "__main__":
    main() 