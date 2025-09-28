from twitter.get_tweets import get_tweets
from db.database import NewsDatabase
import argparse
from pydantic_models.tweet_model import Tweet
from llm.rank.evaluate_tweets import rank_tweet
from pydantic_models.rank_model import Rank
from pydantic_models.article_model import Article
from llm.article.create_article import collect_tweets_for_article, create_article
from twitter.get_profiles import get_people_usernames, get_organization_usernames
from datetime import datetime, timedelta
import time
from llm.open_router import ModelType
from typing import Optional
import yaml
import pathlib

db_path = "main/db/news_data.db"

# Set the specific date to run for
RUN_DAY = "2025-09-26"  # Format: YYYY-MM-DD
# Set RUN_DAY to the previous day
# RUN_DAY = (datetime.strptime(RUN_DAY, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

GET_TEST_DATA = True


def load_config() -> dict:
    """Load configuration from keys/key.yaml file."""
    keys_path = pathlib.Path(__file__).parent.parent / "keys" / "key.yaml"
    with open(keys_path, "r") as f:
        return yaml.safe_load(f)


def print_timing(start_time, operation_name):
    end_time = time.time()
    duration = end_time - start_time
    minutes = int(duration // 60)
    seconds = duration % 60
    if minutes > 0:
        print(
            f"\n{operation_name} completed in {minutes} minute(s) and {seconds:.2f} seconds"
        )
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

    # Raise a warning if RUN_DAY is over 7 days ago
    if (datetime.now() - datetime.strptime(RUN_DAY, "%Y-%m-%d")).days > 7:
        input(
            f"Warning: RUN_DAY is over 7 days ago: {RUN_DAY}!!! \nPress Enter to continue..."
        )

    # Make sure database is ready
    db = initialize_database()

    user_list = get_people_usernames(use_test_data=GET_TEST_DATA)
    # user_list.extend(get_organization_usernames())

    # Use the specific run date
    stop_date = datetime.strptime(RUN_DAY, "%Y-%m-%d").strftime("%Y-%m-%d")

    all_tweets = []
    for user in user_list:
        tweets = get_tweets(user, stop_date)
        all_tweets.extend(tweets)
        # print(f"Retrieved {len(tweets)} tweets for {user}")

    # Save the tweets to the database
    for tweet in all_tweets:
        db.save_tweet_object(tweet)
        # print(tweet.text)

    print_timing(start_time, "Tweet collection")
    return all_tweets


def rank_tweets_function(
    tweet_list: list[Tweet] | None = None,
    rank_model_type: Optional[ModelType] = None,
    ollama_host: Optional[str] = None,
):
    start_time = time.time()
    print("\nStarting tweet ranking...")

    rank_list = []
    # Initialize the database
    db = initialize_database()

    if tweet_list is None:
        # Pull in all tweets from the specific run date from the database
        # Exclude retweets as the text is cut off!
        # Run the following sql query:
        sql_query = f"""
        SELECT * FROM tweet
        WHERE date(created_at) = '{RUN_DAY}'
        and tweet_type != 'retweet';
        """

        # Use the execute_query method to get the tweets
        tweet_list = db.execute_query(sql_query, return_type=Tweet)

        print(
            f"Retrieved {len(tweet_list)} tweets from the specific run date: {RUN_DAY}"
        )

    if tweet_list:
        # Limit the number of tweets for testing
        # tweet_list = tweet_list[:3]

        for tweet in tweet_list:
            rank = rank_tweet(tweet, rank_model_type, ollama_host)
            # Save the rank to the database
            # NOTE: this can save duplicate ranks
            db.save_rank_object(rank)

            # Limit the length of the tweet text for printing
            print_limit = 60
            if len(tweet.text) > print_limit:
                # Remove new lines for printing
                text = tweet.text.replace("\n", " ")
                print(
                    f"Saved rank for {tweet.username} | '{text[0:print_limit]}...' | Score: {rank.score}"
                )
            else:
                print(
                    f"Saved rank for {tweet.username} | '{tweet.text}' | Score: {rank.score}"
                )
            # Save the rank to the list
            rank_list.append(rank)
    else:
        raise ValueError("No tweets found!")

    print_timing(start_time, "Tweet ranking")
    return rank_list


def write_article_function(
    rank_list: list[Rank] | None = None,
    article_model_type: Optional[ModelType] = None,
    ollama_host: Optional[str] = None,
) -> Article:
    start_time = time.time()
    print("\nStarting article generation...")

    # Collect tweet data from provided ranks or from database
    tweets_df = collect_tweets_for_article(rank_list, RUN_DAY)

    # Generate and get the article
    article = create_article(tweets_df, article_model_type, ollama_host)

    # Save article to database
    db = initialize_database()
    db.save_article_object(article)
    print(f"Article saved to database with title: {article.title}")

    print_timing(start_time, "Article generation")
    return article


def create_podcast_function():
    start_time = time.time()
    print("\nStarting podcast creation...")
    raise NotImplementedError()

    # Placeholder for creating podcast
    pass

    print_timing(start_time, "Podcast creation")


def run_everything(rank_model_type: Optional[ModelType] = None, article_model_type: Optional[ModelType] = None, ollama_host: Optional[str] = None):
    total_start_time = time.time()
    print("\nStarting full pipeline execution...")

    tweet_list = get_tweets_function()
    rank_list = rank_tweets_function(
        tweet_list, rank_model_type=rank_model_type, ollama_host=ollama_host
    )
    write_article_function(rank_list, article_model_type=article_model_type, ollama_host=ollama_host)
    # create_podcast_function()

    print_timing(total_start_time, "Full pipeline")


def main():
    total_start_time = time.time()

    parser = argparse.ArgumentParser(description="Twitter News Bot")
    parser.add_argument(
        "-e", "--everything", action="store_true", help="Run everything"
    )
    parser.add_argument("-t", "--tweets", action="store_true", help="Get tweets")
    parser.add_argument("-r", "--rank", action="store_true", help="Rank tweets")
    parser.add_argument("-a", "--article", action="store_true", help="Write article")
    parser.add_argument("-p", "--podcast", action="store_true", help="Create podcast")
    parser.add_argument(
        "-fr", "--free", action="store_true", help="Use free models for both ranking and article generation"
    )
    parser.add_argument(
        "-pa", "--paid", action="store_true", help="Use paid models (fast for ranking, smart for article generation)"
    )
    parser.add_argument("-lo", "--local", action="store_true", help="Use local LLM")

    args = parser.parse_args()

    # Load configuration
    config = load_config()
    ollama_host = config.get("ollama_host")

    # Model type configuration
    rank_model_type = None
    article_model_type = None
    
    # If we are running a step that requires an LLM, set the arguments
    if args.rank or args.article or args.podcast or args.everything:
        # Determine which model type to use
        if args.free:
            rank_model_type = "free"
            article_model_type = "free"
            print("Using OpenRouter free models for both ranking and article generation")
        elif args.paid:
            rank_model_type = "fast"
            article_model_type = "smart"
            print("Using OpenRouter paid models (fast for ranking, smart for article generation)")
        elif args.local:
            rank_model_type = None
            article_model_type = None
            print("Using local LLM")
        else:
            raise ValueError("No model type provided (use --free, --paid, or --local)")

    if args.everything:
        run_everything(rank_model_type=rank_model_type, article_model_type=article_model_type, ollama_host=ollama_host)
    elif args.tweets:
        get_tweets_function()
    elif args.rank:
        rank_tweets_function(rank_model_type=rank_model_type, ollama_host=ollama_host)
    elif args.article:
        write_article_function(article_model_type=article_model_type, ollama_host=ollama_host)
    elif args.podcast:
        create_podcast_function()
    else:
        # If no arguments provided, run everything as default
        run_everything(rank_model_type=rank_model_type, article_model_type=article_model_type, ollama_host=ollama_host)

    print_timing(total_start_time, "Total execution")


if __name__ == "__main__":
    main()
