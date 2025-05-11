import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import logfire
from twitter.tweet import Tweet
from llm.rank.rank import Rank, LLMRank
import jinja2
import pathlib
from datetime import datetime, timedelta

# # Send LLM logs to Logfire
# logfire.configure()
# logfire.instrument_pydantic()

# Agent.instrument_all()

# Read the env var OLLAMA_HOST
ollama_host = os.getenv("OLLAMA_HOST")
full_url = f"{ollama_host}/v1"
model_name = "qwen3:14b"


def get_date_info() -> dict[str, str]:
    """
    Generate formatted date information for the template.
    Returns a dictionary with today, tomorrow, next week, next month, and next year dates.
    """
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(weeks=1)
    next_month = today + timedelta(days=30)  # Approximate
    next_year = today + timedelta(days=365)  # Approximate
    
    # Format dates
    date_format = "%B %d, %Y"  # Example: January 01, 2023
    return {
        "today": today.strftime(date_format),
        "tomorrow": tomorrow.strftime(date_format),
        "next_week": next_week.strftime(date_format),
        "next_month": next_month.strftime(date_format),
        "next_year": next_year.strftime(date_format)
    }


def format_tweet_info(tweet: Tweet) -> str:
    """
    Format important information from a tweet into a readable string.
    """
    tweet_info = f"Tweet text: {tweet.text}\n"
    tweet_info += f"Username: {tweet.username}\n"
    tweet_info += f"Created at: {tweet.created_at}\n"
    # tweet_info += f"Retweet count: {tweet.retweet_count}\n"
    # tweet_info += f"Reply count: {tweet.reply_count}\n"
    # tweet_info += f"Like count: {tweet.like_count}\n"
    return tweet_info


def rank_tweet(tweet: Tweet, use_local_llm: bool = True) -> Rank:
    # Get formatted tweet information
    tweet_info = format_tweet_info(tweet)

    # Get date information for the template
    date_info = get_date_info()

    # Pull in the jinja prompt
    template_path = pathlib.Path(__file__).parent / "rank_prompt_v3.jinja"
    with open(template_path, "r") as f:
        template_content = f.read()
    
    # Render the template with the tweet text and date information
    jinja_env = jinja2.Environment()
    template = jinja_env.from_string(template_content)
    prompt = template.render(tweet=tweet_info, **date_info)

    if use_local_llm:
        # Initialize the model
        ollama_model = OpenAIModel(
            model_name=model_name,
            provider=OpenAIProvider(base_url=full_url),
        )
        agent = Agent(
            model=ollama_model,
            output_type=LLMRank,
            prompt=prompt,
            retries=3
        )
    else:
        # TODO: Implement remote LLM
        # Use the OpenAI API
        raise NotImplementedError("Remote LLM not implemented yet")
    
    # Get the LLM output as LLMRank
    llm_rank = agent.run_sync(prompt).output
    
    # Convert LLMRank to a full Rank with additional metadata
    rank = Rank.from_llm_rank(
        llm_rank=llm_rank,
        tweet_id=tweet.tweet_id,
        model=model_name,
        prompt=prompt
    )
    
    return rank

