import requests
import yaml
import datetime
import uuid
from typing import List
from .tweet import Tweet


def parse_tweet_date(tweet_date: str) -> datetime.datetime:
    """
    Parses a tweet date string and returns a datetime.datetime object.
    Handles both ISO and Twitter date formats.
    
    Args:
        tweet_date: Date string from tweet data
    
    Returns:
        A datetime.datetime object
    """
    try:
        # Twitter format: "Fri May 09 09:55:55 +0000 2025"
        return datetime.datetime.strptime(tweet_date, "%a %b %d %H:%M:%S %z %Y")
    except ValueError as e:
        print(f"Warning: Could not parse date: {tweet_date}")
        print(f"Error found: {e}")
        return None


def get_tweets(username: str, stop_date: str) -> List[Tweet]:
    """
    Fetches tweets for a given username until reaching the stop date.
    Returns a list of Tweet objects.
    
    Args:
        username: Twitter username without the @ symbol
        stop_date: Date string in format "YYYY-MM-DD"
    
    Returns:
        List of Tweet objects
    """
    # Load API keys
    with open("keys/key.yaml", "r") as f:
        keys = yaml.safe_load(f)
    
    stop_date_obj = datetime.datetime.strptime(stop_date, "%Y-%m-%d").date()
    
    url = "https://api.twitterapi.io/twitter/user/last_tweets"
    headers = {"X-API-Key": keys["twitter_api_io_key"]}
    
    all_tweets = []
    cursor = ""
    reached_date_limit = False
    
    while not reached_date_limit:
        querystring = {
            "userName": username,
            "cursor": cursor,
        }
    
        response = requests.request("GET", url, headers=headers, params=querystring)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            break
            
        full_data = response.json()
        
        # The API response has tweets in data.tweets, not directly in data
        if "data" in full_data and "tweets" in full_data["data"]:
            tweets = full_data["data"]["tweets"]
            
            for tweet_data in tweets:
                if "createdAt" in tweet_data:
                    # Parse the tweet date
                    created_at_str = tweet_data["createdAt"]
                    try:
                        # Use the new parse_tweet_date function
                        tweet_date = parse_tweet_date(created_at_str)
                        if tweet_date is None:
                            print(f"Warning: Could not parse date: {created_at_str}")
                            continue
                    except ValueError:
                        print(f"Warning: Could not parse date: {created_at_str}")
                        continue
                    
                    # If tweet is before stop_date, stop collecting
                    if tweet_date.date() < stop_date_obj:
                        print(f"Reached tweet from {tweet_date} which is before stop date {stop_date}")
                        reached_date_limit = True
                        break
                    
                    # Convert the API tweet to our Tweet object
                    tweet_objs = _convert_api_tweet_to_tweet_object(tweet_data)
                    if tweet_objs:
                        all_tweets.extend(tweet_objs)
                
            if reached_date_limit:
                break
    
            # Check if there are more pages
            if len(tweets) == 20 and full_data["data"].get("has_next_page") and not reached_date_limit:
                cursor = full_data["data"].get("next_cursor", "")
                print(f"Fetching more tweets with cursor: {cursor}")
            else:
                print("Found all tweets")
                break
        else:
            print("No tweets found in response")
            break
    
    print(f"Total tweets collected: {len(all_tweets)}")
    return all_tweets


