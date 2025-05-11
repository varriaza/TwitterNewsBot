from twitter.get_tweets import get_tweets
from db.database import NewsDatabase
import argparse
from twitter.tweet import Tweet
from llm.rank.evaluate_tweets import evaluate_tweet

db_path = "main/db/news_data.db"

def initialize_database():
    # Initialize database and create tables
    db = NewsDatabase(db_path)
    print(f"Database initialized at {db_path}")
    return db

def get_tweets_function() -> list[Tweet]:
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
        # db.save_tweet_object(tweet)
        print(tweet.text)

    return all_tweets

def rank_tweets_function(tweet_list: list[Tweet] | None = None, use_local_llm: bool = True):
    # Initialize the database
    db = initialize_database()
    
    if tweet_list is None:
        # Pull in all tweets from the last 24 hours from the database
        # Exclude retweets as the text is cut off!
        # Run the following sql query:
        sql_query = """
        SELECT * FROM tweets
        WHERE created_at > datetime('now', '-7 days')
        and tweet_type = 'regular';
        """
        
        # Use the execute_query method to get the tweets
        tweet_list = db.execute_query(sql_query, return_type=Tweet)
        
        print(f"Retrieved {len(tweet_list)} tweets from the last 24 hours")
    
    
    if tweet_list:
        # Limit the number of tweets to 1 if we have any tweets
        tweet_list = tweet_list[:3]
        
        for tweet in tweet_list:
            rank = evaluate_tweet(tweet, use_local_llm)
            # Save the rank to the database
            # TODO: Add logic to avoid saving duplicate ranks
            db.save_rank_object(rank)
            if len(tweet.text) > 40:
                print(f"Saved rank for tweet:'{tweet.text[0:40]}...' | Score: {rank.score}")
            else:
                print(f"Saved rank for tweet:'{tweet.text}' | Score: {rank.score}")
    else:
        raise ValueError("No tweets found!")

def write_article_function():
    # Placeholder for writing article
    pass

def create_podcast_function():
    # Placeholder for creating podcast
    pass

def run_everything():
    tweet_list = get_tweets_function()
    rank_tweets_function(tweet_list)
    write_article_function()
    create_podcast_function()

def main():
    parser = argparse.ArgumentParser(description='Twitter News Bot')
    parser.add_argument('-e', '--everything', action='store_true', help='Run everything')
    parser.add_argument('-t', '--tweets', action='store_true', help='Get tweets')
    parser.add_argument('-r', '--rank', action='store_true', help='Rank tweets')
    parser.add_argument('-w', '--write', action='store_true', help='Write article')
    parser.add_argument('-p', '--podcast', action='store_true', help='Create podcast')
    
    args = parser.parse_args()
    
    if args.everything:
        run_everything()
    elif args.tweets:
        get_tweets_function()
    elif args.rank:
        rank_tweets_function()
    elif args.write:
        write_article_function()
    elif args.podcast:
        create_podcast_function()
    else:
        # If no arguments provided, run everything as default
        run_everything()

if __name__ == "__main__":
    main()
