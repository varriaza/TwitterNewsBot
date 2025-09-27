from db.database import NewsDatabase
from pydantic_models.tweet_model import Tweet
from pydantic_models.rank_model import Rank
from pydantic_models.article_model import Article
from pydantic_models.article_plan_model import ArticlePlan
from pydantic_models.llm_article_model import LLMArticle
import pandas as pd
import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import jinja2
import pathlib
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import Optional, Dict, Any
import yaml
from llm.open_router import create_openrouter_model, get_model_display_name, ModelType

# Read the env var OLLAMA_HOST
ollama_host = os.getenv("OLLAMA_HOST")
full_url = f"{ollama_host}/v1"
model_name = "qwen3:14b_t0"


def collect_tweets_for_article(
    rank_list: list[Rank] | None = None, run_date: str = None
) -> pd.DataFrame:
    # Initialize the database
    db = NewsDatabase("main/db/news_data.db")

    print(f"Collecting tweets for article from date: {run_date}")

    if rank_list is None or len(rank_list) == 0:
        # Pull in all ranks from the specific date with score >= 7
        # Join on the tweets table to pull based on when the tweets were created 
        # (and not when the rank was run)
        sql_query = f"""
        SELECT * FROM rank
        join tweet on rank.tweet_id = tweet.tweet_id
        WHERE date(tweet.created_at) = '{run_date}'
        AND rank.score >= 7
        ORDER BY rank.score DESC
        LIMIT 10;
        """

        rank_list = db.execute_query(sql_query, return_type=Rank)
        print(f"Retrieved {len(rank_list)} high-scoring ranks from date: {run_date}")

    if not rank_list or len(rank_list) == 0:
        raise ValueError("No high-scoring ranks found for article generation!")

    # Get all tweet IDs from the ranks
    tweet_ids = [rank.tweet_id for rank in rank_list]

    # Query for the tweets using these IDs
    placeholders = ",".join(["?" for _ in tweet_ids])
    tweet_query = f"""
    SELECT * FROM tweet 
    WHERE tweet_id IN ({placeholders})
    ORDER BY created_at DESC;
    """

    tweets = db.execute_query(tweet_query, params=tweet_ids, return_type=Tweet)
    print(f"Retrieved {len(tweets)} tweets referenced by the high-scoring ranks")

    # Create dictionaries from tweets and ranks for DataFrame creation
    tweets_dict = {tweet.tweet_id: tweet.__dict__ for tweet in tweets}
    ranks_dict = {
        rank.tweet_id: {"rank_reason": rank.reason, "rank_score": rank.score}
        for rank in rank_list
    }

    # Create combined data for DataFrame
    combined_data = []
    for tweet_id, tweet_data in tweets_dict.items():
        if tweet_id in ranks_dict:
            # Combine tweet data with rank data
            combined_row = tweet_data.copy()
            combined_row.update(ranks_dict[tweet_id])
            combined_data.append(combined_row)

    # Create DataFrame with combined data
    tweets_df = pd.DataFrame(combined_data)
    print(
        f"Created DataFrame with {len(tweets_df)} rows of combined tweet and rank data"
    )

    return tweets_df


def format_tweet_sources(tweets_df: pd.DataFrame) -> str:
    """Format tweet information into a single string."""
    tweet_sources = []
    for _, row in tweets_df.iterrows():
        # Create a formatted string for each tweet with text, link, score and reason
        tweet_url = f"https://twitter.com/{row.get('username', 'user')}/status/{row.get('tweet_id', '')}"
        tweet_info = (
            f"Tweet: {row.get('text', '')}\n"
            f"Link: {tweet_url}\n"
            f"Score: {row.get('rank_score', 0)}\n"
            f"Reason: {row.get('rank_reason', '')}\n"
        )
        tweet_sources.append(tweet_info)

    # Join all tweet sources into a single string
    return "\n\n".join(tweet_sources)