def _convert_api_tweet_to_tweet_object(tweet_data: dict) -> List[Tweet]:
    """
    Converts a tweet from the Twitter API format to our Tweet object(s).
    
    Args:
        tweet_data: Dictionary containing tweet data from the API
        
    Returns:
        List of Tweet objects:
        - For regular tweets: returns a list with a single Tweet object
        - For retweets: returns a list with the original tweet and the retweet
        - For replies: returns a list with the original tweet and the reply
    """
    result_tweets = []
    
    # Get the current tweet's username
    username = tweet_data["author"].get("userName", "")
    if not username:
        raise ValueError(f"Username not found! tweet_data:\n{tweet_data}")
    
    # Parse created_at for the current tweet
    created_at_str = tweet_data.get("createdAt", "")
    created_at = parse_tweet_date(created_at_str)
    if created_at is None:
        raise ValueError(f"Can't parse date! \ndate: {created_at_str}\n tweet_data:\n{tweet_data}")
    
    # Get text content, URL, and metrics for the current tweet
    text = tweet_data.get("text", "")
    url = tweet_data.get("url", "")
    metrics = tweet_data.get("public_metrics", {})
    retweet_count = metrics.get("retweet_count", 0) or tweet_data.get("retweetCount", 0)
    reply_count = metrics.get("reply_count", 0) or tweet_data.get("replyCount", 0)
    like_count = metrics.get("like_count", 0) or tweet_data.get("likeCount", 0)
    quote_count = metrics.get("quote_count", 0) or tweet_data.get("quoteCount", 0)
    view_count = metrics.get("impression_count", 0) or tweet_data.get("viewCount", 0)
    bookmark_count = tweet_data.get("bookmarkCount", 0)
    
    # Check tweet type
    if tweet_data.get("retweeted_tweet"):
        # CASE 1: This is a retweet
        # First, create the original tweet
        original_tweet_data = tweet_data["retweeted_tweet"]
        original_tweet_id = str(uuid.uuid4())
        
        original_username = original_tweet_data["author"].get("userName", "")
        
        # Parse the date of the original tweet
        original_created_at_str = original_tweet_data.get("createdAt", "")
        original_created_at = parse_tweet_date(original_created_at_str)
        if original_created_at is None:
            # If we can't parse the date of the original tweet, use the retweet date
            original_created_at = created_at
        
        # Get original tweet metrics
        original_metrics = original_tweet_data.get("public_metrics", {})
        original_retweet_count = original_metrics.get("retweet_count", 0) or original_tweet_data.get("retweetCount", 0)
        original_reply_count = original_metrics.get("reply_count", 0) or original_tweet_data.get("replyCount", 0)
        original_like_count = original_metrics.get("like_count", 0) or original_tweet_data.get("likeCount", 0)
        original_quote_count = original_metrics.get("quote_count", 0) or original_tweet_data.get("quoteCount", 0)
        original_view_count = original_metrics.get("impression_count", 0) or original_tweet_data.get("viewCount", 0)
        original_bookmark_count = original_tweet_data.get("bookmarkCount", 0)
        
        # Create and add the original tweet as a regular tweet
        original_tweet = Tweet(
            tweet_id=original_tweet_id,
            username=original_username,
            created_at=original_created_at,
            text=original_tweet_data.get("text", ""),
            url=original_tweet_data.get("url", ""),
            tweet_type="regular",
            linked_tweet_id=None,
            retweet_count=original_retweet_count,
            reply_count=original_reply_count,
            like_count=original_like_count,
            quote_count=original_quote_count,
            view_count=original_view_count,
            bookmark_count=original_bookmark_count
        )
        result_tweets.append(original_tweet)
        
        # NOTE: The text of the retweet gets cut off!!!
        # Now create the retweet itself
        retweet_id = str(uuid.uuid4())
        retweet = Tweet(
            tweet_id=retweet_id,
            username=username,
            created_at=created_at,
            text=text,
            url=url,
            tweet_type="retweet",
            linked_tweet_id=original_tweet_id,
            retweet_count=retweet_count,
            reply_count=reply_count,
            like_count=like_count,
            quote_count=quote_count,
            view_count=view_count,
            bookmark_count=bookmark_count
        )
        result_tweets.append(retweet)
        
    elif tweet_data.get("inReplyToId") and tweet_data.get("isReply"):
        # CASE 2: This is a reply
        # For replies, we create a placeholder for the original tweet
        # Note: The API doesn't provide the full original tweet data in the reply context
        
        # original_tweet_id = str(uuid.uuid4())
        original_tweet_id = None
        in_reply_to_username = tweet_data.get("inReplyToUsername", "")
        
        # Create a placeholder for the original tweet with minimal data
        # Commenting out the original tweet creation since we don't have the text
        # ----------------------------------------------------------------------
        # original_tweet = Tweet(
        #     tweet_id=original_tweet_id,
        #     username=in_reply_to_username,
        #     created_at=created_at - datetime.timedelta(minutes=5),  # Approximate time (earlier)
        #     text="",  # We don't have the original text
        #     url="",
        #     tweet_type="regular",
        #     linked_tweet_id=None,
        #     retweet_count=0,
        #     reply_count=0,
        #     like_count=0,
        #     quote_count=0,
        #     view_count=0,
        #     bookmark_count=0
        # )
        # result_tweets.append(original_tweet)
        
        # Create the reply tweet
        reply_id = str(uuid.uuid4())
        reply = Tweet(
            tweet_id=reply_id,
            username=username,
            created_at=created_at,
            text=text,
            url=url,
            tweet_type="reply",
            linked_tweet_id=original_tweet_id,
            retweet_count=retweet_count,
            reply_count=reply_count,
            like_count=like_count,
            quote_count=quote_count,
            view_count=view_count,
            bookmark_count=bookmark_count
        )
        result_tweets.append(reply)
        
    else:
        # CASE 3: Regular tweet, quoted tweet, or other type
        tweet_type = "regular"
        linked_tweet_id = None
        
        # Check for quoted tweets
        if tweet_data.get("quoted_tweet"):
            tweet_type = "quote"
            # Use a new UUID for the quoted tweet reference
            linked_tweet_id = str(uuid.uuid4())
            
        # Create a single regular tweet
        tweet_id = str(uuid.uuid4())
        tweet = Tweet(
            tweet_id=tweet_id,
            username=username,
            created_at=created_at,
            text=text,
            url=url,
            tweet_type=tweet_type,
            linked_tweet_id=linked_tweet_id,
            retweet_count=retweet_count,
            reply_count=reply_count,
            like_count=like_count,
            quote_count=quote_count,
            view_count=view_count,
            bookmark_count=bookmark_count
        )
        result_tweets.append(tweet)
    
    return result_tweets


