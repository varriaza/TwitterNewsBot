from twitter.get_tweets import get_tweets
from db.database import NewsDatabase
import argparse
from twitter.tweet import Tweet
from llm.rank.evaluate_tweets import rank_tweet
from llm.rank.rank import Rank
from llm.article.create_article import collect_tweets_for_article, create_article, LLMArticle
from twitter.get_profiles import get_people_usernames, get_organization_usernames
from datetime import datetime, timedelta
import time

db_path = "main/db/news_data.db"

# Set the number of days to go back
DAYS_AGO = 1

def print_timing(start_time, operation_name):
    end_time = time.time()
    duration = end_time - start_time
    minutes = int(duration // 60)
    seconds = duration % 60
    if minutes > 0:
        print(f"\n{operation_name} completed in {minutes} minute(s) and {seconds:.2f} seconds")
    else:
        print(f"\n{operation_name} completed in {seconds:.2f} seconds")
    return end_time

def initialize_database():
    # Initialize database and create tables
    db = NewsDatabase(db_path)
    return db

def get_tweets_function() -> list[Tweet]:
    start_time = time.time()
    print("\nStarting tweet collection...")
    
    # Make sure database is ready
    db = initialize_database()
    
    user_list = get_people_usernames() 
    user_list.extend(get_organization_usernames())

    # stop_date = "2025-05-07"
    # Have the stop date be today's date
    stop_date = (datetime.now() - timedelta(days=DAYS_AGO)).strftime("%Y-%m-%d")

    all_tweets = []
    for user in user_list:
        tweets = get_tweets(user, stop_date)
        all_tweets.extend(tweets)
        print(f"Retrieved {len(tweets)} tweets for {user}")
    
    # Save the tweets to the database
    for tweet in all_tweets:
        db.save_tweet_object(tweet)
        # print(tweet.text)

    print_timing(start_time, "Tweet collection")
    return all_tweets

def rank_tweets_function(tweet_list: list[Tweet] | None = None, use_local_llm: bool = True):
    start_time = time.time()
    print("\nStarting tweet ranking...")
    
    rank_list = []
    # Initialize the database
    db = initialize_database()
    
    if tweet_list is None:
        # Pull in all tweets from the last x days from the database
        # Exclude retweets as the text is cut off!
        # Run the following sql query:
        sql_query = f"""
        SELECT * FROM tweets
        WHERE created_at > datetime('now', '-{DAYS_AGO} days')
        and tweet_type != 'retweet';
        """
        
        # Use the execute_query method to get the tweets
        tweet_list = db.execute_query(sql_query, return_type=Tweet)
        
        print(f"Retrieved {len(tweet_list)} tweets from the last {DAYS_AGO} day(s)")
    
    
    if tweet_list:
        # Limit the number of tweets for testing
        # tweet_list = tweet_list[:3]
        
        for tweet in tweet_list:
            rank = rank_tweet(tweet, use_local_llm)
            # Save the rank to the database
            # NOTE: this can save duplicate ranks
            db.save_rank_object(rank)

            # Limit the length of the tweet text for printing
            print_limit = 60
            if len(tweet.text) > print_limit:
                # Remove new lines for printing
                text = tweet.text.replace("\n", " ")
                print(f"Saved rank for {tweet.username} | '{text[0:print_limit]}...' | Score: {rank.score}")
            else:
                print(f"Saved rank for {tweet.username} | '{tweet.text}' | Score: {rank.score}")
            # Save the rank to the list
            rank_list.append(rank)
    else:
        raise ValueError("No tweets found!")
    
    print_timing(start_time, "Tweet ranking")
    return rank_list

def write_article_function(rank_list: list[Rank] | None = None) -> LLMArticle:
    start_time = time.time()
    print("\nStarting article generation...")
    
    # Collect tweet data from provided ranks or from database
    tweets_df = collect_tweets_for_article(rank_list, DAYS_AGO)
    
    # Generate and get the article
    article = create_article(tweets_df)
    
    # Save article to database
    db = initialize_database()
    db.save_article_object(article)
    print(f"Article saved to database with title: {article.title}")
    
    print_timing(start_time, "Article generation")
    return article


def create_podcast_function():
    start_time = time.time()
    print("\nStarting podcast creation...")
    
    # Placeholder for creating podcast
    pass
    
    print_timing(start_time, "Podcast creation")

def run_everything():
    total_start_time = time.time()
    print("\nStarting full pipeline execution...")
    
    tweet_list = get_tweets_function()
    rank_list = rank_tweets_function(tweet_list)
    write_article_function(rank_list)
    create_podcast_function()
    
    print_timing(total_start_time, "Full pipeline")

def main():
    total_start_time = time.time()
    
    parser = argparse.ArgumentParser(description='Twitter News Bot')
    parser.add_argument('-e', '--everything', action='store_true', help='Run everything')
    parser.add_argument('-t', '--tweets', action='store_true', help='Get tweets')
    parser.add_argument('-r', '--rank', action='store_true', help='Rank tweets')
    parser.add_argument('-a', '--article', action='store_true', help='Write article')
    parser.add_argument('-p', '--podcast', action='store_true', help='Create podcast')
    
    args = parser.parse_args()
    
    if args.everything:
        run_everything()
    elif args.tweets:
        get_tweets_function()
    elif args.rank:
        rank_tweets_function()
    elif args.article:
        write_article_function()
    elif args.podcast:
        create_podcast_function()
    else:
        # If no arguments provided, run everything as default
        run_everything()
    
    print_timing(total_start_time, "Total execution")

if __name__ == "__main__":
    main()