def generate_article_plan(tweets_df: pd.DataFrame, openrouter_model_type: Optional[ModelType] = None) -> ArticlePlan:
    """Generate a structured plan for the article using the tweet data."""
    # Format tweet information
    sources = format_tweet_sources(tweets_df)

    # Load the planning Jinja template
    template_path = pathlib.Path(__file__).parent / "article_plan_prompt.jinja"
    with open(template_path, "r") as f:
        template_content = f.read()

    # Render the template
    jinja_env = jinja2.Environment()
    template = jinja_env.from_string(template_content)
    prompt = template.render(sources=sources)

    # Make LLM call for planning
    if openrouter_model_type:
        # Use OpenRouter with specified model type
        openrouter_model = create_openrouter_model(openrouter_model_type)
        agent = Agent(model=openrouter_model, output_type=ArticlePlan, system_prompt=prompt, retries=3)
    else:
        # Initialize the local Ollama model
        ollama_model = OpenAIChatModel(
            model_name=model_name,
            provider=OpenAIProvider(base_url=full_url),
        )
        agent = Agent(model=ollama_model, output_type=ArticlePlan, system_prompt=prompt, retries=3)

    # Run the agent and get the plan
    plan = agent.run_sync(prompt).output
    print(f"Generated article plan with daily summary: {plan.daily_summary}")
    # print(f"Article plan top stories: {plan.top_stories}")
    # print(f"Article plan structure: {plan.structure}")
    # print("--------------------------------")
    return plan


def save_article_to_markdown(article: Article) -> str:
    """Save the article to a markdown file and return the file path."""
    # Create the directory if it doesn't exist
    output_dir = pathlib.Path(__file__).parent / "generated_articles"
    output_dir.mkdir(exist_ok=True)

    # Generate a unique filename using timestamp and UUID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"article_{timestamp}.md"
    filepath = output_dir / filename

    # Create the markdown content
    markdown_content = f"""# {article.title}

*Generated on: {article.created_at.strftime('%Y-%m-%d %H:%M:%S')}*

## Daily Summary
{article.daily_summary}

## Top Stories
{chr(10).join(f"- {story}" for story in article.top_stories)}

## Article Summary
{article.summary}

## Full Article
{article.content}
"""

    # Write the content to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Article saved to: {filepath}")
    return str(filepath)


def create_article(tweets_df: pd.DataFrame, openrouter_model_type: Optional[ModelType] = None) -> Article:
    """Create an article using a two-step process: planning and generation."""
    # Step 1: Generate an article plan
    plan = generate_article_plan(tweets_df, openrouter_model_type)

    # Step 2: Generate the full article using the plan
    sources = format_tweet_sources(tweets_df)

    # Load the article generation Jinja template
    template_path = pathlib.Path(__file__).parent / "article_prompt_v1.jinja"
    with open(template_path, "r") as f:
        template_content = f.read()

    # Render the template with both sources and plan
    jinja_env = jinja2.Environment()
    template = jinja_env.from_string(template_content)
    prompt = template.render(
        sources=sources,
        daily_summary=plan.daily_summary,
        top_stories=plan.top_stories,
        structure=plan.structure,
    )

    # Make LLM call for article generation
    if openrouter_model_type:
        # Use OpenRouter with specified model type
        openrouter_model = create_openrouter_model(openrouter_model_type)
        agent = Agent(model=openrouter_model, output_type=LLMArticle, system_prompt=prompt, retries=3)
        current_model = get_model_display_name(openrouter_model_type)
    # Use the local Ollama model if no model type is provided
    else:
        # Initialize the local Ollama model
        ollama_model = OpenAIChatModel(
            model_name=model_name,
            provider=OpenAIProvider(base_url=full_url),
        )
        agent = Agent(model=ollama_model, output_type=LLMArticle, system_prompt=prompt, retries=3)
        current_model = model_name

    # Run the agent and get the result
    llm_article = agent.run_sync(prompt).output

    print(f"Generated article with title: {llm_article.title}")
    print(f"Article summary: {llm_article.summary}")

    # Create a full Article object from the LLMArticle and additional metadata
    article = Article.from_llm_article(llm_article, model=current_model, prompt=prompt)

    # Save the article to a markdown file
    save_article_to_markdown(article)

    return article
