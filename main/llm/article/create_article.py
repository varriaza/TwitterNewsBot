from db.database import NewsDatabase
from twitter.tweet import Tweet
from llm.rank.rank import Rank
import pandas as pd
import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import jinja2
import pathlib
from pydantic import BaseModel, Field
from datetime import datetime

# Read the env var OLLAMA_HOST
ollama_host = os.getenv("OLLAMA_HOST")
full_url = f"{ollama_host}/v1"
model_name = "qwen3:14b"

class ArticlePlan(BaseModel):
    main_topic: str = Field(description="The main topic or focus of the article")
    key_points: list[str] = Field(description="List of key points to cover in the article")
    structure: list[str] = Field(description="Outline of the article structure with section headings")

class LLMArticle(BaseModel):
    article_id: str = Field(default="", description="The unique identifier for the article")
    title: str = Field(description="The title of the news article")
    content: str = Field(description="The full content of the news article")
    summary: str = Field(description="A short summary of the article")
    created_at: datetime = Field(default_factory=datetime.now, description="When the article was generated")

def collect_tweets_for_article(rank_list: list[Rank] | None = None) -> pd.DataFrame:
    # Initialize the database
    db = NewsDatabase("main/db/news_data.db")
    
    if rank_list is None or len(rank_list) == 0:
        # Pull in all ranks from the last x days with score >= 7
        days_ago = 2
        
        sql_query = f"""
        SELECT * FROM ranks
        WHERE run_time > datetime('now', '-{days_ago} days')
        AND score >= 7
        ORDER BY score DESC;
        """
        
        rank_list = db.execute_query(sql_query, return_type=Rank)
        print(f"Retrieved {len(rank_list)} high-scoring ranks from the last {days_ago} day(s)")
    
    if not rank_list or len(rank_list) == 0:
        raise ValueError("No high-scoring ranks found for article generation!")
    
    # Get all tweet IDs from the ranks
    tweet_ids = [rank.tweet_id for rank in rank_list]
    
    # Query for the tweets using these IDs
    placeholders = ','.join(['?' for _ in tweet_ids])
    tweet_query = f"""
    SELECT * FROM tweets 
    WHERE tweet_id IN ({placeholders})
    ORDER BY created_at DESC;
    """
    
    tweets = db.execute_query(tweet_query, params=tweet_ids, return_type=Tweet)
    print(f"Retrieved {len(tweets)} tweets referenced by the high-scoring ranks")
    
    # Create dictionaries from tweets and ranks for DataFrame creation
    tweets_dict = {tweet.tweet_id: tweet.__dict__ for tweet in tweets}
    ranks_dict = {rank.tweet_id: {'rank_reason': rank.reason, 'rank_score': rank.score} for rank in rank_list}
    
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
    print(f"Created DataFrame with {len(tweets_df)} rows of combined tweet and rank data")
    
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

def generate_article_plan(tweets_df: pd.DataFrame) -> ArticlePlan:
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
    ollama_model = OpenAIModel(
        model_name=model_name,
        provider=OpenAIProvider(base_url=full_url),
    )
    
    agent = Agent(
        model=ollama_model,
        output_type=ArticlePlan,
        prompt=prompt,
        retries=3
    )
    
    # Run the agent and get the plan
    plan = agent.run_sync(prompt).output
    print(f"Generated article plan with main topic: {plan.main_topic}")
    # print(f"Article plan key points: {plan.key_points}")
    # print(f"Article plan structure: {plan.structure}")
    # print("--------------------------------")
    return plan

def create_article(tweets_df: pd.DataFrame) -> LLMArticle:
    """Create an article using a two-step process: planning and generation."""
    # Step 1: Generate an article plan
    plan = generate_article_plan(tweets_df)
    
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
        main_topic=plan.main_topic,
        key_points=plan.key_points,
        structure=plan.structure
    )
    
    # Make LLM call for article generation
    ollama_model = OpenAIModel(
        model_name=model_name,
        provider=OpenAIProvider(base_url=full_url),
    )
    
    agent = Agent(
        model=ollama_model,
        output_type=LLMArticle,
        prompt=prompt,
        retries=3
    )
    
    # Run the agent and get the result
    article = agent.run_sync(prompt).output
    
    print(f"Generated article with title: {article.title}")
    # print(f"Article content: {article.content}")
    print(f"Article summary: {article.summary}")
    return article