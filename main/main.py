from twitter.get_tweets import get_tweets
from db.database import NewsDatabase
import argparse
from twitter.tweet import Tweet
from llm.rank.evaluate_tweets import rank_tweet
from llm.rank.rank import Rank
from llm.article.create_article import collect_tweets_for_article, create_article, LLMArticle

db_path = "main/db/news_data.db"

def initialize_database():
    # Initialize database and create tables
    db = NewsDatabase(db_path)
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
        db.save_tweet_object(tweet)
        print(tweet.text)

    return all_tweets

def rank_tweets_function(tweet_list: list[Tweet] | None = None, use_local_llm: bool = True):
    rank_list = []
    # Initialize the database
    db = initialize_database()
    
    if tweet_list is None:
        # Pull in all tweets from the last x days from the database
        days_ago = 7

        # Exclude retweets as the text is cut off!
        # Run the following sql query:
        sql_query = f"""
        SELECT * FROM tweets
        WHERE created_at > datetime('now', '-{days_ago} days')
        and tweet_type != 'retweet';
        """
        
        # Use the execute_query method to get the tweets
        tweet_list = db.execute_query(sql_query, return_type=Tweet)
        
        print(f"Retrieved {len(tweet_list)} tweets from the last {days_ago} day(s)")
    
    
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
                print(f"Saved rank for tweet:'{text[0:print_limit]}...' | Score: {rank.score}")
            else:
                print(f"Saved rank for tweet:'{tweet.text}' | Score: {rank.score}")
            # Save the rank to the list
            rank_list.append(rank)
    else:
        raise ValueError("No tweets found!")
    
    return rank_list

def write_article_function(rank_list: list[Rank] | None = None) -> LLMArticle:
    # Collect tweet data from provided ranks or from database
    tweets_df = collect_tweets_for_article(rank_list)
    
    # Generate and get the article
    article = create_article(tweets_df)
    
    # Save article to database
    db = initialize_database()
    db.save_article_object(article)
    print(f"Article saved to database with title: {article.title}")
    
    return article


def create_podcast_function():
    # Placeholder for creating podcast
    pass

def run_everything():
    tweet_list = get_tweets_function()
    rank_list = rank_tweets_function(tweet_list)
    write_article_function(rank_list)
    create_podcast_function()

def main():
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

if __name__ == "__main__":
    main()
